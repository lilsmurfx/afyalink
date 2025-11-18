import streamlit as st
from utils.auth import login, signup
from utils.database import get_user_name

st.set_page_config(page_title="AfyaLink", layout="wide")

# --- Initialize session state ---
for key in ["logged_in", "trigger_rerun", "login_email", "login_pass", "user_id", "role", "full_name"]:
    if key not in st.session_state:
        st.session_state[key] = None if key in ["user_id", "role", "full_name"] else False if key=="logged_in" else ""

# --- Header / Description ---
st.markdown(
    "<h1 style='text-align:center; color:#2C3E50;'>AfyaLink Medical System</h1>",
    unsafe_allow_html=True
)
st.markdown(
    "<p style='text-align:center; color:#34495E;'>"
    "AfyaLink is an intuitive medical management platform connecting "
    "<b>patients</b>, <b>doctors</b>, and <b>administrators</b>.<br>"
    "Manage medical records, schedule appointments, and track patient health—all in one secure system."
    "</p>",
    unsafe_allow_html=True
)

# --- Demo login cards ---
st.subheader("💡 Demo Login Accounts")
col1, col2, col3 = st.columns(3)

def fill_demo(email, password):
    st.session_state["login_email"] = email
    st.session_state["login_pass"] = password

card_style = """
<div style='background-color:{bg}; padding:15px; border-radius:10px; text-align:center;'>
    <h4 style='color:white'>{role}</h4>
    <p style='color:white'>{info}</p>
</div>
"""

with col1:
    if st.button("Login as Admin"):
        fill_demo("admin-admin2@gmail.com", "admin2")
    st.markdown(card_style.format(bg="#1abc9c", role="Admin", info="Email: admin-admin2@gmail.com<br>Password: admin2"), unsafe_allow_html=True)

with col2:
    if st.button("Login as Doctor"):
        fill_demo("doctor3@afyalink.com", "doctor3")
    st.markdown(card_style.format(bg="#3498db", role="Doctor", info="Email: doctor3@afyalink.com<br>Password: doctor3"), unsafe_allow_html=True)

with col3:
    if st.button("Login as Patient"):
        fill_demo("patient2@gmail.com", "patient2")
    st.markdown(card_style.format(bg="#e74c3c", role="Patient", info="Email: patient2@gmail.com<br>Password: patient2"), unsafe_allow_html=True)

# --- Logged Out State ---
if not st.session_state["logged_in"]:
    tabs = st.tabs(["Login", "Sign Up"])

    # -------- Login Tab --------
    with tabs[0]:
        st.subheader("Login")
        email = st.text_input("Email", key="login_email")
        password = st.text_input("Password", type="password", key="login_pass")

        if st.button("Login"):
            res = login(email, password)

            # --- Handle login without session/JWT ---
            if not res or res.get("error"):
                st.error(res.get("error", "Login failed. Check credentials."))
            elif not res.get("user"):
                st.error("Login failed: user not found.")
            else:
                user = res["user"]
                st.session_state.update({
                    "logged_in": True,
                    "user_id": user.get("id"),
                    "role": res.get("role", "user"),
                    "full_name": get_user_name(user.get("id")),
                    "trigger_rerun": not st.session_state["trigger_rerun"]
                })
                st.experimental_rerun()

    # -------- Sign Up Tab --------
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

# --- Logged In State ---
else:
    st.success(f"Welcome, {st.session_state.get('full_name', 'User')}!")
    st.info(f"You are logged in as: {st.session_state['role']}")
    st.info("Go to your dashboard from the left panel (Streamlit Pages).")

    if st.button("Logout"):
        st.session_state.update({
            "logged_in": False,
            "user_id": None,
            "role": None,
            "full_name": None,
            "login_email": "",
            "login_pass": "",
            "trigger_rerun": not st.session_state["trigger_rerun"]
        })
        st.experimental_rerun()
