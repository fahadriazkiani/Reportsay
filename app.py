import streamlit as st
import google.generativeai as genai
from PIL import Image
import urllib.parse  # Used to create the free Maps links

# ==========================================
# 🔑 SETUP: PASTE YOUR API KEY BELOW
# ==========================================
GOOGLE_API_KEY = "AIzaSyAMQNqfsL2WfPuLbB5nSMlf5vf1v7KcxFI"
genai.configure(api_key=GOOGLE_API_KEY)

st.set_page_config(page_title="Reportsay", page_icon="🩺", layout="centered")

# Custom CSS for Professional Blue Branding
st.markdown("""
    <style>
    .main-title {font-family: 'Helvetica', sans-serif; font-size: 3rem; color: #007BFF; text-align: center; font-weight: 800; margin-bottom: 0px;}
    .sub-title {font-size: 1.2rem; color: #555; text-align: center; margin-bottom: 2rem;}
    .report-box {border: 2px solid #007BFF; padding: 20px; border-radius: 10px; background-color: #f0f8ff; color: #333;}
    </style>
""", unsafe_allow_html=True)

# Sidebar for Model Selection
st.sidebar.header("⚙️ Settings")
try:
    model_list = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
    selected_model_name = st.sidebar.selectbox("Select AI Model:", model_list, index=0)
    model = genai.GenerativeModel(selected_model_name)
    st.sidebar.success(f"Connected to: {selected_model_name}")
except:
    model = genai.GenerativeModel('gemini-1.5-flash')

# ==========================================
# 🚀 APP INTERFACE
# ==========================================
st.markdown('<div class="main-title">Reportsay 🩺</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-title">Your Personal AI Medical Assistant</div>', unsafe_allow_html=True)

tab1, tab2 = st.tabs(["📝 Interpret Report", "💰 Compare Prices (Lahore)"])

# --- TAB 1: AI INTERPRETER ---
with tab1:
    st.write("### Upload a Lab Report")
    uploaded_file = st.file_uploader("Choose an image...", type=["jpg", "jpeg", "png"])
    if uploaded_file is not None:
        image = Image.open(uploaded_file)
        st.image(image, caption='Uploaded Report', use_container_width=True)
        if st.button("🔍 Analyze with Reportsay"):
            if "PASTE_YOUR_KEY" in GOOGLE_API_KEY:
                st.error("⚠️ Please paste your API Key!")
            else:
                with st.spinner('Analyzing...'):
                    try:
                        prompt = "Analyze this report. Use 🔴 for High/Low and ✅ for Normal. Explain abnormalities simply. Disclaimer: AI only."
                        response = model.generate_content([prompt, image])
                        st.markdown(f'<div class="report-box">{response.text}</div>', unsafe_allow_html=True)
                    except Exception as e:
                        st.error(f"Error: {e}")

# --- TAB 2: PRICE CHECKER (WITH FREE MAPS LINKS) ---
with tab2:
    st.write("### 🏥 Compare Lab Rates in Lahore")
    test_name = st.selectbox("Select a Test:", 
                             ["CBC (Complete Blood Count)", "LFT (Liver Function)", "RFT/KFT (Kidney Function)", 
                              "Lipid Profile", "Cardiac Profile", "HbA1c (Diabetes)", "Thyroid Profile", "Vitamin D"])
    
    if st.button("Check Prices"):
        st.write(f"Showing estimated rates for: **{test_name}**")
        
        # Data including Lab name and estimated prices
        labs_data = [
            {"Lab": "Mughal Labs", "Price": "Rs. 750", "Location": "Mughal Labs Lahore"},
            {"Lab": "Excel Labs", "Price": "Rs. 800", "Location": "Excel Labs Lahore"},
            {"Lab": "Shaukat Khanum", "Price": "Rs. 850", "Location": "Shaukat Khanum Laboratory Lahore"},
            {"Lab": "IDC", "Price": "Rs. 900", "Location": "Islamabad Diagnostic Centre Lahore"},
            {"Lab": "Chughtai Lab", "Price": "Rs. 950", "Location": "Chughtai Lab Lahore"}
        ]
        
        # Display as custom "cards" with a Google Maps button for each
        for item in labs_data:
            col1, col2, col3 = st.columns([2, 1, 1])
            with col1:
                st.write(f"**{item['Lab']}**")
            with col2:
                st.write(item['Price'])
            with col3:
                # Create the free Google Maps URL
                query = urllib.parse.quote(item['Location'])
                maps_url = f"https://www.google.com/maps/search/?api=1&query={query}"
                st.link_button("📍 Find", maps_url)
            st.divider()