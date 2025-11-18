# utils/auth.py

from database.db import supabase

# Replace with your JWT secret for optional token verification
JWT_SECRET = "vVTbDjDDXDp/Yr7v7nhOZgwG1UBuk0kXy/GuiYskWLLearSKh+oXIo2hnLGswptQPFVWMDGOHv7P2pq9vksihA=="

# ----------------------------
# Login function
# ----------------------------
def login(email: str, password: str):
    """
    Logs in a user using email and password.
    Always returns a dict with keys: user, session, role, error
    """
    try:
        res = supabase.auth.sign_in_with_password({
            "email": email,
            "password": password
        })

        # If login failed
        if res.get("error") or not res.get("user") or not res.get("session"):
            return {
                "user": None,
                "session": None,
                "role": None,
                "error": res.get("error", {}).get("message", "Login failed")
            }

        user_id = res["user"]["id"]

        # Fetch role from your users table (replace "patients" or "doctors" logic as needed)
        role = fetch_user_role(user_id)

        return {
            "user": res["user"],
            "session": res["session"],
            "role": role,
            "error": None
        }

    except Exception as e:
        return {
            "user": None,
            "session": None,
            "role": None,
            "error": str(e)
        }

# ----------------------------
# Signup function
# ----------------------------
def signup(email: str, password: str, role: str, full_name: str):
    """
    Signs up a user and inserts into role table (patients or doctors)
    Returns dict with keys: user, session, role, error
    """
    try:
        res = supabase.auth.sign_up({
            "email": email,
            "password": password
        })

        if res.get("error") or not res.get("user"):
            return {
                "user": None,
                "session": None,
                "role": None,
                "error": res.get("error", {}).get("message", "Signup failed")
            }

        user_id = res["user"]["id"]

        # Insert into role-specific table
        table_name = "patients" if role == "patient" else "doctors"
        supabase.table(table_name).insert({
            "user_id": user_id,
            "full_name": full_name,
            "email": email
        }).execute()

        return {
            "user": res["user"],
            "session": None,  # Signup does not create session automatically
            "role": role,
            "error": None
        }

    except Exception as e:
        return {
            "user": None,
            "session": None,
            "role": None,
            "error": str(e)
        }

# ----------------------------
# Helper: fetch user role from your tables
# ----------------------------
def fetch_user_role(user_id: str):
    """
    Returns "patient", "doctor", or "admin" based on user_id
    """
    # Check patients table
    patient = supabase.table("patients").select("id").eq("user_id", user_id).execute()
    if patient.data:
        return "patient"

    # Check doctors table
    doctor = supabase.table("doctors").select("id").eq("user_id", user_id).execute()
    if doctor.data:
        return "doctor"

    # Default fallback
    return "admin"
