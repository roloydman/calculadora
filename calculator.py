"""Pure calculation backend (no Streamlit dependency, unit-testable)."""
import ast
import math
import operator


# Safe evaluation backend
BIN_OPS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.FloorDiv: operator.floordiv,
    ast.Mod: operator.mod,
    ast.Pow: operator.pow,
}

UNARY_OPS = {
    ast.UAdd: operator.pos,
    ast.USub: operator.neg,
}


# Evaluation resource limits (DoS prevention). Structural bounds make a
# wall-clock timeout unnecessary: every accepted expression is small enough
# to evaluate instantly in a single thread.
MAX_EXPRESSION_LENGTH = 500
MAX_AST_NODES = 200
MAX_POWER_DIGITS = 1000
MAX_EXPONENT_ABS = 10000
MAX_FACTORIAL_ARG = 170
MAX_RESULT_DIGITS = 1000


def _strict_factorial(value):
    """Integer-only factorial rejecting silent float truncation."""
    if isinstance(value, bool):
        raise ValueError(f"factorial requires an integer, got {value!r}")
    if isinstance(value, float):
        if not value.is_integer():
            raise ValueError(f"factorial requires an integer, got {value}")
        value = int(value)
    if not isinstance(value, int):
        raise ValueError(f"factorial requires an integer, got {value!r}")
    if value > MAX_FACTORIAL_ARG:
        raise ValueError(f"factorial argument too large (max {MAX_FACTORIAL_ARG})")
    return math.factorial(value)


def build_functions(use_degrees: bool):
    """Build whitelisted math functions honoring angle unit."""

    def _trig(func):
        def wrapper(x):
            angle = math.radians(x) if use_degrees else x
            return func(angle)

        return wrapper

    def _inv_trig(func):
        def wrapper(x):
            value = func(x)
            return math.degrees(value) if use_degrees else value

        return wrapper

    return {
        "sqrt": math.sqrt,
        "cbrt": lambda x: math.copysign(abs(x) ** (1 / 3), x),
        "sin": _trig(math.sin),
        "cos": _trig(math.cos),
        "tan": _trig(math.tan),
        "asin": _inv_trig(math.asin),
        "acos": _inv_trig(math.acos),
        "atan": _inv_trig(math.atan),
        "log": lambda x, base=10: math.log(x, base),
        "ln": math.log,
        "exp": math.exp,
        "factorial": _strict_factorial,
        "abs": abs,
        "round": round,
        "pow": pow,
    }


CONSTANTS = {"pi": math.pi, "e": math.e, "tau": math.tau}


def safe_evaluate(expression: str, use_degrees: bool = False):
    """Safely evaluate a math expression using AST whitelist."""
    cleaned = expression.strip().replace("^", "**").replace("÷", "/").replace("×", "*")
    if not cleaned:
        raise ValueError("Empty expression")
    if len(cleaned) > MAX_EXPRESSION_LENGTH:
        raise ValueError(f"Expression exceeds {MAX_EXPRESSION_LENGTH} characters")
    try:
        tree = ast.parse(cleaned, mode="eval")
    except SyntaxError as exc:
        raise ValueError(f"Syntax error: {exc}") from exc
    if _count_nodes(tree) > MAX_AST_NODES:
        raise ValueError(f"Expression too complex (max {MAX_AST_NODES} nodes)")
    functions = build_functions(use_degrees)
    result = _eval_node(tree.body, functions)
    if isinstance(result, complex):
        raise ValueError("Complex results are not supported")
    return result


def _count_nodes(node):
    """Count AST nodes to bound evaluation work before running it."""
    total = 1
    for child in ast.iter_child_nodes(node):
        total += _count_nodes(child)
    return total


def _check_result_size(result):
    """Reject intermediate results that would exhaust memory or display."""
    if isinstance(result, bool):
        return
    if isinstance(result, int):
        if result.bit_length() > 3400:  # ~1023 decimal digits
            raise ValueError(f"Result exceeds {MAX_RESULT_DIGITS} digits")
    elif isinstance(result, float):
        if math.isinf(result) or math.isnan(result):
            raise OverflowError("Result out of range")


def _guarded_pow(base, exponent):
    """Power with magnitude estimation so giants are rejected pre-compute."""
    for operand in (base, exponent):
        if isinstance(operand, bool) or not isinstance(operand, (int, float)):
            raise ValueError(f"Power operands must be numbers, got {operand!r}")
    if isinstance(exponent, float):
        if exponent.is_integer():
            exponent = int(exponent)
        else:
            result = base**exponent
            _check_result_size(result)
            return result
    if abs(exponent) > MAX_EXPONENT_ABS:
        raise ValueError(f"Exponent too large (max {MAX_EXPONENT_ABS})")
    grows = (exponent >= 0 and abs(base) > 1) or (exponent < 0 and 0 < abs(base) < 1)
    if grows and base != 0:
        digits = abs(exponent * math.log10(abs(base)))
        if digits > MAX_POWER_DIGITS:
            raise ValueError(f"Power result exceeds {MAX_POWER_DIGITS} digits")
    try:
        result = base**exponent
    except OverflowError as exc:
        raise OverflowError("Power result out of range") from exc
    _check_result_size(result)
    return result


def _eval_node(node, functions):
    if isinstance(node, ast.Constant):
        if isinstance(node.value, (int, float)):
            return node.value
        raise ValueError(f"Unsupported constant: {node.value!r}")
    if isinstance(node, ast.BinOp):
        op_type = type(node.op)
        if op_type not in BIN_OPS:
            raise ValueError(f"Operator not allowed: {op_type.__name__}")
        left = _eval_node(node.left, functions)
        right = _eval_node(node.right, functions)
        if op_type is ast.Pow:
            return _guarded_pow(left, right)
        result = BIN_OPS[op_type](left, right)
        _check_result_size(result)
        return result
    if isinstance(node, ast.UnaryOp):
        op_type = type(node.op)
        if op_type not in UNARY_OPS:
            raise ValueError(f"Unary operator not allowed: {op_type.__name__}")
        return UNARY_OPS[op_type](_eval_node(node.operand, functions))
    if isinstance(node, ast.Call):
        if not isinstance(node.func, ast.Name):
            raise ValueError("Only direct function calls are allowed")
        name = node.func.id
        if name not in functions:
            raise ValueError(f"Function not allowed: {name}")
        args = [_eval_node(arg, functions) for arg in node.args]
        if node.keywords:
            raise ValueError("Keyword arguments are not allowed")
        return functions[name](*args)
    if isinstance(node, ast.Name):
        if node.id not in CONSTANTS:
            raise ValueError(f"Unknown constant: {node.id}")
        return CONSTANTS[node.id]
    raise ValueError(f"Expression element not allowed: {type(node).__name__}")
