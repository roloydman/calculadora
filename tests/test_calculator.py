"""Backend tests for the calculator safe evaluator."""
import math
import time

import pytest

from calculator import safe_evaluate


def test_basic_arithmetic():
    assert safe_evaluate("2+3*4") == 14
    assert safe_evaluate("(2+3)*4") == 20
    assert safe_evaluate("7-10") == -3
    assert safe_evaluate("7/2") == 3.5


def test_power_aliases():
    assert safe_evaluate("2**10") == 1024
    assert safe_evaluate("2^3") == 8
    assert safe_evaluate("10**100") == 10**100


def test_functions_and_constants():
    assert safe_evaluate("sqrt(16)") == 4.0
    assert safe_evaluate("factorial(5)") == 120
    assert safe_evaluate("pi*2") == pytest.approx(math.pi * 2)
    assert safe_evaluate("log(100)") == pytest.approx(2.0)
    assert safe_evaluate("ln(e)") == pytest.approx(1.0)


def test_degree_trigonometry():
    assert safe_evaluate("sin(30)", use_degrees=True) == pytest.approx(0.5)
    assert safe_evaluate("cos(60)", use_degrees=True) == pytest.approx(0.5)


def test_radian_trigonometry():
    assert safe_evaluate("sin(pi/2)", use_degrees=False) == pytest.approx(1.0)


def test_strict_factorial_accepts_integers():
    assert safe_evaluate("factorial(0)") == 1
    assert safe_evaluate("factorial(5.0)") == 120


def test_strict_factorial_rejects_floats():
    with pytest.raises(ValueError, match="requires an integer"):
        safe_evaluate("factorial(5.9)")
    with pytest.raises(ValueError, match="requires an integer"):
        safe_evaluate("factorial(5.5)")


def test_factorial_rejects_negative_and_huge():
    with pytest.raises(ValueError):
        safe_evaluate("factorial(-1)")
    with pytest.raises(ValueError, match="too large"):
        safe_evaluate("factorial(171)")


def test_giant_power_rejected_instantly():
    start = time.time()
    with pytest.raises((ValueError, OverflowError)):
        safe_evaluate("9**9**9")
    assert time.time() - start < 5


def test_oversized_inputs_rejected():
    with pytest.raises(ValueError, match="exceeds"):
        safe_evaluate("1+" * 300)
    with pytest.raises(ValueError, match="exceeds"):
        safe_evaluate("10**2000")


def test_code_injection_blocked():
    with pytest.raises(ValueError):
        safe_evaluate("__import__('os').system('echo hacked')")
    with pytest.raises(ValueError):
        safe_evaluate("eval('1+1')")
    with pytest.raises(ValueError):
        safe_evaluate("unknown(42)")


def test_invalid_and_empty_inputs():
    with pytest.raises(ValueError):
        safe_evaluate("")
    with pytest.raises(ValueError):
        safe_evaluate("2+")
    with pytest.raises(ZeroDivisionError):
        safe_evaluate("1/0")
