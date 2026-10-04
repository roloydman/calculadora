"""Interactive Streamlit calculator UI (backend lives in calculator.py)."""
import streamlit as st

from calculator import safe_evaluate


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
        "- Shortcut: `^` works as power, `Ans` recalls the last answer.\n"
        "- Limits: 500 chars, results capped at ~1000 digits, factorial up to 170."
    )
