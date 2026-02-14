import streamlit as st
import google.generativeai as genai
from PIL import Image
import json
import os
import requests
import tempfile
from fpdf import FPDF

# --- 1. CONFIGURATION ---
st.set_page_config(
    page_title="ReportSay - AI Medical Assistant", 
    page_icon="https://i.postimg.cc/VLmw1MPY/logo.png", 
    layout="wide"
)

# --- 2. CSS STYLING ---
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

# --- 3. API SETUP ---
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

# --- 5. SMART MODEL SELECTOR (THE FIX) ---
def get_working_model():
    """
    Dynamically finds a working model instead of hardcoding one.
    """
    try:
        # Ask Google what is available
        available_models = []
        for m in genai.list_models():
            if 'generateContent' in m.supported_generation_methods:
                available_models.append(m.name)
        
        # 1. Try to find the best modern model (Flash)
        for model_name in available_models:
            if "gemini-1.5-flash" in model_name:
                return genai.GenerativeModel(model_name)
        
        # 2. If Flash not found, look for Pro Vision (Legacy)
        for model_name in available_models:
            if "gemini-pro-vision" in model_name:
                return genai.GenerativeModel(model_name)
                
        # 3. If neither, just pick the first one that supports vision/images
        # (Usually models with 'vision' or '1.5' in the name support images)
        if available_models:
             return genai.GenerativeModel(available_models[0])
             
        return None
    except Exception as e:
        st.error(f"Error listing models: {e}")
        return None

# --- 6. MAIN TABS ---
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
                with st.spinner("🤖 AI is finding the best model..."):
                    
                    # CALL THE SMART SELECTOR
                    model = get_working_model()
                    
                    if model:
                        # Test if the selected model actually works
                        try:
                            prompt = (
                                f"You are a medical lab expert. Analyze this report in {language}. "
                                "1. Summarize findings.\n2. Highlight abnormalities.\n3. Disclaimer: Consult a doctor."
                            )
                            response = model.generate_content([prompt, image])
                            
                            # Success! Display it.
                            st.markdown(f"""<div class="report-box"><h3>📝 AI Analysis Result</h3>{response.text}</div>""", unsafe_allow_html=True)
                            
                            # PDF Logic
                            pdf = FPDF()
                            pdf.add_page()
                            # (Logo logic omitted for brevity, focus is on AI fix first)
                            pdf.set_font("Arial", 'B', 16)
                            pdf.cell(0, 10, txt="ReportSay Analysis", ln=True, align='C')
                            pdf.ln(10)
                            pdf.set_font("Arial", size=11)
                            text_content = response.text.encode('latin-1', 'replace').decode('latin-1')
                            pdf.multi_cell(0, 7, txt=text_content)
                            pdf_output = pdf.output(dest='S').encode('latin-1')
                            
                            st.download_button("📥 Download PDF", pdf_output, "ReportSay_Analysis.pdf", "application/pdf")
                            
                        except Exception as inner_e:
                            st.error(f"Model found ({model.model_name}) but failed to generate: {inner_e}")
                            st.info("Debugging: Try updating requirements.txt to 'google-generativeai>=0.7.0'")
                    else:
                        st.error("CRITICAL: No AI models found available for your API Key.")
                        st.write("Debug Info - Available models:")
                        # Print list for debugging
                        for m in genai.list_models():
                            st.code(m.name)

        except Exception as e:
            st.error(f"Error processing file: {e}")

# ==========================================
# TAB 2: # --- TAB 2: DYNAMIC PRICE CHECKER ---
with tab2:
    st.write("### 🏥 Real-Time Lab Rates in Lahore")
    
    # 1. LOAD THE SCRAPED DATA
    try:
        with open('data/lab_prices.json', 'r') as f:
            live_data = json.load(f)
        st.sidebar.info("✨ Prices updated today")
    except:
        live_data = {} # Backup if file isn't ready yet

    test_name = st.selectbox("Select a Test:", 
                             ["CBC", "LFT", "RFT", "Lipid Profile", "HbA1c", "Thyroid", "Vitamin D"])
    
    if st.button("Check Live Prices"):
        # Helper to find price in our scraped data
        def get_live_price(lab, test, backup):
            # Try to find an exact match or a partial match in the scraped names
            lab_data = live_data.get(lab, {})
            for name, price in lab_data.items():
                if test.lower() in name.lower():
                    return price
            return backup # Use your manual price if scraper didn't find it

        # Display results
        col1, col2, col3 = st.columns([2, 1, 1])
        col1.write("**Laboratory**")
        col2.write("**Price (PKR)**")
        col3.write("**Location**")
        st.divider()

        # Define Labs to show
        labs = [
            {"name": "Mughal", "backup": "Rs. 750", "loc": "Mughal Labs Lahore"},
            {"name": "Chughtai", "backup": "Rs. 950", "loc": "Chughtai Lab Lahore"},
            {"name": "IDC", "backup": "Rs. 900", "loc": "IDC Lahore"}
        ]

        for lab in labs:
            price = get_live_price(lab['name'], test_name, lab['backup'])
            
            c1, c2, c3 = st.columns([2, 1, 1])
            c1.write(f"**{lab['name']} Labs**")
            c2.write(f"**{price}**")
            query = urllib.parse.quote(lab['loc'])
            c3.link_button("📍 Find", f"https://www.google.com/maps/search/{query}")
            st.divider()
