from supabase_config import supabase
from datetime import datetime
import uuid

# -----------------------
# Users / Admin functions
# -----------------------
def get_all_users():
    res = supabase.table("users").select("*").execute()
    return res.data if res.data else []

def get_all_patients():
    res = supabase.table("patients").select("*").execute()
    return res.data if res.data else []

def add_patient(name: str, age: int, doctor_id: str, create_user: bool = True):
    supabase.table("patients").insert({
        "name": name,
        "age": age,
        "doctor_id": doctor_id,
        "created_at": datetime.utcnow().isoformat()
    }).execute()

    if create_user:
        existing = supabase.table("users").select("*").eq("full_name", name).execute()
        if not existing.data:
            supabase.table("users").insert({
                "full_name": name,
                "role": "patient",
                "email": "",
                "password": ""
            }).execute()

def get_user_name(user_id: str):
    res = supabase.table("users").select("full_name").eq("id", user_id).single().execute()
    return res.data["full_name"] if res.data else "User"

# -----------------------
# Doctor functions
# -----------------------
def get_doctor_patients(doctor_id: str):
    res = supabase.table("patients").select("*").eq("doctor_id", doctor_id).execute()
    return res.data if res.data else []

def add_record(patient_id: str, title: str, description: str):
    supabase.table("medical_records").insert({
        "patient_id": patient_id,
        "record_title": title,
        "description": description,
        "created_at": datetime.utcnow().isoformat()
    }).execute()

def add_appointment(doctor_id: str, patient_id: str, appointment_time: datetime):
    supabase.table("appointments").insert({
        "doctor_id": doctor_id,
        "patient_id": patient_id,
        "appointment_time": appointment_time.isoformat(),
        "status": "scheduled",
        "created_at": datetime.utcnow().isoformat()
    }).execute()

# -----------------------
# Appointments / Patients
# -----------------------
def get_user_appointments(user_id: str, role: str):
    if role == "doctor":
        res = supabase.table("appointments").select("*").eq("doctor_id", user_id).execute()
    else:
        res = supabase.table("appointments").select("*").eq("patient_id", user_id).execute()
    appointments = res.data if res.data else []
    for appt in appointments:
        if "appointment_time" in appt:
            appt["appointment_time"] = datetime.fromisoformat(appt["appointment_time"])
        if "created_at" in appt:
            appt["created_at"] = datetime.fromisoformat(appt["created_at"])
    return appointments

# -----------------------
# Patient records
# -----------------------
def get_patient_records(patient_id: str):
    res = supabase.table("medical_records").select("*").eq("patient_id", patient_id).execute()
    records = res.data if res.data else []
    for r in records:
        if "created_at" in r:
            r["created_at"] = datetime.fromisoformat(r["created_at"])
    return records

# -----------------------
# Admin / Unassign
# -----------------------
def unassign_patient(patient_id: str):
    supabase.table("patients").update({"doctor_id": None}).eq("id", patient_id).execute()

# -----------------------
# Patient File Uploads
# -----------------------
def upload_patient_file(patient_id: str, file, user_token: str):
    """
    Upload a patient's file to Supabase Storage and save record in DB.
    Accepts Streamlit UploadedFile objects.
    Requires the logged-in user's JWT for authenticated upload.
    """
    if not file:
        return None

    file_ext = file.name.split('.')[-1]
    file_name = f"{patient_id}/{uuid.uuid4()}.{file_ext}"

    # Upload file using the user's JWT token (RLS compliant)
    res = supabase.storage.from_('patient-files').upload(file_name, file.read(), token=user_token)

    if res.status_code in [200, 201]:
        # Record file metadata in database
        supabase.table('patient_files').insert({
            "patient_id": patient_id,
            "file_name": file_name,
            "original_name": file.name,
            "uploaded_at": datetime.utcnow().isoformat()
        }).execute()
        return file_name
    else:
        raise Exception(f"Upload failed: {res.error}")

def get_patient_files(patient_id: str):
    """Return all files uploaded by a patient"""
    res = supabase.table('patient_files').select("*").eq("patient_id", patient_id).execute()
    files = res.data if res.data else []
    for f in files:
        if "uploaded_at" in f:
            f["uploaded_at"] = datetime.fromisoformat(f["uploaded_at"])
    return files
