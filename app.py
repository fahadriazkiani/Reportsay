import streamlit as st
import google.generativeai as genai
from PIL import Image
import json
import os
import datetime
from fpdf import FPDF
import requests
import tempfile
import re

# --- 1. PAGE CONFIGURATION ---
st.set_page_config(
    page_title="ReportSay - AI Medical Assistant", 
    page_icon="https://i.postimg.cc/VLmw1MPY/logo.png", 
    layout="wide"
)

# --- 2. CUSTOM CSS (Blue Theme) ---
st.markdown("""
    <style>
    .main { background-color: #f8f9fa; }
    header {visibility: hidden;}
    .custom-header { text-align: center; padding-bottom: 30px; }
    .custom-title { font-size: 4rem; font-weight: 800; color: #007BFF; font-family: 'Helvetica Neue', sans-serif; }
    .custom-subtitle { font-size: 1.3rem; color: #555; margin-top: -10px; }
    .stButton>button { background-color: #007BFF; color: white; border-radius: 8px; height: 3em; font-weight: bold; border: none; }
    .stButton>button:hover { background-color: #0056b3; }
    .report-box { background-color: #ffffff; padding: 25px; border-radius: 12px; border-left: 6px solid #007BFF; box-shadow: 0 4px 15px rgba(0,0,0,0.1); }
    </style>
    """, unsafe_allow_html=True)

# --- 3. SECURE API SETUP ---
if "MY_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["MY_API_KEY"])
else:
    st.error("⚠️ API Key missing! Please check Streamlit Secrets.")

# --- 4. HEADER ---
st.markdown("""
    <div class="custom-header">
        <img src="https://i.postimg.cc/VLmw1MPY/logo.png" style="width: 100px; vertical-align: middle; margin-right: 15px;">
        <span class="custom-title">Reportsay</span>
        <p class="custom-subtitle">Your Personal AI Medical Assistant</p>
    </div>
    """, unsafe_allow_html=True)

# --- 5. SAFE MODEL SELECTOR ---
def get_safe_model():
    try:
        priority_models = ["gemini-1.5-flash", "gemini-1.5-pro", "gemini-pro-vision"]
        available = [m.name for m in genai.list_models()]
        for p in priority_models:
            for a in available:
                if p in a: return genai.GenerativeModel(a)
        return genai.GenerativeModel('gemini-pro-vision')
    except: return genai.GenerativeModel('gemini-1.5-flash')

# --- 6. TEXT CLEANER FOR PDF (THE FIX) ---
def clean_text_for_pdf(text):
    """
    Removes Markdown symbols like **bold** and ## headers
    so the PDF looks professional and clean.
    """
    # Remove bold/italic markers (* or _)
    text = re.sub(r'\*\*|__', '', text)
    text = re.sub(r'\*|_', '', text)
    # Remove hash headers (### Title)
    text = re.sub(r'^#+\s+', '', text, flags=re.MULTILINE)
    return text

# --- 7. TABS ---
tab1, tab2 = st.tabs(["📄 AI Report Analysis", "💰 Smart Price Checker (Lahore)"])

# ==========================================
# TAB 1: AI REPORT ANALYSIS
# ==========================================
with tab1:
    col1, col2 = st.columns([1, 1])
    with col1:
        st.markdown("### 📤 Upload Report")
        uploaded_file = st.file_uploader("Upload Image or PDF", type=['png', 'jpg', 'jpeg', 'pdf'])
    with col2:
        st.markdown("### 🌐 Preferences")
        language = st.selectbox("Interpretation Language", ["English", "Urdu (اردو)"])

    if uploaded_file:
        st.markdown("---")
        try:
            image = Image.open(uploaded_file)
            col_img1, col_img2, col_img3 = st.columns([1, 2, 1])
            with col_img2:
                st.image(image, caption="Uploaded Document", use_container_width=True)
            
            if st.button("🔍 Analyze Report Now"):
                with st.spinner("🤖 AI is thinking..."):
                    model = get_safe_model()
                    try:
                        prompt = (
                            f"You are a medical lab expert. Analyze this report in {language}. "
                            "1. Summarize findings.\n2. Highlight abnormalities.\n3. Disclaimer: Consult a doctor."
                        )
                        response = model.generate_content([prompt, image])
                        
                        # Display (Markdown is GOOD here)
                        st.markdown(f"""<div class="report-box"><h3>📝 AI Analysis Result</h3>{response.text}</div>""", unsafe_allow_html=True)
                        
                        # PDF Logic
                        pdf = FPDF()
                        pdf.add_page()
                        
                        # Add Logo
                        logo_url = "https://i.postimg.cc/VLmw1MPY/logo.png"
                        try:
                            img_resp = requests.get(logo_url)
                            if img_resp.status_code == 200:
                                with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmp_file:
                                    tmp_file.write(img_resp.content)
                                    tmp_logo_path = tmp_file.name
                                pdf.image(tmp_logo_path, x=10, y=8, w=30)
                        except: pass

                        pdf.set_xy(10, 40)
                        pdf.set_font("Arial", 'B', 16)
                        pdf.cell(0, 10, txt="ReportSay Analysis", ln=True, align='C')
                        pdf.ln(5)
                        
                        pdf.set_font("Arial", size=11)
                        
                        # --- CLEAN TEXT BEFORE WRITING TO PDF ---
                        raw_text = response.text
                        polished_text = clean_text_for_pdf(raw_text)
                        
                        # Handle encoding (important for symbols)
                        final_pdf_text = polished_text.encode('latin-1', 'replace').decode('latin-1')
                        pdf.multi_cell(0, 7, txt=final_pdf_text)
                        
                        pdf.ln(10)
                        pdf.set_font("Arial", 'I', 8)
                        pdf.cell(0, 10, txt="Generated by ReportSay AI. Not a medical diagnosis.", align='C')
                        
                        pdf_output = pdf.output(dest='S').encode('latin-1')
                        st.download_button("📥 Download Official Report (PDF)", pdf_output, "ReportSay_Analysis.pdf", "application/pdf")
                        
                    except Exception as e:
                        if "429" in str(e):
                            st.warning("🚦 Traffic Limit. Please wait 30 seconds.")
                        else:
                            st.error(f"AI Error: {e}")

        except Exception as e:
            st.error(f"Error processing file: {e}")

# ==========================================
# TAB 2: SMART PRICE CHECKER
# ==========================================
with tab2:
    st.markdown("### 🏥 Compare Lab Rates in Lahore")
    st.caption("Live prices from Mughal, SKM, Al-Noor, IDC, and Chughtai.")

    json_path = 'data/lab_prices.json'
    
    if os.path.exists(json_path):
        try:
            with open(json_path, 'r') as f:
                lab_data = json.load(f)
            
            all_tests = set()
            for tests in lab_data.values():
                for k in tests.keys():
                    clean_k = k.replace(',', '').replace('.', '').strip()
                    if not clean_k.isdigit() and len(clean_k) > 1:
                        all_tests.add(k)
            
            selected_test = st.selectbox(
                "Select a Commonly Prescribed Test:",
                options=[""] + sorted(list(all_tests)),
                format_func=lambda x: "Type to search..." if x == "" else x
            )
            
            if selected_test:
                st.markdown(f"#### 💰 Price Comparison: **{selected_test}**")
                cols = st.columns(3)
                found = False
                for idx, (lab_name, tests) in enumerate(lab_data.items()):
                    with cols[idx % 3]:
                        st.markdown(f"**{lab_name}**")
                        price = tests.get(selected_test)
                        if not price:
                            for k, v in tests.items():
                                if selected_test.lower() in k.lower() and not k.replace(',','').isdigit():
                                    price = v
                                    break
                        if price:
                            st.success(f"Rs. {price}")
                            found = True
                        else:
                            st.info("Check Lab")
                if not found:
                    st.warning("Price not available in current database.")
            
            mtime = os.path.getmtime(json_path)
            dt = datetime.datetime.fromtimestamp(mtime).strftime("%Y-%m-%d %H:%M")
            st.caption(f"Last updated: {dt}")
        except Exception as e:
            st.error(f"Data Error: {e}")
    else:
        st.warning("⚠️ Database is updating. Please run the 'Daily Lab Price Update' workflow on GitHub.")
