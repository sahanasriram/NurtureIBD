import streamlit as st
import pdfplumber
import pytesseract
from PIL import Image
import google.generativeai as genai
import pandas as pd

# Authenticator Code for session and logout START
from auth_config import authenticator


# st.set_page_config(page_title="Chronical Dashboard", initial_sidebar_state="collapsed")
import streamlit as st

for key in ['authentication_status', 'username', 'name']:
    if key not in st.session_state:
        st.session_state[key] = None

if st.session_state.get("authentication_status"):
    # Show your page content
    st.write(f"Welcome, {st.session_state['name']}!")
    authenticator.logout("Logout", "main")
else:
    st.warning("Please log in to access this page." , )
    if st.button("Go to Login →"):
        st.switch_page("./AppLogin.py")
    st.stop()

# Authenticator Code for session and logout END

# Setup Tesseract OCR
pytesseract.pytesseract.tesseract_cmd = r'C:\\Program Files\\Tesseract-OCR\\tesseract.exe'

# Gemini API Setup
genai.configure(api_key=st.secrets["apikey"])
model = genai.GenerativeModel("gemini-2.5-flash")

# Sidebar
st.sidebar.title("📋 Menu")
page = st.sidebar.selectbox("Go to", ["Home","Patient Entry & Upload", "AI Analysis"])
# Homepage
if page=="Home":
    st.title("🏥 Welcome to the Patient Care App")

    st.subheader("ℹ️ About this App")
    st.write("""
   
    This app is built using Streamlit.
    Nurture IBD is a health platform built to bridge the gap between medical visits and daily life for people managing chronic illnesses such as Inflammatory Bowel Disease, 
    celiac disease, diabetes, and kidney disease. Many patients struggle to make sense of complex medical data and apply it to their everyday choices — that’s where we step in.
    Our app makes it simple to track symptoms, upload lab reports, and store detailed health history. Using AI, Nurture IBD interprets this data to provide personalized diet guidance, 
    medicine reminders, and care suggestions tailored to each individual. With an easy-to-use design, we empower patients to take control of their health, improve communication with their doctors, 
    and make informed decisions that enhance their quality of life.
    This application helps patients and doctors by:
    - Collecting important patient information
    - Uploading and analyzing blood reports
    - Generating personalized **Diet Plans**
    - Suggesting **Medication & Supplement Schedules**
    - Interpreting **Blood Analysis Reports** in a simple way
    """)

    st.subheader("📖 How to Use")
    st.write("""
    1. Go to **Patient Entry & Upload** to enter your details and upload reports.  
    2. Then switch to **AI Analysis** to view diet, medication, and report analysis.  
    3. You can always return here to re-read the instructions.
    """)

    st.info("💡 Tip: Upload your most recent blood test for the best recommendations.")

# Initialize patient history and report text
if 'patient_history' not in st.session_state:
    st.session_state.patient_history = {
        "Name": "",
        "Age": 18,
        "Gender": "",
        "Height": "",
        "Weight": "",
        "Location": "",
        "Tobacco use": "",
        "Family History": "",
        "Current or past disease": [],
        "Other": "",
        "Allergies and Dietary Restrictions": "",
        "Trigger foods": "",
        "Current Medication": "",
        "Other Information": "",
    }

if 'uploaded_text' not in st.session_state:
    st.session_state.uploaded_text = ""

if page == "Patient Entry & Upload":
    st.title(":hospital: Patient Entry & Document Upload")

    # Patient form inputs
    st.session_state.patient_history["Name"] = st.text_input(":bust_in_silhouette: Name", st.session_state.patient_history["Name"])
    st.session_state.patient_history["Age"] = st.number_input(":birthday: Age", min_value=2, max_value=100, value=st.session_state.patient_history["Age"])
    st.session_state.patient_history["Gender"] = st.selectbox(":restroom: Gender", ["Male", "Female", "Other"], index=["Male", "Female", "Other"].index(st.session_state.patient_history["Gender"]) if st.session_state.patient_history["Gender"] in ["Male", "Female", "Other"] else 0)
    st.session_state.patient_history["Height"] = st.text_input("Height (feet & inches): ", st.session_state.patient_history["Height"])
    st.session_state.patient_history["Weight"] = st.text_input("Weight (pounds): ", st.session_state.patient_history["Weight"])
    st.session_state.patient_history["Location"] = st.text_input("Location (for ingredient purchase purposes): ", st.session_state.patient_history["Location"])
    st.session_state.patient_history["Tobacco use"] = st.selectbox("Do you use tobacco?", ["Yes", "No", "I have before but quit"], index=["Yes", "No", "I have before but quit"].index(st.session_state.patient_history["Tobacco use"]) if st.session_state.patient_history["Tobacco use"] in ["Yes", "No", "I have before but quit"] else 0)
    st.session_state.patient_history["Family History"] = st.text_input("Enter any family diseases or diagnosis history here: ", st.session_state.patient_history["Family History"])
    st.session_state.patient_history["Current or past disease"] = st.multiselect("Select any of the diseases you may have",
        ["Hypertension(Anti-hypertensive agents)",
         "Coronary Artery Disease (Aspirin, Beta blockers, Statins)",
         "Congestive Heart Failure (Diuretics, Beta blockers, ACEi/ARB)",
         "Chronic Kidney disease (SGLT2 inhibitors) Dialysis",
         "Diabetes mellitus (Oral hypoglycemic medications/ insulin)",
         "Chronic Obstructive Pulmonary Disease (Steroids, Bronchodilators- Beta 2 Agonists & Muscarinic agonists)"],
         default=st.session_state.patient_history["Current or past disease"])
    st.session_state.patient_history["Other"] = st.text_input("Enter if you have any other diseases not listed: ", st.session_state.patient_history["Other"])
    st.session_state.patient_history["Allergies and Dietary Restrictions"] = st.text_input("Enter any allergies or dietary restrictions you may have: ", st.session_state.patient_history["Allergies and Dietary Restrictions"])
    st.session_state.patient_history["Trigger foods"] = st.text_input("Enter any foods that trigger your IBD: ", st.session_state.patient_history["Trigger foods"])
    st.session_state.patient_history["Current Medication"] = st.text_input("What medications are you currently taking: ", st.session_state.patient_history["Current Medication"])
    st.session_state.patient_history["Other Information"] = st.text_input("Please enter any other relevant information here: ", st.session_state.patient_history["Other Information"])

    # View collected data
    with st.expander("🔍 View Submitted Patient Info"):
        for key, value in st.session_state.patient_history.items():
            st.markdown(f"**{key}:** {value if value else '—'}")

    # File Upload
    st.markdown("---")
    st.subheader(":page_facing_up: Upload Blood Report Here")
    uploaded_file = st.file_uploader("Choose a file", type=['pdf'])

    if uploaded_file is not None:
        file_type = uploaded_file.type
        if "pdf" in file_type:
            st.subheader(":page_with_curl: PDF Content:")
            try:
                with pdfplumber.open(uploaded_file) as pdf:
                    all_text = ""
                    all_tables = []
                    for page_num, page in enumerate(pdf.pages):
                        page_text = page.extract_text()
                        if page_text:
                            all_text += f"Page {page_num + 1}:\n{page_text}\n\n"
                        tables = page.extract_tables()
                        for table in tables:
                            if table:
                                df = pd.DataFrame(table[1:], columns=table[0])
                                all_tables.append(df)
                    st.subheader(":memo: Extracted Text:")
                    st.text(all_text)
                    st.session_state.uploaded_text = all_text
                    if all_tables:
                        st.subheader(":bar_chart: Extracted Tables:")
                        for i, table in enumerate(all_tables):
                            st.write(f"Table {i + 1}:")
                            st.dataframe(table)
                    else:
                        st.warning("No tables found in the PDF.")
            except Exception as e:
                st.error(f":warning: Could not read the PDF. Error: {e}")
        elif "image" in file_type:
            st.subheader(":frame_with_picture: Image Preview:")
            try:
                img = Image.open(uploaded_file)
                st.image(img, caption="Uploaded Image", use_column_width=True)
                text = pytesseract.image_to_string(img)
                st.subheader(":memo: Extracted Text:")
                st.text(text)
                st.session_state.uploaded_text = text
            except Exception as e:
                st.error(f":warning: Could not process the image. Error: {e}")
    else:
        st.warning("No file uploaded yet.")

    st.markdown("---")
    st.caption("Built with :heart: using Streamlit")

if page == "AI Chat":
    st.title("💬 AI Chat Assistant")
    
    if "messages" not in st.session_state:
        st.session_state.messages = []

    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    if prompt := st.chat_input("Type your message here..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            # Create context with patient info
            patient_context = "\n".join(
                f"{key}: {value}" for key, value in st.session_state.patient_history.items() if value)
            full_context = patient_context + st.session_state.uploaded_text
            
            # Create chat prompt with context
            chat_prompt = f"""
            You are a medical assistant. Here is the patient information:
            {full_context}
            
            Previous conversation:
            {[msg['content'] for msg in st.session_state.messages[:-1]]}
            
            User question: {prompt}
            
            Please provide a helpful response based on the patient's information.
            Stay friendly and match the tone of the user. Make sure to reference the patient's details where relevant.
            Make sure to format your response in markdown for better readability. Make sure to keep the topic on track.
            Avoid making a diagnosis or using overly technical terms. Respond as a knowledgeable but approachable assistant.
            Provide concise and clear answers, breaking down complex information into simple terms.
            """
            
            with st.spinner("Thinking..."):
                try:
                    response = model.generate_content(chat_prompt)
                    ai_response = response.text
                    st.markdown(ai_response)
                    st.session_state.messages.append({"role": "assistant", "content": ai_response})
                except Exception as e:
                    st.error(f"Error: {e}")

# ------------------ PAGE 2 ------------------
elif page == "AI Analysis":
    st.title("🧠 AI Analysis Assistant")
    ai_section = st.sidebar.radio("AI Analysis Sections", ["Diet Plan", "Medicine Schedule", "Blood Analysis Report"])

    st.markdown("Ask questions based on the submitted patient information below.")
    with st.expander("🔍 View Submitted Patient Info"):
        for key, value in st.session_state.patient_history.items():
            st.markdown(f"**{key}:** {value if value else '—'}")

    # Generate prompt
    patient_context = "\n".join(
        f"{key}: {value}" for key, value in st.session_state.patient_history.items() if value)

    full_context = patient_context + "\n" + st.session_state.uploaded_text

    prompt = f"""  
You are a medically informed assistant. Based on the patient information below, provide a clear and helpful response structured with these exact markdown section titles:
## Diet Plan
## Medication & Supplement Schedule
## Blood Analysis Report

Only use these exact headings. Do not use different symbols or formats.

Patient Info:
{full_context}

Details:
- Diet Plan: Based on diseases, allergies, goals, create a diet plan that will benefit the patient and allow them to be pain free. Use data from blood report to factor into plan. Give
tham actual products and meals that they can have for breakfast, lunch, and dinner. Plan out their meals for the next week, give options for meal prepped meals and freshly made meals. 
give them ingredients they can purchase in stores based on the location inputted. Work around the medication schedule if there.
- Medication Schedule: suggest medications based on patient medical data and create a schedule based on when they are supposed to take medication. Suggest any vitamins
they may need.
- Blood Analysis Report: If any lab data is included, interpret simply. Input information from the blood analysis report to create a more cohesive diet plan
Avoid making a diagnosis or using overly technical terms. Factor the blood analysis report into the diet plan and medication schedule.
"""

    # Generate AI response if not already present
    if 'ai_response' not in st.session_state:
        with st.spinner("Analyzing patient info..."):
            try:
                response = model.generate_content(prompt)
                st.session_state.ai_response = response.text
                st.success("Analysis complete!")
            except Exception as e:
                st.error(f"Gemini API Error: {e}")
                st.stop()

    # Optional: regenerate
    if st.button("🔁 Regenerate AI Analysis"):
        st.session_state.pop('ai_response', None)
        st.rerun()

    # Split and map AI response by headers
    sections = st.session_state.ai_response.split("## ")
    section_map = {}
    for section in sections:
        if section.strip():
            lines = section.strip().split("\n", 1)
            if len(lines) == 2:
                title, content = lines[0].strip(), lines[1].strip()
                section_map[title] = content

    # Show fallback if parsing failed
    if not section_map:
        st.warning("⚠️ Could not parse AI response properly. Showing raw output:")
        st.text(st.session_state.ai_response)

    # Show selected section
    if ai_section == "Diet Plan":
        st.subheader("🥗 Personalized Diet Plan")
        st.markdown(section_map.get("Diet Plan", "_No diet plan available._"))

    elif ai_section == "Medicine Schedule":
        st.subheader("💊 Medication & Supplement Schedule")
        st.markdown(section_map.get("Medication & Supplement Schedule", "_No medication schedule available._"))

    elif ai_section == "Blood Analysis Report":
        st.subheader("🧪 Blood Work Interpretation")
        st.markdown(section_map.get("Blood Analysis Report", "_No blood report data available._"))



