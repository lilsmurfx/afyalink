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

# --- Access control ---
if "logged_in" not in st.session_state or not st.session_state["logged_in"]:
    st.warning("Please login first.")
    st.stop()
if st.session_state.get("role") != "patient":
    st.error("Access denied. Patients only.")
    st.stop()

st.set_page_config(page_title="Patient Dashboard", layout="wide")
user_id = st.session_state["user_id"]  # MUST match Supabase Auth UID
user_name = get_user_name(user_id)

# --- CSS ---
st.markdown("""
<style>
.metric-card { background-color: #2E8B57; color: white; border-radius: 12px; padding: 20px; text-align: center; font-weight: bold; box-shadow: 0 4px 6px rgba(0,0,0,0.2);}
.section-title { color: #2E8B57; font-weight: bold; font-size: 20px; margin-bottom: 10px;}
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

# --- Fetch Data ---
records = get_patient_records(user_id)
appointments = get_user_appointments(user_id, "patient")
uploaded_files = get_patient_files(user_id)

# --- Metrics Cards ---
col1, col2, col3 = st.columns(3)
with col1:
    st.markdown(f'<div class="metric-card">🩺<br>Total Visits<br><h2>{len(records)}</h2></div>', unsafe_allow_html=True)
with col2:
    st.markdown(f'<div class="metric-card">📅<br>Total Appointments<br><h2>{len(appointments)}</h2></div>', unsafe_allow_html=True)
with col3:
    next_appt_text = appointments[0]["appointment_time"].strftime("%d %b %Y %H:%M") if appointments else "No upcoming"
    st.markdown(f'<div class="metric-card">⏰<br>Next Appointment<br><h2>{next_appt_text}</h2></div>', unsafe_allow_html=True)

st.markdown("<hr>", unsafe_allow_html=True)

# --- Medical Records ---
st.markdown('<div class="section-title">📄 Your Medical Records</div>', unsafe_allow_html=True)
if records:
    record_df = pd.DataFrame(records)
    search = st.text_input("Search Records by Title")
    filtered_records = record_df[record_df['record_title'].str.contains(search, case=False)] if search else record_df
    st.dataframe(filtered_records[['record_title', 'description']], height=250)
    st.download_button("Download Records as CSV", filtered_records.to_csv(index=False).encode('utf-8'), "medical_records.csv", "text/csv")
else:
    st.info("No medical records found.")

st.markdown("<hr>", unsafe_allow_html=True)

# --- Appointments ---
st.markdown('<div class="section-title">📅 Your Appointments</div>', unsafe_allow_html=True)
if appointments:
    appt_df = pd.DataFrame(appointments).sort_values('appointment_time')
    st.dataframe(appt_df[['appointment_time', 'status']], height=250)
    appt_df['month'] = appt_df['appointment_time'].dt.to_period('M')
    monthly_count = appt_df.groupby('month').size().reset_index(name='count')
    fig = px.bar(monthly_count, x='month', y='count', title="Appointments per Month", text='count', color_discrete_sequence=['#2E8B57'])
    st.plotly_chart(fig, use_container_width=True)
else:
    st.info("No scheduled appointments.")

st.markdown("<hr>", unsafe_allow_html=True)

# --- Upload Files ---
st.markdown('<div class="section-title">🧾 Upload Lab Reports / Prescriptions</div>', unsafe_allow_html=True)
uploaded_file = st.file_uploader("Choose a file", type=["pdf", "png", "jpg", "jpeg"])
if uploaded_file:
    try:
        # Read bytes from UploadedFile
        file_bytes = uploaded_file.read()
        upload_patient_file(user_id, uploaded_file)  # Ensure patient_id = auth.uid()
        st.success(f"File '{uploaded_file.name}' uploaded successfully!")
        st.experimental_rerun()
    except Exception as e:
        st.error(f"Upload failed: {e}")

# --- Uploaded Files Table ---
st.markdown('<div class="section-title">📂 Uploaded Files</div>', unsafe_allow_html=True)
if uploaded_files:
    files_df = pd.DataFrame(uploaded_files).sort_values('uploaded_at', ascending=False)
    for _, row in files_df.iterrows():
        uploaded_at_text = row['uploaded_at'].strftime('%d %b %Y %H:%M') if isinstance(row['uploaded_at'], datetime) else str(row['uploaded_at'])
        st.write(f"- {row['original_name']} (Uploaded: {uploaded_at_text})")
        url = supabase.storage.from_('patient-files').get_public_url(row['file_name'])['public_url']
        st.markdown(f"[Download]({url})")
else:
    st.info("No uploaded files found.")
