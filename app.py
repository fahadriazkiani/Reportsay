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

# --- 1. CONFIGURATION ---
st.set_page_config(
    page_title="ReportSay - AI Medical Assistant", 
    page_icon="https://i.postimg.cc/VLmw1MPY/logo.png", 
    layout="wide"
)

# --- 2. PROFESSIONAL DESIGN SYSTEM (CSS) ---
st.markdown("""
    <style>
    /* Global Background */
    .main { background-color: #f4f6f9; }
    
    /* Hide Default Streamlit Elements */
    header {visibility: hidden;}
    .block-container { padding-top: 2rem; } /* Reduce top whitespace */

    /* --- HERO HEADER (Flexbox for perfect alignment) --- */
    .hero-container {
        display: flex;
        align-items: center;
        justify-content: center;
        background-color: #ffffff;
        padding: 2rem;
        border-radius: 15px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.05);
        margin-bottom: 30px;
    }
    
    .hero-logo {
        width: 100px; /* Increased size */
        height: auto;
        margin-right: 20px;
    }
    
    .hero-text-col {
        display: flex;
        flex-direction: column;
    }
    
    .hero-title {
        font-size: 3.5rem;
        font-weight: 800;
        color: #007BFF;
        line-height: 1.1;
        margin: 0;
        font-family: 'Helvetica Neue', sans-serif;
    }
    
    .hero-subtitle {
        font-size: 1.2rem;
        color: #666;
        margin: 5px 0 0 0;
        font-weight: 400;
    }

    /* --- INPUT CARDS (Upload & Language) --- */
    /* This makes the upload and select box look like panels */
    .css-1r6slb0, .css-12oz5g7 { /* Target Streamlit containers */
        background-color: white;
        padding: 20px;
        border-radius: 12px;
        box-shadow: 0 2px 5px rgba(0,0,0,0.05);
        border: 1px solid #e1e4e8;
    }

    /* --- PRICE CARDS (Al-Noor Style) --- */
    .lab-card {
        background-color: #ffffff;
        border-radius: 12px;
        padding: 20px;
        margin-bottom: 15px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.05);
        border: 1px solid #e1e4e8;
        text-align: center;
        transition: transform 0.2s, box-shadow 0.2s;
        height: 220px;
        display: flex;
        flex-direction: column;
        justify-content: space-between;
    }
    
    .lab-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 10px 20px rgba(0,123,255,0.15);
        border-color: #007BFF;
    }

    .lab-name {
        font-size: 1.1rem;
        font-weight: 700;
        color: #333;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        margin-bottom: 10px;
        border-bottom: 2px solid #f0f2f5;
        padding-bottom: 10px;
    }

    .lab-price {
        font-size: 2rem;
        font-weight: 800;
        color: #28a745;
        margin: 10px 0;
    }
    
    .lab-price-missing {
        font-size: 1.2rem;
        color: #dc3545;
        font-style: italic;
        margin: 15px 0;
    }

    .lab-btn {
        display: block;
        width: 100%;
        padding: 10px 0;
        background-color: #007BFF;
        color: white !important;
        text-decoration: none;
        border-radius: 8px;
        font-weight: 600;
        transition: background-color 0.2s;
        text-align: center;
    }
    .lab-btn:hover { background-color: #0056b3; }

    /* AI Report Box */
    .report-box { 
        background-color: #ffffff; 
        padding: 25px; 
        border-radius: 12px; 
        border-left: 5px solid #007BFF; 
        box-shadow: 0 5px 15px rgba(0,0,0,0.05); 
        margin-top: 20px;
    }
    
    /* Styled Headers for Sections */
    .section-header {
        font-size: 1.5rem;
        font-weight: 700;
        color: #444;
        margin-bottom: 15px;
        display: flex;
        align-items: center;
        gap: 10px;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 3. API SETUP ---
if "MY_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["MY_API_KEY"])
else:
    st.error("⚠️ API Key missing! Please check Streamlit Secrets.")

# --- 4. HERO HEADER (HTML) ---
# This replaces the old header with a properly aligned Flexbox structure
st.markdown("""
    <div class="hero-container">
        <img src="https://i.postimg.cc/VLmw1MPY/logo.png" class="hero-logo">
        <div class="hero-text-col">
            <h1 class="hero-title">Reportsay</h1>
            <p class="hero-subtitle">Advanced AI Analysis & Price Transparency</p>
        </div>
    </div>
    """, unsafe_allow_html=True)

# --- 5. FUNCTIONS ---
def get_auto_model():
    """Finds best available Gemini model automatically."""
    try:
        all_models = [m for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        for m in all_models:
            if 'flash' in m.name: return genai.GenerativeModel(m.name)
        for m in all_models:
            if '1.5-pro' in m.name: return genai.GenerativeModel(m.name)
        if all_models: return genai.GenerativeModel(all_models[0].name)
        return None
    except: return None

def clean_text_for_pdf(text):
    text = re.sub(r'\*\*|__', '', text)
    text = re.sub(r'\*|_', '', text)
    text = re.sub(r'^#+\s+', '', text, flags=re.MULTILINE)
    return text

# --- 6. NAVIGATION ---
tab1, tab2 = st.tabs(["📄 AI Report Analysis", "💰 Smart Price Checker"])

# ==========================================
# TAB 1: AI REPORT ANALYSIS (Redesigned)
# ==========================================
with tab1:
    # Creating a visual "Card" effect by using containers
    col1, col2 = st.columns([1, 1], gap="medium")
    
    with col1:
        st.markdown('<div class="section-header">📤 Upload Report</div>', unsafe_allow_html=True)
        # We wrap this in a container to visually separate it
        with st.container():
            uploaded_file = st.file_uploader("Upload Image or PDF", type=['png', 'jpg', 'jpeg', 'pdf'])
            if not uploaded_file:
                st.info("Supported formats: PNG, JPG, PDF (Max 200MB)")

    with col2:
        st.markdown('<div class="section-header">🌐 Language</div>', unsafe_allow_html=True)
        with st.container():
            language = st.selectbox("Select Interpretation Language", ["English", "Urdu (اردو)"])
            st.caption("AI will translate complex medical terms into your chosen language.")

    if uploaded_file:
        st.markdown("---")
        try:
            image = Image.open(uploaded_file)
            col_img1, col_img2, col_img3 = st.columns([1, 2, 1])
            with col_img2:
                # Image Preview Card
                st.markdown('<div style="background: white; padding: 15px; border-radius: 12px; border: 1px solid #ddd; box-shadow: 0 4px 6px rgba(0,0,0,0.05);">', unsafe_allow_html=True)
                st.image(image, caption="Uploaded Document Preview", use_container_width=True)
                st.markdown('</div>', unsafe_allow_html=True)
            
            st.write("")
            # Big Action Button
            if st.button("✨ Analyze Report Now", use_container_width=True, type="primary"):
                with st.spinner("🤖 AI is analyzing your report..."):
                    model = get_auto_model()
                    if model:
                        try:
                            prompt = (
                                f"You are a medical lab expert. Analyze this report in {language}. "
                                "1. Summarize findings.\n2. Highlight abnormalities.\n3. Disclaimer: Consult a doctor."
                            )
                            response = model.generate_content([prompt, image])
                            
                            # Result Card
                            st.markdown(f"""<div class="report-box"><h3>📝 AI Analysis Result</h3>{response.text}</div>""", unsafe_allow_html=True)
                            
                            # PDF Logic
                            pdf = FPDF()
                            pdf.add_page()
                            try:
                                img_resp = requests.get("https://i.postimg.cc/VLmw1MPY/logo.png")
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
                            clean_txt = clean_text_for_pdf(response.text)
                            pdf.multi_cell(0, 7, txt=clean_txt.encode('latin-1', 'replace').decode('latin-1'))
                            
                            pdf_output = pdf.output(dest='S').encode('latin-1')
                            st.download_button("📥 Download Official Report (PDF)", pdf_output, "ReportSay_Analysis.pdf", "application/pdf", use_container_width=True)
                            
                        except Exception as e:
                             st.warning("🚦 Traffic Limit. Please wait 30 seconds." if "429" in str(e) else f"AI Error: {e}")
                    else:
                        st.error("No AI models found. Reboot app.")
        except Exception as e:
            st.error(f"Error processing file: {e}")

# ==========================================
# TAB 2: SMART PRICE CHECKER (Unchanged & Beautiful)
# ==========================================
with tab2:
    st.markdown("### 🏥 Compare Lab Rates in Lahore")
    st.caption("Live prices from verified lab panels.")

    LAB_LOCATIONS = {
        "Mughal Labs": "https://maps.app.goo.gl/MughalLabsLahore",
        "Shaukat Khanum": "https://maps.app.goo.gl/SKMLahore",
        "IDC": "https://maps.app.goo.gl/IDCLahore",
        "Chughtai Lab": "https://maps.app.goo.gl/ChughtaiLahore",
        "Al-Noor": "https://maps.app.goo.gl/AlNoorLahore"
    }

    COMMON_TESTS = ["Select a test...", "CBC", "HbA1c", "Glucose Profile", "Lipid Profile", "LFTs", "RFTs", "Cardiac Profile", "Thyroid Profile", "Vitamins"]

    json_path = 'data/lab_prices.json'
    
    if os.path.exists(json_path):
        try:
            with open(json_path, 'r') as f:
                lab_data = json.load(f)
            
            selected_test = st.selectbox("Select a Commonly Prescribed Test:", options=COMMON_TESTS)
            
            if selected_test and selected_test != "Select a test...":
                st.markdown(f"#### 💰 Prices for: **{selected_test}**")
                cols = st.columns(3)
                
                for idx, (lab_name, tests) in enumerate(lab_data.items()):
                    with cols[idx % 3]:
                        price = tests.get(selected_test)
                        if not price:
                            for k, v in tests.items():
                                if selected_test.lower() in k.lower() and len(k) < 30:
                                    price = v
                                    break
                        
                        if price:
                            price_display = f'<div class="lab-price">Rs. {price}</div>'
                        else:
                            price_display = '<div class="lab-price-missing">Check Lab</div>'
                        
                        map_link = LAB_LOCATIONS.get(lab_name, "https://maps.google.com")

                        card_html = f"""
                        <div class="lab-card">
                            <div class="lab-name">{lab_name}</div>
                            {price_display}
                            <a href="{map_link}" target="_blank" class="lab-btn">📍 Get Directions</a>
                        </div>
                        """
                        st.markdown(card_html, unsafe_allow_html=True)
            
            mtime = os.path.getmtime(json_path)
            dt = datetime.datetime.fromtimestamp(mtime).strftime("%Y-%m-%d %H:%M")
            st.caption(f"Last updated: {dt}")
            
        except Exception as e:
            st.error(f"Data Error: {e}")
    else:
        st.warning("⚠️ Database is updating. Please run the 'Daily Lab Price Update' workflow on GitHub.")
