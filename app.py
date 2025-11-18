import streamlit as st
from utils.auth import login, signup
from utils.database import get_user_name

st.set_page_config(page_title="AfyaLink", layout="wide")

# --- Initialize session state ---
default_state = {
    "logged_in": False,
    "trigger_rerun": False,
    "login_email": "",
    "login_pass": "",
    "user_id": None,
    "role": None,
    "full_name": None,
    "access_token": None
}

for key, value in default_state.items():
    if key not in st.session_state:
        st.session_state[key] = value


# --- Header ---
st.markdown(
    "<h1 style='text-align:center; color:#2C3E50;'>AfyaLink Medical System</h1>",
    unsafe_allow_html=True
)

st.markdown("<hr>", unsafe_allow_html=True)


# =============================
# NOT LOGGED IN
# =============================
if not st.session_state["logged_in"]:

    tabs = st.tabs(["Login", "Sign Up"])

    # ---------------------------------------------------------
    # LOGIN TAB
    # ---------------------------------------------------------
    with tabs[0]:
        st.subheader("Login")

        email = st.text_input("Email", key="login_email")
        password = st.text_input("Password", type="password", key="login_pass")

        if st.button("Login"):
            res = login(email, password)

            # Login failed → show error
            if not res or res.get("error"):
                st.error(res.get("error", "Login failed. Check credentials."))
            
            elif not res.get("user"):
                st.error("Login failed: No user returned.")
            
            else:
                user = res["user"]

                # Store login info
                st.session_state["logged_in"] = True
                st.session_state["user_id"] = user["id"]
                st.session_state["role"] = res.get("role", "patient")

                # Fetch full name if exists, else fallback
                st.session_state["full_name"] = user.get(
                    "user_metadata", {}
                ).get("full_name", "User")

                # No JWT for now
                st.session_state["access_token"] = None

                st.success("Login successful!")
                st.experimental_rerun()


    # ---------------------------------------------------------
    # SIGNUP TAB
    # ---------------------------------------------------------
    with tabs[1]:
        st.subheader("Sign Up")

        full_name = st.text_input("Full Name", key="signup_name")
        email = st.text_input("Email", key="signup_email")
        password = st.text_input("Password", type="password", key="signup_pass")
        role = st.selectbox("Role", ["patient", "doctor"])

        if st.button("Sign Up"):
            res = signup(email, password, role, full_name)

            if res.get("error"):
                st.error(res["error"])
            else:
                st.success("Signup successful! Please login.")


# =============================
# LOGGED IN VIEW
# =============================
else:
    st.success(f"Welcome, {st.session_state.get('full_name', 'User')}!")
    st.info(f"You are logged in as: {st.session_state['role']}")
    st.info("Use the left sidebar to navigate to your dashboard.")

    # Logout Button
    if st.button("Logout"):
        st.session_state.update({
            "logged_in": False,
            "user_id": None,
            "role": None,
            "full_name": None,
            "login_email": "",
            "login_pass": "",
            "access_token": None,
            "trigger_rerun": not st.session_state["trigger_rerun"]
        })
        st.experimental_rerun()
