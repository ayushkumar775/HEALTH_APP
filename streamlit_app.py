import os
import pickle
import streamlit as st
import pandas as pd
from streamlit_option_menu import option_menu
import time
import sqlite3

# ===== DATABASE =====
conn = sqlite3.connect("health.db", check_same_thread=False)
c = conn.cursor()

# ===== FORCE FIX TABLE STRUCTURE (NO ERROR) =====
c.execute("PRAGMA table_info(history)")
columns = c.fetchall()

# If table doesn't exist OR has old structure → recreate
if len(columns) != 5:
    c.execute("DROP TABLE IF EXISTS history")

    c.execute("""
    CREATE TABLE history (
        username TEXT,
        disease TEXT,
        result TEXT,
        risk REAL,
        date TEXT
    )
    """)

    conn.commit()
st.set_page_config(page_title="Health Assistant", layout="wide", page_icon="🧑‍⚕️")


# ===== USERS TABLE =====
c.execute("""
CREATE TABLE IF NOT EXISTS users (
    username TEXT,
    password TEXT
)
""")
conn.commit()

# ================= CSS =================
st.markdown("""
<style>
.result-box {padding:20px;border-radius:12px;margin-top:15px;}
.success-box {background-color:#d4edda;}
.error-box {background-color:#f8d7da;}
.info-box {background-color:#d1ecf1;}
</style>
""", unsafe_allow_html=True)

# ================= 🔥 ANIMATED RISK BAR =================
def show_risk_meter(risk):
    import time

    # clamp value (safety)
    risk = max(0, min(100, int(risk)))

    # color logic
    if risk < 40:
        color = "#28a745"   # green
    elif risk < 75:
        color = "#ffa500"   # orange
    else:
        color = "#dc3545"   # red

    st.markdown("### 📊 Risk Meter")

    placeholder = st.empty()

    for i in range(0, risk + 1):
        html = f"""
        <div style="background:#e0e0e0;border-radius:12px;padding:6px">
            <div style="width:{i}%;background:{color};padding:10px;
            border-radius:12px;text-align:center;color:white;font-weight:bold;
            box-shadow:0 0 8px {color};">
                {i}%
            </div>
        </div>
        """
        placeholder.markdown(html, unsafe_allow_html=True)
        time.sleep(0.01)


# ===== PDF FUNCTION =====
def create_pdf(name, disease, result, risk, advice_list=None):
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, Image
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib import colors
    from datetime import datetime
    import matplotlib.pyplot as plt
    import random
    import os

    file = "report.pdf"
    doc = SimpleDocTemplate(file)
    styles = getSampleStyleSheet()

    # ===== CUSTOM STYLES =====
    center_title = ParagraphStyle(
        'center',
        parent=styles['Title'],
        alignment=1,
        fontSize=18,
        spaceAfter=10
    )

    section_style = ParagraphStyle(
        'section',
        parent=styles['Heading2'],
        textColor=colors.darkblue,
        spaceAfter=6
    )

    content = []

    # ===== HEADER =====
    try:
        logo = Image("logo.png", width=100, height=100)
        logo.hAlign = 'CENTER'
        content.append(logo)
    except:
        pass

    content.append(Paragraph("🩺 AI Health Prediction Report", center_title))
    content.append(Spacer(1, 10))

    # ===== PATIENT DETAILS =====
    patient_id = random.randint(1000, 9999)
    date_now = datetime.now().strftime("%d-%m-%Y %H:%M")

    info_data = [
        ["Patient Name", name],
        ["Patient ID", str(patient_id)],
        ["Disease", disease],
        ["Result", result],
        ["Risk Level", f"{risk:.2f}%"],
        ["Generated On", date_now]
    ]

    table = Table(info_data, colWidths=[150, 250])
    table.setStyle([
        ("BACKGROUND", (0,0), (-1,-1), colors.whitesmoke),
        ("GRID", (0,0), (-1,-1), 0.5, colors.grey),
        ("BOTTOMPADDING", (0,0), (-1,-1), 6),
    ])

    content.append(table)
    content.append(Spacer(1, 15))

    # ===== RISK CATEGORY =====
    if risk < 40:
        level = "Low Risk"
        bar_color = "green"
    elif risk < 75:
        level = "Moderate Risk"
        bar_color = "orange"
    else:
        level = "High Risk"
        bar_color = "red"

    content.append(Paragraph("Risk Analysis", section_style))
    content.append(Paragraph(f"<b>Category:</b> {level}", styles["Normal"]))
    content.append(Spacer(1, 10))

    
    # ===== BETTER GRAPH =====
    import matplotlib.pyplot as plt

    values = [float(Glucose), float(BMI), float(Age)]
    labels = ["Glucose", "BMI", "Age"]

    plt.figure()

    colors = []
    for v, name in zip(values, labels):
        if name == "Glucose":
            colors.append("red" if v > 140 else "green")
        elif name == "BMI":
            colors.append("red" if v > 30 else "green")
        elif name == "Age":
            colors.append("orange" if v > 45 else "green")

    plt.bar(labels, values, color=colors)
    plt.title("Health Parameters Overview")
    plt.ylabel("Values")

    graph_path = "health_chart.png"
    plt.savefig(graph_path)
    plt.close()

    content.append(Image(graph_path, width=300, height=200))
    content.append(Spacer(1, 15))



    # ===== ADVICE =====
    content.append(Paragraph("Recommended Advice", section_style))

    if advice_list:
        for adv in advice_list:
            content.append(Paragraph(f"• {adv}", styles["Normal"]))
    else:
        content.append(Paragraph("• Maintain healthy lifestyle", styles["Normal"]))

    content.append(Spacer(1, 15))

    # ===== DOCTOR =====
    content.append(Paragraph("Doctor Recommendation", section_style))

    if disease == "Diabetes":
        content.append(Paragraph("• Endocrinologist consultation", styles["Normal"]))
        content.append(Paragraph("• HbA1c test required", styles["Normal"]))

    elif disease == "Heart":
        content.append(Paragraph("• Cardiologist consultation", styles["Normal"]))
        content.append(Paragraph("• ECG / Stress test", styles["Normal"]))

    elif disease == "Parkinson":
        content.append(Paragraph("• Neurologist consultation", styles["Normal"]))
        content.append(Paragraph("• Motor assessment required", styles["Normal"]))

    content.append(Spacer(1, 30))

    # ===== SIGNATURE =====
    content.append(Paragraph("__________________________", styles["Normal"]))
    content.append(Paragraph("Authorized Medical System", styles["Normal"]))
    content.append(Spacer(1, 10))

    # ===== FOOTER =====
    content.append(Paragraph(
        "<para align='center'><font size=8>⚠️ AI-generated report. Consult a doctor.</font></para>",
        styles["Normal"]
    ))

    doc.build(content)

    # Cleanup graph file
    if os.path.exists(graph_path):
        os.remove(graph_path)

    return file

# ===== EMAIL FUNCTION =====
def send_email_with_pdf(to_email, subject, message, file_path):
    import smtplib
    from email.mime.multipart import MIMEMultipart
    from email.mime.text import MIMEText
    from email.mime.base import MIMEBase
    from email import encoders

    sender_email = "kkumarsanjay3640@gmail.com"
    sender_password = "rzpyipinkoouzgiw"

    try:
        msg = MIMEMultipart()
        msg["From"] = sender_email
        msg["To"] = to_email
        msg["Subject"] = subject

        msg.attach(MIMEText(message, "plain"))

        with open(file_path, "rb") as f:
            part = MIMEBase("application", "octet-stream")
            part.set_payload(f.read())

        encoders.encode_base64(part)
        part.add_header(
            "Content-Disposition",
            f'attachment; filename="report.pdf"'
        )
        msg.attach(part)

        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        server.login(sender_email, sender_password)
        server.sendmail(sender_email, to_email, msg.as_string())
        server.quit()

        return True

    except Exception as e:
        print("Email Error:", e)
        return False      

# ================= LOAD =================
working_dir = os.path.dirname(os.path.abspath(__file__))

loaded = pickle.load(open(f'{working_dir}/diabetes_model.sav', 'rb'))
if isinstance(loaded, tuple):
    diabetes_model, diabetes_scaler = loaded
else:
    diabetes_model = loaded
    diabetes_scaler = None

heart_model = pickle.load(open(f'{working_dir}/heart_disease_model.sav', 'rb'))
parkinsons_model = pickle.load(open(f'{working_dir}/parkinsons_model.sav', 'rb'))


import hashlib

# ================= SIDEBAR =================
with st.sidebar:

    st.title("🔐 Login System")

    login_user = st.text_input("Username")
    login_pass = st.text_input("Password", type="password")

    # ===== HASH FUNCTION =====
    def hash_password(password):
        return hashlib.sha256(password.encode()).hexdigest()

    # ===== SIGNUP =====
    if st.button("Signup"):
        if login_user == "" or login_pass == "":
            st.warning("Enter username & password")
        else:
            c.execute("SELECT * FROM users WHERE username=?", (login_user,))
            if c.fetchone():
                st.warning("User already exists")
            else:
                hashed = hash_password(login_pass)
                c.execute("INSERT INTO users VALUES (?,?)", (login_user, hashed))
                conn.commit()
                st.success("Account Created")

    # ===== LOGIN =====
    if st.button("Login"):
        hashed = hash_password(login_pass)

        c.execute("SELECT * FROM users WHERE username=? AND password=?",
                  (login_user, hashed))
        data = c.fetchone()

        if data:
            st.session_state.user = login_user
            st.session_state.logged_in = True
            st.success("Logged In")
        else:
            st.error("Invalid Credentials")

    # ===== REMEMBER LOGIN =====
    if "logged_in" in st.session_state and st.session_state.logged_in:
        st.success(f"Welcome {st.session_state.user}")

        # ===== PROFILE =====
        st.markdown("### 👤 Profile")
        st.write(f"Username: {st.session_state.user}")

        # ===== LOGOUT =====
        if st.button("Logout"):
            st.session_state.clear()
            st.success("Logged out")
            st.stop()

# ===== BLOCK APP =====
if "logged_in" not in st.session_state:
    st.warning("🔐 Please login first")
    st.stop()

# ===== MAIN MENU =====
with st.sidebar:
    selected = option_menu(
        'Multiple Disease Prediction System',
        ['Diabetes','Heart Disease','Parkinsons','Doctor Consultation','Emergency Alert','History']
    )

# ================= DIABETES =================

if selected == 'Diabetes':

    st.title("🩺 Diabetes Prediction System")

    # ---- INIT SESSION (ONCE) ----
    if "diabetes_result" not in st.session_state:
        st.session_state.diabetes_result = None
        st.session_state.diabetes_risk = 0   # ✅ FIX: never None

    col1, col2, col3 = st.columns(3)

    with col1:
        Pregnancies = st.text_input('Pregnancies')
        SkinThickness = st.text_input('Skin Thickness')
        DPF = st.text_input('Diabetes Pedigree Function')

    with col2:
        Glucose = st.text_input('Glucose Level')
        Insulin = st.text_input('Insulin Level')
        Age = st.text_input('Age')

    with col3:
        BloodPressure = st.text_input('Blood Pressure')
        BMI = st.text_input('BMI')

    # ---- BUTTON ----
    if st.button("Predict Diabetes"):

        try:
            vals = [float(Pregnancies), float(Glucose), float(BloodPressure),
                    float(SkinThickness), float(Insulin), float(BMI),
                    float(DPF), float(Age)]
        except:
            st.error("⚠️ Please enter all values correctly")
            st.stop()

        df = pd.DataFrame([vals], columns=[
            'Pregnancies','Glucose','BloodPressure','SkinThickness',
            'Insulin','BMI','DiabetesPedigreeFunction','Age'
        ])

        df['BMI_Age'] = df['BMI'] * df['Age']
        df['Glucose_BMI'] = df['Glucose'] * df['BMI']

        df = df[['Pregnancies','Glucose','BloodPressure','SkinThickness',
                 'Insulin','BMI','DiabetesPedigreeFunction','Age',
                 'BMI_Age','Glucose_BMI']]

        if diabetes_scaler:
            df = diabetes_scaler.transform(df)

        pred = diabetes_model.predict(df)

        # ✅ FIX: risk always number
        try:
            prob = diabetes_model.predict_proba(df)
            risk = prob[0][1] * 100
        except:
            risk = 0
        from datetime import datetime

        c.execute("INSERT INTO history VALUES (?,?,?,?,?)",
                (st.session_state.user,
                "Diabetes",   # change for each module
                "Positive" if pred[0]==1 else "Negative",
                risk,
                datetime.now().strftime("%d-%m-%Y %H:%M")))
        conn.commit() 

        st.session_state.diabetes_result = pred
        st.session_state.diabetes_risk = risk

    # ---- DISPLAY ----
    if st.session_state.diabetes_result is not None:

        pred = st.session_state.diabetes_result
        risk = st.session_state.diabetes_risk

        st.markdown("## 📊 Result")

        if risk is not None:
            show_risk_meter(risk)

        if pred[0] == 1:
            st.markdown('<div class="result-box error-box">🚨 Diabetes Detected</div>', unsafe_allow_html=True)
        else:
            st.markdown('<div class="result-box success-box">✅ No Diabetes</div>', unsafe_allow_html=True)
        st.markdown("### 🛑 Advice")
        if float(Glucose) > 140: st.write("🚫 Reduce sugar intake")
        if float(BMI) > 30: st.write("🏃 Lose weight")
        if float(Age) > 45: st.write("🩺 Regular checkups")
        if float(Insulin) == 0: st.write("⚠️ Check insulin levels")

        st.write("🥗 Healthy diet")
        st.write("🧘 Reduce stress")
        st.write("🚶 Daily walking")

        st.markdown("### 🚑 When to Act Immediately")

        # ✅ FIX HERE
        if risk > 75:
            st.error("🚨 High Risk! Consult a doctor immediately")

        if float(Glucose) > 250:
            st.warning("⚠️ Extremely high glucose")
        
        if risk <= 75 and float(Glucose) <= 250:
            st.success("✅ No immediate risk detected")    

        st.markdown("### 👨‍⚕️ Doctor Consultation")
        st.write("• Endocrinologist")
        st.write("• HbA1c test")

        # ---- CHART ----
        st.markdown("### 📊 Health Chart")
        try:
            chart_df = pd.DataFrame({
                "Feature": ["Glucose", "BMI", "Age"],
                "Value": [float(Glucose), float(BMI), float(Age)]
            })
            st.bar_chart(chart_df.set_index("Feature"))
        except:
            pass


        # --- EMAIL + PDF  ----
        name_input = st.text_input("Patient Name", key="name")
        email_input = st.text_input("Email", key="email")

        # 👉 CREATE ADVICE LIST
        advice_list = []

        try:
            if float(Glucose) > 140:
                advice_list.append("Reduce sugar intake")
            if float(BMI) > 30:
                advice_list.append("Lose weight")
            if float(Age) > 45:
                advice_list.append("Regular checkups")
            if float(Insulin) == 0:
                advice_list.append("Check insulin levels")
        except:
            pass

        advice_list += [
            "Healthy diet",
            "Reduce stress",
            "Daily walking"
        ]

        col1, col2 = st.columns(2)

        # 👉 DOWNLOAD PDF
        with col1:
            if st.button("📥 Download Report"):
                if name_input == "":
                    st.error("Enter patient name")
                else:
                    file = create_pdf(name_input, "Diabetes", "Positive", risk, advice_list)

                    with open(file, "rb") as f:
                        st.download_button("⬇️ Click to Download PDF", f)

        # 👉 EMAIL WITH PDF ATTACHMENT
        with col2:
            if st.button("📧 Send Email"):
                if name_input == "" or "@" not in email_input:
                    st.error("Enter valid name & email")
                else:
                    file = create_pdf(name_input, "Diabetes", "Positive", risk, advice_list)

                    success = send_email_with_pdf(
                        email_input,
                        "Diabetes Report",
                        f"Result: Positive\nRisk: {risk:.2f}%",
                        file
                    )

                    if success:
                        st.success("✅ Email with PDF Sent")
                    else:
                        st.error("❌ Failed to send email")



                        
        
# ================= HEART =================
if selected == 'Heart Disease':

    st.title("❤️ Heart Disease Prediction")

    labels = ['age','sex','cp','trestbps','chol','fbs','restecg',
              'thalach','exang','oldpeak','slope','ca','thal']

    inputs = []

    for i in range(0,len(labels),3):
        c1,c2,c3 = st.columns(3)
        with c1: inputs.append(st.text_input(labels[i]))
        if i+1<len(labels):
            with c2: inputs.append(st.text_input(labels[i+1]))
        if i+2<len(labels):
            with c3: inputs.append(st.text_input(labels[i+2]))

    if st.button("Predict Heart"):

        try:
            x = [float(i) for i in inputs]
        except:
            st.error("⚠️ Enter all values correctly")
            st.stop()

        pred = heart_model.predict([x])

        st.markdown("## 📊 Result")

        try:
            prob = heart_model.predict_proba([x])
            risk = prob[0][1]*100
            show_risk_meter(risk)
        except:
            risk = 0
            
        # ===== SAVE HISTORY =====
        from datetime import datetime

        c.execute("INSERT INTO history VALUES (?,?,?,?,?)",
                (st.session_state.user,
                "Diabetes",   # change for each module
                "Positive" if pred[0]==1 else "Negative",
                risk,
                datetime.now().strftime("%d-%m-%Y %H:%M")))
        conn.commit()

        if pred[0]==1:
            st.markdown('<div class="result-box error-box">🚨 Heart Disease</div>', unsafe_allow_html=True)

            st.markdown("### 🛑 Advice")
            if x[4]>240: st.write("🥗 Reduce cholesterol")
            if x[3]>140: st.write("🩺 Control BP")
            if x[8]==1: st.write("⚠️ Avoid heavy exercise")

            st.write("🚭 Stop smoking")
            st.write("🏃 Exercise regularly")
            st.write("🧘 Reduce stress")

            st.markdown("### 🚑 Emergency Alert")
            if risk > 80:
                st.error("🚨 Critical Risk!")
            if x[3] > 180:
                st.warning("⚠️ Very high BP")

            st.markdown("### 👨‍⚕️ Doctor")
            st.write("• Cardiologist")
            st.write("• ECG / Stress test")

        else:
            st.markdown('<div class="result-box success-box">✅ No Heart Disease</div>', unsafe_allow_html=True)
            
            # ===== HEALTH CHART =====
            st.markdown("### 📊 Health Chart")

            try:
                chart_df = pd.DataFrame({
                    "Feature": ["Cholesterol", "Blood Pressure", "Age"],
                    "Value": [float(x[4]), float(x[3]), float(x[0])]
                })
                st.bar_chart(chart_df.set_index("Feature"))
            except:
                st.warning("Chart error")

            # ===== EMAIL + PDF =====
            name_input = st.text_input("Patient Name", key="heart_name")
            email_input = st.text_input("Email", key="heart_email")

            if name_input:
                advice_list = [
                    "Reduce cholesterol" if x[4] > 240 else "",
                    "Control BP" if x[3] > 140 else "",
                    "Avoid heavy exercise" if x[8] == 1 else "",
                    "Stop smoking",
                    "Exercise regularly",
                    "Reduce stress"
                ]

                # remove empty values
                advice_list = [a for a in advice_list if a != ""]

                file = create_pdf(
                    name_input,
                    "Heart",
                    "Positive" if pred[0]==1 else "Negative",
                    risk,
                    advice_list
                )

                with open(file, "rb") as f:
                    st.download_button("📥 Download Report", f)

            if st.button("📧 Send Email (Heart)"):
                if "@" not in email_input:
                    st.error("Enter valid email")
                else:
                    success = send_email_with_pdf(
                        email_input,
                        "Heart Report",
                        f"Risk: {risk:.2f}%",
                        file
                    )

                    if success:
                        st.success("✅ Email Sent")
                    else:
                        st.error("❌ Failed to send email")
            

            
            
            

# ================= PARKINSON =================
if selected == 'Parkinsons':

    st.title("🧠 Parkinson Prediction")

    labels = ['Fo','Fhi','Flo','Jitter%','JitterAbs','RAP','PPQ','DDP',
              'Shimmer','Shimmer_dB','APQ3','APQ5','APQ','DDA','NHR','HNR',
              'RPDE','DFA','spread1','spread2','D2','PPE']

    inputs = []

    for i in range(0,len(labels),3):
        c1,c2,c3 = st.columns(3)
        with c1: inputs.append(st.text_input(labels[i]))
        if i+1<len(labels):
            with c2: inputs.append(st.text_input(labels[i+1]))
        if i+2<len(labels):
            with c3: inputs.append(st.text_input(labels[i+2]))

    if st.button("Predict Parkinson"):

        try:
            x = [float(i) for i in inputs]
        except:
            st.error("⚠️ Enter values correctly")
            st.stop()

        pred = parkinsons_model.predict([x])

        st.markdown("## 📊 Result")

        try:
            prob = parkinsons_model.predict_proba([x])
            risk = prob[0][1]*100
            show_risk_meter(risk)
        except:
            risk = 0
            
        # ===== SAVE HISTORY =====
        from datetime import datetime

        c.execute("INSERT INTO history VALUES (?,?,?,?,?)",
                (st.session_state.user,
                "Diabetes",   # change for each module
                "Positive" if pred[0]==1 else "Negative",
                risk,
                datetime.now().strftime("%d-%m-%Y %H:%M")))
        conn.commit()

        if pred[0]==1:
            st.markdown('<div class="result-box error-box">🚨 Parkinson Detected</div>', unsafe_allow_html=True)

            st.markdown("### 🛑 Advice")
            if x[0] < 150: st.write("🗣️ Speech therapy")
            if x[7] > 0.01: st.write("🧠 Monitor coordination")
            if x[15] < 20: st.write("⚠️ Neurological check")

            st.write("🏃 Exercise")
            st.write("🧘 Stress control")
            st.write("😴 Good sleep")

            st.markdown("### 🚑 Medical Attention")
            if risk > 75:
                st.error("🚨 High Risk!")

            st.markdown("### 👨‍⚕️ Doctor")
            st.write("• Neurologist")

        else:
            st.markdown('<div class="result-box success-box">✅ No Parkinson</div>', unsafe_allow_html=True)
            
            # ===== HEALTH CHART =====
            st.markdown("### 📊 Health Chart")

            try:
                chart_df = pd.DataFrame({
                    "Feature": ["Fo", "Jitter", "Shimmer"],
                    "Value": [float(x[0]), float(x[7]), float(x[15])]
                })
                st.bar_chart(chart_df.set_index("Feature"))
            except:
                st.warning("Chart error")

            # ===== EMAIL + PDF =====
            name_input = st.text_input("Patient Name", key="parkinson_name")
            email_input = st.text_input("Email", key="parkinson_email")

            if name_input:
                advice_list = [
                    "Speech therapy" if x[0] < 150 else "",
                    "Monitor coordination" if x[7] > 0.01 else "",
                    "Neurological check" if x[15] < 20 else "",
                    "Exercise",
                    "Stress control",
                    "Good sleep"
                ]

                advice_list = [a for a in advice_list if a != ""]

                file = create_pdf(
                    name_input,
                    "Parkinson",
                    "Positive" if pred[0]==1 else "Negative",
                    risk,
                    advice_list
                )

                with open(file, "rb") as f:
                    st.download_button("📥 Download Report", f)

            if st.button("📧 Send Email (Parkinson)"):
                if "@" not in email_input:
                    st.error("Enter valid email")
                else:
                    success = send_email_with_pdf(
                        email_input,
                        "Parkinson Report",
                        f"Risk: {risk:.2f}%",
                        file
                    )

                    if success:
                        st.success("✅ Email Sent")
                    else:
                        st.error("❌ Failed to send email")

            

# Doctor's Consultation Group
if selected == 'Doctor Consultation':
    st.title('🩺 Doctor Consultation')

    # Doctor data as a list of dictionaries
    doctors = [
        {'Name': 'Dr Gautam Naik', 'Type': 'Cardiologist', 'Phone': '+91 8069305511', 'Experience': '12 Years', 'Hospital': 'NH-19, South East Delhi, New Delhi, 110076'},
        {'Name': 'Dr Amit Mittal', 'Type': 'Cardiologist', 'Phone': '+91 8062207719', 'Experience': '11 Years', 'Hospital': 'Apollo Hospitals Indraprastha, New Delhi'},
        {'Name': 'Dr Gaurav Gupta', 'Type': 'Diabetologist', 'Phone': '+91 08800737264', 'Experience': '8 Years', 'Hospital': 'Galaxy Royal Shoppe, Gaur City 2, Greater Noida, UP, 201009'},
        {'Name': 'Dr Harsh Bardhan', 'Type': 'Diabetologist', 'Phone': '+91 9917XXXXXX', 'Experience': '10 Years', 'Hospital': '112 City Plaza, Gaur City-1, Sector 4, Noida, UP, 201009'},
        {'Name': 'Dr Mohit Bhatt', 'Type': 'Neurology', 'Phone': '+91 8010994994', 'Experience': '38 Years', 'Hospital': 'Kokilaben Dhirubani Hospital, Andheri, Mumbai'},
        {'Name': 'Dr Debashis Bhattacharyya', 'Type': 'Neurology', 'Phone': '+91 8010994994', 'Experience': '22 Years', 'Hospital': 'Narayana Multispeciality Hospital, Howrah, Kolkata'},
        {'Name': 'Dr Ajay Nihalani', 'Type': 'Psychiatrist', 'Phone': '+91 08130491951', 'Experience': '12 Years', 'Hospital': 'Rajhans Plaza, Ahinsa Khand-I, Indirapuram, Ghaziabad, UP'},
        {'Name': 'Dr Kapil K. Singhal', 'Type': 'Neurologist', 'Phone': '+91 9087898765', 'Experience': '22 Years', 'Hospital': '135, Opposite Avantika Hospital, Niti Khand 2, Ghaziabad, UP'},
        {'Name': 'Dr (Lt Den) C.S. Narayanan', 'Type': 'Neurologist', 'Phone': '+91 8372553627', 'Experience': '12 Years', 'Hospital': 'Manipal Hospital, Ghaziabad'}
    ]

    # Display each doctor one by one in a vertical format
    for doc in doctors:
        st.subheader(doc['Name'])
        st.write(f"**Type:** {doc['Type']}")
        st.write(f"**Phone:** {doc['Phone']}")
        st.write(f"**Experience:** {doc['Experience']}")
        st.write(f"**Hospital:** {doc['Hospital']}")
        st.markdown("---")  # divider line between doctors

# # Emergency Alert
# if selected == 'Emergency Alert':
#     st.title('Emergency Alert')
#     col1, col2, col3, col4, col5 = st.columns(5)
    
#     # HTML with inline CSS
#     with col1:
#         st.markdown('<p style="color:red; font-size: 28px;"><b>Working on...</b></p>', unsafe_allow_html=True)
    
    # Emergency Alert
if selected == 'Emergency Alert':
    st.title('🚨 Emergency Alert System')

    st.info("This section helps you reach emergency services quickly. "
            "Use the buttons or call the helplines below in case of urgent medical needs.")

    # Columns for layout
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("📞 Emergency Helpline Numbers")
        st.write("🚑 **National Ambulance Helpline:** 102 / 108")
        st.write("🚓 **Police Helpline:** 100")
        st.write("🔥 **Fire Service:** 101")
        st.write("🧑‍⚕️ **Medical Helpline:** +91 8010 999 111")
        st.write("💊 **Poison Control Center:** 1800-11-6117")

    with col2:
        st.subheader("🏥 Nearby Hospitals (Sample Data)")
        st.write("• AIIMS Hospital, New Delhi — +91 11 2658 8500")
        st.write("• Apollo Hospital, New Delhi — +91 11 2987 1000")
        st.write("• Fortis Hospital, Noida — +91 120 430 0222")
        st.write("• Max Super Specialty, Saket — +91 11 2651 5050")

    st.markdown("---")

    st.subheader("⚡ Quick Alert System")
    name = st.text_input("Enter Your Name")
    location = st.text_input("Enter Your Current Location / City")
    contact = st.text_input("Enter Your Contact Number")

    if st.button("🚨 Send Emergency Alert"):
        if name and location and contact:
            st.success(f"✅ Emergency Alert Sent!\n\n"
                       f"Name: {name}\n"
                       f"Location: {location}\n"
                       f"Contact: {contact}\n\n"
                       f"Authorities have been notified (demo message).")
        else:
            st.warning("⚠️ Please fill in all details before sending the alert.")

# ================= 📜 HISTORY =================
if selected == 'History':

    st.title("📜 Prediction History")

    # ===== FETCH DATA =====
    c.execute("SELECT * FROM history WHERE username=?", (st.session_state.user,))
    data = c.fetchall()

    if len(data) == 0:
        st.info("No history found")
        st.stop()

    # ===== FILTER =====
    disease_filter = st.selectbox("Filter by Disease",
                                 ["All", "Diabetes", "Heart", "Parkinson"])

    search_name = st.text_input("Search by Name")

    # ===== APPLY FILTER =====
    filtered = []

    for row in data:
        name, disease, result, risk, date = row

        if disease_filter != "All" and disease != disease_filter:
            continue

        if search_name and search_name.lower() not in name.lower():
            continue

        filtered.append(row)

    # ===== GRAPH =====
    import plotly.express as px
    import pandas as pd

    st.markdown("### 📊 Risk Trend")

    if len(filtered) == 1:
        st.info(f"Only one record: {filtered[0][3]:.2f}%")
        st.progress(filtered[0][3] / 100)

    elif len(filtered) > 1:

        df_chart = pd.DataFrame({
            "Date": [row[4] for row in filtered],
            "Risk": [row[3] for row in filtered]
        })

        # ===== COLOR LOGIC =====
        colors = ["green" if r < 40 else "orange" if r < 75 else "red"
                for r in df_chart["Risk"]]

        # ===== SCATTER GRAPH =====
        fig = px.scatter(
            df_chart,
            x="Date",
            y="Risk",
            color=colors,
            title="Risk Level Visualization"
        )

        fig.update_traces(marker=dict(size=10))

        fig.update_layout(
            xaxis_title="Date",
            yaxis_title="Risk (%)",
            template="plotly_dark",
            showlegend=False
        )

        st.plotly_chart(fig, use_container_width=True)
        
        fig.update_traces(
            line=dict(color="#00BFFF", width=3),
            marker=dict(size=8)
        )

        fig.update_layout(
            xaxis_title="Date",
            yaxis_title="Risk (%)",
            template="plotly_dark"
        )

        st.plotly_chart(fig, use_container_width=True)

    # ===== SHOW DATA =====
    st.markdown("### 📋 Records")

    for i, row in enumerate(filtered[::-1]):
        name, disease, result, risk, date = row

        st.write(f"""
        🧑 {name}  
        🏥 {disease}  
        📊 {result}  
        ⚠️ {risk:.2f}%  
        📅 {date}
        """)

        # ===== DOWNLOAD PDF =====
        if st.button(f"📄 Download {i}"):

            file = create_pdf(
                name,
                disease,
                result,
                risk,
                ["Follow medical advice"]
            )

            with open(file, "rb") as f:
                st.download_button(f"Download Report {i}", f)

    # ===== CLEAR HISTORY =====
    if st.button("🗑 Clear All History"):
        c.execute("DELETE FROM history WHERE username=?", (st.session_state.user,))
        conn.commit()
        st.success("History Cleared")

