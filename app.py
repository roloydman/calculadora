"""Interactive Streamlit calculator with safe expression evaluation."""
import ast
import math
import operator

import streamlit as st


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
        "factorial": lambda x: math.factorial(int(x)),
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
    tree = ast.parse(cleaned, mode="eval")
    functions = build_functions(use_degrees)
    return _eval_node(tree.body, functions)


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
        return BIN_OPS[op_type](left, right)
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


# Session state helpers
def init_state():
    defaults = {
        "expression": "",
        "result": None,
        "error": "",
        "history": [],
        "memory": 0.0,
        "last_answer": 0.0,
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def append_token(token: str):
    st.session_state["expression"] = st.session_state.get("expression", "") + token
    st.session_state["error"] = ""


def recall_answer():
    st.session_state["expression"] = (
        st.session_state.get("expression", "") + str(st.session_state.get("last_answer", 0.0))
    )
    st.session_state["error"] = ""


def recall_memory():
    st.session_state["expression"] = (
        st.session_state.get("expression", "") + str(st.session_state.get("memory", 0.0))
    )
    st.session_state["error"] = ""


def insert_percent():
    st.session_state["expression"] = st.session_state.get("expression", "") + "/100"
    st.session_state["error"] = ""


def backspace():
    st.session_state["expression"] = st.session_state.get("expression", "")[:-1]


def clear_all():
    st.session_state["expression"] = ""
    st.session_state["result"] = None
    st.session_state["error"] = ""


def store_memory():
    if st.session_state.get("result") is not None:
        st.session_state["memory"] = st.session_state.get("memory", 0.0) + float(
            st.session_state["result"]
        )


def clear_memory():
    st.session_state["memory"] = 0.0


def clear_history():
    st.session_state["history"] = []


def calculate(use_degrees: bool, precision: int):
    expression = st.session_state["expression"].strip()
    if not expression:
        st.session_state["error"] = "Type or click an expression first."
        return
    try:
        value = safe_evaluate(expression, use_degrees=use_degrees)
        rounded = round(float(value), precision) if isinstance(value, float) else value
        st.session_state["result"] = rounded
        st.session_state["last_answer"] = float(value)
        st.session_state["history"].insert(0, f"{expression} = {rounded}")
        st.session_state["history"] = st.session_state["history"][:50]
        st.session_state["error"] = ""
    except Exception as exc:  # Keep UI friendly for math errors
        st.session_state["result"] = None
        st.session_state["error"] = f"Invalid expression: {exc}"


# UI
st.set_page_config(page_title="Interactive Calculator", page_icon="🧮", layout="centered")
init_state()

st.title("🧮 Interactive Calculator")
st.caption("Button keypad, typed expressions, scientific functions and history.")

with st.sidebar:
    st.header("Settings")
    mode = st.radio("Input mode", ["Keypad", "Expression", "Both"], index=2)
    use_degrees = st.checkbox("Degrees (instead of radians)", value=True)
    precision = st.slider("Decimal precision", min_value=0, max_value=10, value=6)
    st.divider()
    st.subheader("Memory")
    st.metric("Stored value", f"{st.session_state['memory']}")
    mem_col_a, mem_col_b, mem_col_c = st.columns(3)
    with mem_col_a:
        st.button("M+", key="mem_add", on_click=store_memory)
    with mem_col_b:
        st.button("MR", key="mem_recall", on_click=recall_memory)
    with mem_col_c:
        st.button("MC", key="mem_clear", on_click=clear_memory)

if mode in ("Keypad", "Both"):
    st.subheader("Keypad")
    display = st.session_state["expression"] or "0"
    st.code(display, language="text")

    keypad_rows = [
        ["7", "8", "9", "/", "("],
        ["4", "5", "6", "*", ")"],
        ["1", "2", "3", "-", "sqrt("],
        ["0", ".", "pi", "+", "**"],
    ]
    for row_index, row in enumerate(keypad_rows):
        cols = st.columns(len(row))
        for col_pos, (col_obj, token) in enumerate(zip(cols, row)):
            with col_obj:
                st.button(
                    token,
                    key=f"key_{row_index}_{col_pos}_{token}",
                    use_container_width=True,
                    on_click=append_token,
                    args=(token,),
                )

    sci_rows = [
        ["sin(", "cos(", "tan(", "log(", "ln("],
        ["exp(", "factorial(", "%", "e", "Ans"],
    ]
    st.caption("Scientific")
    for row_index, row in enumerate(sci_rows):
        cols = st.columns(len(row))
        for col_pos, (col_obj, token) in enumerate(zip(cols, row)):
            with col_obj:
                button_key = f"sci_{row_index}_{col_pos}_{token}"
                if token == "Ans":
                    st.button(
                        token,
                        key=button_key,
                        use_container_width=True,
                        on_click=recall_answer,
                    )
                elif token == "%":
                    st.button(
                        token,
                        key=button_key,
                        use_container_width=True,
                        on_click=insert_percent,
                    )
                else:
                    st.button(
                        token,
                        key=button_key,
                        use_container_width=True,
                        on_click=append_token,
                        args=(token,),
                    )

    action_cols = st.columns(4)
    with action_cols[0]:
        st.button("⌫", key="action_back", use_container_width=True, on_click=backspace)
    with action_cols[1]:
        st.button("C", key="action_clear", use_container_width=True, on_click=clear_all)
    with action_cols[2]:
        st.button(
            "=",
            key="action_equals",
            use_container_width=True,
            type="primary",
            on_click=calculate,
            args=(use_degrees, precision),
        )
    with action_cols[3]:
        st.button(
            "00", key="action_00", use_container_width=True, on_click=append_token, args=("00",)
        )

if mode in ("Expression", "Both"):
    st.subheader("Expression")
    # Single source of truth: the widget itself owns "expression".
    # Keypad buttons use on_click callbacks, so typed text and
    # button clicks can no longer overwrite each other.
    st.text_input(
        "Type a formula (example: sqrt(16) + sin(30) * (2 + 3))",
        key="expression",
    )
    if mode == "Expression":
        if st.button("Calculate", key="calc_expression", type="primary"):
            calculate(use_degrees, precision)
    else:
        st.button(
            "Calculate",
            key="calc_both",
            type="primary",
            on_click=calculate,
            args=(use_degrees, precision),
        )

if st.session_state["result"] is not None:
    st.success(f"Result: {st.session_state['result']}")
if st.session_state["error"]:
    st.error(st.session_state["error"])

st.subheader("History")
if st.session_state["history"]:
    for item in st.session_state["history"]:
        st.write(f"- {item}")
    st.button("Clear history", key="clear_history", on_click=clear_history)
else:
    st.info("No calculations yet. Results appear here automatically.")

with st.expander("Supported operations"):
    st.markdown(
        "- Operators: `+ - * / // % **` and parentheses\n"
        "- Constants: `pi`, `e`, `tau`\n"
        "- Functions: `sqrt`, `cbrt`, `sin`, `cos`, `tan`, `asin`, `acos`, `atan`, "
        "`log(x[, base])`, `ln`, `exp`, `factorial`, `abs`, `round`, `pow`\n"
        "- Shortcut: `^` works as power, `Ans` recalls the last answer."
    )
