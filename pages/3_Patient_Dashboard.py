import streamlit as st
import pandas as pd
import plotly.express as px
from utils.database import (
    get_patient_records,
    get_user_appointments,
    get_user_name,
    upload_patient_file,
    get_patient_files
)
from supabase_config import supabase
from datetime import datetime

st.set_page_config(page_title="Patient Dashboard", layout="wide")

# --- Auth checks ---
if "logged_in" not in st.session_state or not st.session_state["logged_in"]:
    st.warning("Please login first.")
    st.stop()

if st.session_state.get("role") != "patient":
    st.error("Access denied. Patients only.")
    st.stop()

# --- User info ---
user_id = st.session_state["user_id"]  # Supabase auth UID
# support both names in session state if you called it differently
user_token = st.session_state.get("access_token") or st.session_state.get("user_token")
user_name = get_user_name(user_id)

# --- CSS ---
st.markdown("""
<style>
.metric-card {
    background-color: #2E8B57;
    color: white;
    border-radius: 12px;
    padding: 20px;
    text-align: center;
    font-weight: bold;
    box-shadow: 0 4px 6px rgba(0,0,0,0.2);
}
.section-title {
    color: #2E8B57;
    font-weight: bold;
    font-size: 20px;
    margin-bottom: 10px;
}
.file-row {
    padding: 8px 0;
    border-bottom: 1px solid #eee;
}
</style>
""", unsafe_allow_html=True)

# --- Header ---
st.markdown(f"""
<div style="
    background-color: #2E8B57;
    padding: 12px;
    border-radius: 12px;
    color: white;
    font-size: 20px;
    display: flex;
    justify-content: space-between;
    align-items: center;">
    <div>👤 {user_name} | Role: Patient</div>
    <div><button onclick="window.location.reload();">Logout</button></div>
</div>
""", unsafe_allow_html=True)

# Helper to safely try rerun
def safe_rerun():
    try:
        st.experimental_rerun()
    except Exception:
        # fallback: do nothing (the page will still show updated data if we re-fetch)
        pass

# --- Fetch Data (fresh) ---
records = get_patient_records(user_id) or []
appointments = get_user_appointments(user_id, "patient") or []
uploaded_files = get_patient_files(user_id) or []

# Normalize appointment_time in case database returned strings
for a in appointments:
    if "appointment_time" in a and not isinstance(a["appointment_time"], datetime):
        try:
            a["appointment_time"] = datetime.fromisoformat(a["appointment_time"])
        except Exception:
            # try pandas fallback
            a["appointment_time"] = pd.to_datetime(a.get("appointment_time"))

# --- Metrics Cards ---
col1, col2, col3 = st.columns(3)
with col1:
    st.markdown(f'<div class="metric-card">🩺<br>Total Visits<br><h2>{len(records)}</h2></div>', unsafe_allow_html=True)
with col2:
    st.markdown(f'<div class="metric-card">📅<br>Total Appointments<br><h2>{len(appointments)}</h2></div>', unsafe_allow_html=True)
with col3:
    next_appt_text = "No upcoming"
    if appointments:
        # pick next future appointment if present
        future_appts = [a for a in appointments if isinstance(a.get("appointment_time"), (datetime, pd.Timestamp)) and a["appointment_time"] >= datetime.now()]
        if future_appts:
            next_appt = sorted(future_appts, key=lambda x: x["appointment_time"])[0]
            next_appt_text = next_appt["appointment_time"].strftime("%d %b %Y %H:%M")
        else:
            # fallback to first appointment displayed
            appt0 = appointments[0]
            if isinstance(appt0.get("appointment_time"), (datetime, pd.Timestamp)):
                next_appt_text = appt0["appointment_time"].strftime("%d %b %Y %H:%M")
    st.markdown(f'<div class="metric-card">⏰<br>Next Appointment<br><h2>{next_appt_text}</h2></div>', unsafe_allow_html=True)

st.markdown("<hr>", unsafe_allow_html=True)

# --- Medical Records ---
st.markdown('<div class="section-title">📄 Your Medical Records</div>', unsafe_allow_html=True)
if records:
    record_df = pd.DataFrame(records)
    search = st.text_input("Search Records by Title")
    if search:
        filtered_records = record_df[record_df['record_title'].str.contains(search, case=False, na=False)]
    else:
        filtered_records = record_df
    # guard columns
    cols = [c for c in ['record_title', 'description'] if c in filtered_records.columns]
    st.dataframe(filtered_records[cols], height=250)
    st.download_button("Download Records as CSV", filtered_records.to_csv(index=False).encode('utf-8'), "medical_records.csv", "text/csv")
else:
    st.info("No medical records found.")

st.markdown("<hr>", unsafe_allow_html=True)

# --- Appointments ---
st.markdown('<div class="section-title">📅 Your Appointments</div>', unsafe_allow_html=True)
if appointments:
    appt_df = pd.DataFrame(appointments).sort_values('appointment_time')
    # ensure columns exist
    appt_cols = [c for c in ['appointment_time', 'status'] if c in appt_df.columns]
    st.dataframe(appt_df[appt_cols], height=250)

    # chart
    try:
        appt_df['month'] = pd.to_datetime(appt_df['appointment_time']).dt.to_period('M')
        monthly_count = appt_df.groupby('month').size().reset_index(name='count')
        fig = px.bar(monthly_count, x='month', y='count', title="Appointments per Month", text='count', color_discrete_sequence=['#2E8B57'])
        st.plotly_chart(fig, use_container_width=True)
    except Exception:
        # if conversion fails, skip chart
        pass
else:
    st.info("No scheduled appointments.")

st.markdown("<hr>", unsafe_allow_html=True)

# --- Upload Files ---
st.markdown('<div class="section-title">🧾 Upload Lab Reports / Prescriptions</div>', unsafe_allow_html=True)
uploaded_file = st.file_uploader("Choose a file", type=["pdf", "png", "jpg", "jpeg"])
if uploaded_file:
    if not user_token:
        st.error("User token missing (access_token). Please login again so uploads are allowed.")
    else:
        try:
            # upload_patient_file is expected to accept (patient_id, file, user_token)
            file_name = upload_patient_file(patient_id=user_id, file=uploaded_file, user_token=user_token)
            st.success(f"File '{uploaded_file.name}' uploaded successfully!")
            # re-fetch files list (so newly uploaded file appears immediately)
            uploaded_files = get_patient_files(user_id) or []
            # attempt rerun to refresh entire page (safe)
            safe_rerun()
        except Exception as e:
            st.error(f"Upload failed: {e}")

st.markdown("<hr>", unsafe_allow_html=True)

# --- Uploaded Files Table ---
st.markdown('<div class="section-title">📂 Uploaded Files</div>', unsafe_allow_html=True)
if uploaded_files:
    # Normalize uploaded_at to datetime if string
    files_df = pd.DataFrame(uploaded_files)
    if 'uploaded_at' in files_df.columns:
        def to_dt(x):
            if isinstance(x, (datetime, pd.Timestamp)):
                return x
            try:
                return datetime.fromisoformat(x)
            except Exception:
                try:
                    return pd.to_datetime(x)
                except Exception:
                    return x
        files_df['uploaded_at'] = files_df['uploaded_at'].apply(to_dt)

    files_df = files_df.sort_values('uploaded_at', ascending=False)
    for _, row in files_df.iterrows():
        orig = row.get('original_name') or row.get('file_name')
        uploaded_at = row.get('uploaded_at')
        uploaded_at_text = uploaded_at.strftime('%d %b %Y %H:%M') if isinstance(uploaded_at, (datetime, pd.Timestamp)) else str(uploaded_at)
        st.markdown(f"<div class='file-row'>**{orig}** — uploaded: {uploaded_at_text}</div>", unsafe_allow_html=True)

        # build public url robustly depending on supabase client response shape
        try:
            public_resp = supabase.storage.from_('patient-files').get_public_url(row['file_name'])
            # client might return dict with 'publicUrl' or 'public_url'
            url = public_resp.get('publicUrl') or public_resp.get('public_url') or public_resp.get('data') or public_resp
            # if nested dict
            if isinstance(url, dict):
                url = url.get('publicUrl') or url.get('public_url') or url.get('url')
            # as a final fallback, attempt string
            if not isinstance(url, str):
                url = str(public_resp)
        except Exception:
            url = None

        if url:
            st.markdown(f"[Download]({url})")
        else:
            st.write("Download URL not available.")
else:
    st.info("No uploaded files found.")
