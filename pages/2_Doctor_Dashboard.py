import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
from utils.database import get_doctor_patients, add_record, get_user_appointments, add_appointment, get_user_name

# --- Access control ---
if "logged_in" not in st.session_state or not st.session_state["logged_in"]:
    st.warning("Please login first.")
    st.stop()
if st.session_state.get("role") != "doctor":
    st.error("Access denied. Doctors only.")
    st.stop()

st.set_page_config(page_title="Doctor Dashboard", layout="wide")

doctor_id = st.session_state["user_id"]
doctor_name = get_user_name(doctor_id)

# --- Custom CSS ---
st.markdown("""
<style>
.header-bar {background-color: #2E8B57; padding: 15px; border-radius: 10px; color: white; font-size: 22px; font-weight: bold; margin-bottom: 20px;}
.section-title {font-size: 22px; font-weight: bold; color: #2E8B57; margin-top: 25px;}
.metric-card {background-color: #4CAF50; color: white; padding: 20px; border-radius: 12px; text-align: center; font-weight: bold; box-shadow: 0 4px 6px rgba(0,0,0,0.2);}
</style>
""", unsafe_allow_html=True)

# --- Header Bar ---
st.markdown(f"<div class='header-bar'>👨‍⚕️ Dr. {doctor_name} — Dashboard</div>", unsafe_allow_html=True)

# Logout button
logout_col1, logout_col2 = st.columns([9, 1])
with logout_col2:
    if st.button("Logout"):
        st.session_state.clear()
        st.experimental_rerun()

# ------------------------
# Fetch data
# ------------------------
patients = get_doctor_patients(doctor_id)
appointments = get_user_appointments(doctor_id, "doctor")

# ------------------------
# STAT CARDS
# ------------------------
total_patients = len(patients)
total_appointments = len(appointments)
upcoming_appointments = sum(
    1 for a in appointments if a["appointment_time"] > datetime.now()
) if appointments else 0

col1, col2, col3 = st.columns(3)
with col1:
    st.markdown(f"<div class='metric-card'>🧑‍🤝‍🧑<br>{total_patients}<br>Total Patients</div>", unsafe_allow_html=True)
with col2:
    st.markdown(f"<div class='metric-card' style='background-color:#388E3C;'>📅<br>{total_appointments}<br>All Appointments</div>", unsafe_allow_html=True)
with col3:
    st.markdown(f"<div class='metric-card' style='background-color:#2E7D32;'>⏳<br>{upcoming_appointments}<br>Upcoming Appointments</div>", unsafe_allow_html=True)

# ------------------------
# PATIENT LIST
# ------------------------
st.markdown("<div class='section-title'>🧑‍🤝‍🧑 Your Patients</div>", unsafe_allow_html=True)
if patients:
    patient_df = pd.DataFrame(patients)
    st.dataframe(patient_df[['id', 'name', 'age']], height=200)
else:
    st.info("You have no assigned patients yet.")

# ------------------------
# ADD MEDICAL RECORD
# ------------------------
st.markdown("<div class='section-title'>📝 Add Medical Record</div>", unsafe_allow_html=True)
with st.form("add_record_form"):
    record_patient_id = st.text_input("Patient ID")
    title = st.text_input("Record Title")
    description = st.text_area("Description")
    submitted_record = st.form_submit_button("Save Record")
    if submitted_record:
        if not record_patient_id or not title:
            st.error("Patient ID and Record Title are required.")
        else:
            add_record(record_patient_id, title, description)
            st.success("Medical record added successfully!")
            st.experimental_rerun()

# ------------------------
# SCHEDULE APPOINTMENT
# ------------------------
st.markdown("<div class='section-title'>📅 Schedule Appointment</div>", unsafe_allow_html=True)
if patients:
    patient_choices = {p['name']: p['id'] for p in patients}
    with st.form("schedule_form"):
        patient_name = st.selectbox("Select Patient", list(patient_choices.keys()))
        appointment_patient_id = patient_choices[patient_name]
        date = st.date_input("Select Date", datetime.today())
        time = st.time_input("Select Time", datetime.now().time())
        submitted_appointment = st.form_submit_button("Schedule")
        if submitted_appointment:
            appt_dt = datetime.combine(date, time)
            add_appointment(doctor_id, appointment_patient_id, appt_dt)
            st.success(f"Appointment scheduled for {patient_name} on {appt_dt}")
            st.experimental_rerun()
else:
    st.warning("You have no patients to schedule appointments for.")

# ------------------------
# APPOINTMENTS CALENDAR
# ------------------------
st.markdown("<div class='section-title'>📊 Appointments Calendar</div>", unsafe_allow_html=True)
appointments = get_user_appointments(doctor_id, "doctor")
if appointments:
    df = pd.DataFrame(appointments)
    df['appointment_time'] = pd.to_datetime(df['appointment_time'])
    df['date'] = df['appointment_time'].dt.date
    df['hour'] = df['appointment_time'].dt.hour
    # Map patient_id to name for chart
    patient_map = {p['id']: p['name'] for p in patients}
    df['patient_name'] = df['patient_id'].map(lambda pid: patient_map.get(pid, "Unknown"))
    fig = px.scatter(
        df,
        x='hour',
        y='date',
        color='patient_name',
        hover_data=['status', 'patient_id'],
        labels={'hour': 'Hour of Day', 'date': 'Date'},
        title="Appointments Overview"
    )
    fig.update_layout(yaxis=dict(autorange="reversed"), height=600)
    st.plotly_chart(fig, use_container_width=True)
else:
    st.info("No scheduled appointments yet.")
