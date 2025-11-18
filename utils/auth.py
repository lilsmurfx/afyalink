# utils/auth.py

from database.db import supabase

# Your JWT secret (for later)
JWT_SECRET = "vVTbDjDDXDp/Yr7v7nhOZgwG1UBuk0kXy/GuiYskWLLearSKh+oXIo2hnLGswptQPFVWMDGOHv7P2pq9vksihA=="

# ----------------------------
# Login function
# ----------------------------
def login(email: str, password: str):
    """
    Logs in a user using email and password.
    Always returns a dict with keys: user, session, role, error
    Login succeeds even if no JWT/session is returned.
    """
    try:
        res = supabase.auth.sign_in_with_password({
            "email": email,
            "password": password
        })

        # If login failed
        if res.get("error") or not res.get("user"):
            return {
                "user": None,
                "session": None,
                "role": None,
                "error": res.get("error", {}).get("message", "Login failed")
            }

        user_id = res["user"]["id"]

        # Determine user role
        role = get_role_from_db(user_id)

        # Accept that session may be None
        return {
            "user": res.get("user"),
            "session": res.get("session"),  # may be None
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
# Signup
# ----------------------------
def signup(email: str, password: str, role: str, full_name: str):
    """
    Registers a new user and inserts into patients or doctors table
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
        if role == "patient":
            supabase.table("patients").insert({"user_id": user_id, "full_name": full_name}).execute()
        else:
            supabase.table("doctors").insert({"user_id": user_id, "full_name": full_name}).execute()

        return {
            "user": res.get("user"),
            "session": res.get("session"),
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
# Determine role
# ----------------------------
def get_role_from_db(user_id: str):
    """
    Returns "patient", "doctor", or "admin"
    """
    patient = supabase.table("patients").select("id").eq("user_id", user_id).execute()
    if patient.data:
        return "patient"

    doctor = supabase.table("doctors").select("id").eq("user_id", user_id).execute()
    if doctor.data:
        return "doctor"

    return "admin"
