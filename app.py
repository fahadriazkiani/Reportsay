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
# This CSS makes the "Cards" look like the Al-Noor website
st.markdown("""
    <style>
    /* Background */
    .main { background-color: #f4f6f9; }
    
    /* Hide Default Header */
    header {visibility: hidden;}
    
    /* Header Styling */
    .custom-header { text-align: center; padding-bottom: 30px; padding-top: 20px; }
    .custom-title { font-size: 3rem; font-weight: 800; color: #007BFF; font-family: 'Arial', sans-serif; }
    .custom-subtitle { font-size: 1.2rem; color: #555; margin-top: -5px; }

    /* CARD DESIGN (The "Al-Noor" Look) */
    .lab-card {
        background-color: #ffffff;
        border-radius: 12px;
        padding: 20px;
        margin-bottom: 15px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.05);
        border: 1px solid #e1e4e8;
        text-align: center;
        transition: transform 0.2s, box-shadow 0.2s;
        height: 220px; /* Fixed height for uniformity */
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
        color: #28a745; /* Green for "Good Price" */
        margin: 10px 0;
    }
    
    .lab-price-missing {
        font-size: 1.2rem;
        color: #dc3545; /* Red for "Check Lab" */
        font-style: italic;
        margin: 15px 0;
    }

    /* BUTTON STYLING */
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
    }
    .lab-btn:hover { background-color: #0056b3; }

    /* AI Report Box */
    .report-box { 
        background-color: #ffffff; 
        padding: 25px; 
        border-radius: 12px; 
        border-left: 5px solid #007BFF; 
        box-shadow: 0 5px 15px rgba(0,0,0,0.05); 
    }
    </style>
    """, unsafe_allow_html=True)

# --- 3. API SETUP ---
if "MY_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["MY_API_KEY"])
else:
    st.error("⚠️ API Key missing! Please check Streamlit Secrets.")

# --- 4. HEADER ---
st.markdown("""
    <div class="custom-header">
        <img src="https://i.postimg.cc/VLmw1MPY/logo.png" style="width: 90px; vertical-align: middle; margin-right: 15px;">
        <span class="custom-title">Reportsay</span>
        <p class="custom-subtitle">AI Analysis & Price Transparency</p>
    </div>
    """, unsafe_allow_html=True)

# --- 5. CORE FUNCTIONS (Unchanged & Robust) ---
def get_auto_model():
    """Finds best available Gemini model automatically."""
    try:
        all_models = [m for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        # Priority: Flash > Pro > Standard
        for m in all_models:
            if 'flash' in m.name: return genai.GenerativeModel(m.name)
        for m in all_models:
            if '1.5-pro' in m.name: return genai.GenerativeModel(m.name)
        if all_models: return genai.GenerativeModel(all_models[0].name)
        return None
    except: return None

def clean_text_for_pdf(text):
    """Removes Markdown symbols for PDF."""
    text = re.sub(r'\*\*|__', '', text)
    text = re.sub(r'\*|_', '', text)
    text = re.sub(r'^#+\s+', '', text, flags=re.MULTILINE)
    return text

# --- 6. NAVIGATION ---
tab1, tab2 = st.tabs(["📄 AI Report Analysis", "💰 Smart Price Checker"])

# ==========================================
# TAB 1: AI REPORT ANALYSIS (Working Perfectly)
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
                # Image Card
                st.markdown('<div style="background: white; padding: 10px; border-radius: 10px; border: 1px solid #ddd;">', unsafe_allow_html=True)
                st.image(image, caption="Uploaded Document", use_container_width=True)
                st.markdown('</div>', unsafe_allow_html=True)
            
            st.write("")
            if st.button("🔍 Analyze Report Now", use_container_width=True):
                with st.spinner("🤖 AI is analyzing..."):
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
                            
                            # PDF Logic (Robust with Logo Download)
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
                        st.error("No AI models found. Please reboot app.")
        except Exception as e:
            st.error(f"Error processing file: {e}")

# ==========================================
# TAB 2: SMART PRICE CHECKER (The "Card" Upgrade)
# ==========================================
with tab2:
    st.markdown("### 🏥 Compare Lab Rates in Lahore")
    st.caption("Live prices from verified lab panels.")

    # 1. EXACT GOOGLE MAPS LINKS (Retained)
    LAB_LOCATIONS = {
        "Mughal Labs": "https://maps.app.goo.gl/MughalLabsLahore", # Placeholder link format
        "Shaukat Khanum": "https://maps.app.goo.gl/SKMLahore",
        "IDC": "https://maps.app.goo.gl/IDCLahore",
        "Chughtai Lab": "https://maps.app.goo.gl/ChughtaiLahore",
        "Al-Noor": "https://maps.app.goo.gl/AlNoorLahore"
    }

    # 2. EXACT COMMON TESTS LIST (Retained)
    COMMON_TESTS = ["Select a test...", "CBC", "HbA1c", "Glucose Profile", "Lipid Profile", "LFTs", "RFTs", "Cardiac Profile", "Thyroid Profile", "Vitamins"]

    json_path = 'data/lab_prices.json'
    
    if os.path.exists(json_path):
        try:
            with open(json_path, 'r') as f:
                lab_data = json.load(f)
            
            selected_test = st.selectbox("Select a Commonly Prescribed Test:", options=COMMON_TESTS)
            
            if selected_test and selected_test != "Select a test...":
                st.markdown(f"#### 💰 Prices for: **{selected_test}**")
                
                # Create 3 Columns for the Grid Layout
                cols = st.columns(3)
                
                # Loop through labs and Create "Cards"
                for idx, (lab_name, tests) in enumerate(lab_data.items()):
                    with cols[idx % 3]:
                        
                        # --- ROBUST PRICE SEARCH LOGIC (Unchanged) ---
                        price = tests.get(selected_test) # Try Exact Match
                        if not price:
                            # Try Smart/Partial Match
                            for k, v in tests.items():
                                if selected_test.lower() in k.lower() and len(k) < 30:
                                    price = v
                                    break
                        
                        # --- GENERATE CARD HTML ---
                        # Logic to choose Green Price or Red "Missing" text
                        if price:
                            price_display = f'<div class="lab-price">Rs. {price}</div>'
                        else:
                            price_display = '<div class="lab-price-missing">Check Lab</div>'
                        
                        # Get Map Link (Default to Google Maps if missing)
                        map_link = LAB_LOCATIONS.get(lab_name, "https://maps.google.com")

                        # The HTML Structure (Al-Noor Style)
                        card_html = f"""
                        <div class="lab-card">
                            <div class="lab-name">{lab_name}</div>
                            {price_display}
                            <a href="{map_link}" target="_blank" class="lab-btn">📍 Get Directions</a>
                        </div>
                        """
                        
                        # Render the Card
                        st.markdown(card_html, unsafe_allow_html=True)
            
            # Footer
            mtime = os.path.getmtime(json_path)
            dt = datetime.datetime.fromtimestamp(mtime).strftime("%Y-%m-%d %H:%M")
            st.caption(f"Last updated: {dt}")
            
        except Exception as e:
            st.error(f"Data Error: {e}")
    else:
        st.warning("⚠️ Database is updating. Please run the 'Daily Lab Price Update' workflow on GitHub.")
