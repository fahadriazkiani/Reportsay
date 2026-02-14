import streamlit as st
import google.generativeai as genai
from PIL import Image
import json
import os
import datetime
from fpdf import FPDF
import requests
import tempfile

# --- 1. PAGE CONFIGURATION (Favicon & Title) ---
# We use your logo as the browser tab icon (favicon)
st.set_page_config(
    page_title="ReportSay - AI Medical Assistant", 
    page_icon="https://i.postimg.cc/VLmw1MPY/logo.png", 
    layout="wide"
)

# --- 2. CUSTOM CSS (The "Old" Blue Color Combination) ---
st.markdown("""
    <style>
    /* Main Background */
    .main { background-color: #f8f9fa; }
    
    /* Hide default Streamlit header to make room for ours */
    header {visibility: hidden;}
    
    /* Custom Header Styling */
    .custom-header {
        text-align: center; 
        padding-bottom: 30px;
    }
    .custom-title {
        font-size: 4rem; 
        font-weight: 800; 
        color: #007BFF; /* The Professional Blue you liked */
        font-family: 'Helvetica Neue', sans-serif;
        vertical-align: middle;
    }
    .custom-subtitle {
        font-size: 1.3rem; 
        color: #555; 
        margin-top: -10px;
    }
    
    /* Button Styling */
    .stButton>button { 
        background-color: #007BFF; 
        color: white; 
        border-radius: 8px; 
        height: 3em; 
        font-weight: bold;
        border: none;
    }
    .stButton>button:hover { background-color: #0056b3; }
    
    /* Report Box Styling */
    .report-box { 
        background-color: #ffffff; 
        padding: 25px; 
        border-radius: 12px; 
        border-left: 6px solid #007BFF; 
        box-shadow: 0 4px 15px rgba(0,0,0,0.1);
    }
    </style>
    """, unsafe_allow_html=True)

# --- 3. SECURE API SETUP ---
if "MY_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["MY_API_KEY"])
else:
    st.error("⚠️ API Key missing! Please check Streamlit Secrets.")

# --- 4. CUSTOM HEADER (Logo + Title) ---
# This recreates the layout from your screenshot
st.markdown("""
    <div class="custom-header">
        <img src="https://i.postimg.cc/VLmw1MPY/logo.png" style="width: 100px; vertical-align: middle; margin-right: 15px;">
        <span class="custom-title">Reportsay</span>
        <p class="custom-subtitle">Your Personal AI Medical Assistant</p>
    </div>
    """, unsafe_allow_html=True)

# --- 5. MAIN NAVIGATION ---
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
            # Centering the image display
            col_img1, col_img2, col_img3 = st.columns([1, 2, 1])
            with col_img2:
                st.image(image, caption="Uploaded Document", use_container_width=True)
            
            if st.button("🔍 Analyze Report Now"):
                with st.spinner("🤖 AI is reading your report..."):
                    # Gemini 1.5 Flash Model
                    model = genai.GenerativeModel('gemini-1.5-flash')
                    prompt = (
                        f"You are a medical lab expert. Analyze this patient's lab report and explain it in {language}. "
                        "1. Summarize the key results.\n"
                        "2. Explicitly mention any HIGH or LOW values.\n"
                        "3. Explain what these tests are for in very simple terms.\n"
                        "4. Add a disclaimer: 'This is an AI interpretation. Please consult a doctor.'"
                    )
                    response = model.generate_content([prompt, image])
                    
                    # Display Result in the Blue Styled Box
                    st.markdown(f"""<div class="report-box"><h3>📝 AI Analysis Result</h3>{response.text}</div>""", unsafe_allow_html=True)
                    
                    # --- PDF GENERATION WITH HEADER LOGO ---
                    pdf = FPDF()
                    pdf.add_page()
                    
                    # 1. Add Logo to PDF
                    logo_url = "https://i.postimg.cc/VLmw1MPY/logo.png"
                    try:
                        response_img = requests.get(logo_url)
                        if response_img.status_code == 200:
                            with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmp_file:
                                tmp_file.write(response_img.content)
                                tmp_logo_path = tmp_file.name
                            # Centered Logo on PDF
                            pdf.image(tmp_logo_path, x=85, y=10, w=40)
                            pdf.ln(25)
                    except:
                        pdf.ln(10)

                    # 2. Add Title
                    pdf.set_font("Arial", 'B', 16)
                    pdf.cell(0, 10, txt="ReportSay Analysis", ln=True, align='C')
                    pdf.ln(5)
                    
                    # 3. Add Content
                    pdf.set_font("Arial", size=11)
                    text_content = response.text.encode('latin-1', 'replace').decode('latin-1')
                    pdf.multi_cell(0, 7, txt=text_content)
                    
                    # 4. Footer
                    pdf.ln(10)
                    pdf.set_font("Arial", 'I', 8)
                    pdf.cell(0, 10, txt="Generated by ReportSay AI. Not a medical diagnosis.", align='C')

                    pdf_output = pdf.output(dest='S').encode('latin-1')
                    
                    st.download_button(
                        label="📥 Download Official Report (PDF)",
                        data=pdf_output,
                        file_name="ReportSay_Analysis.pdf",
                        mime="application/pdf"
                    )
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
            
            # Master List for Dropdown
            all_tests = set()
            for tests in lab_data.values():
                all_tests.update(tests.keys())
            
            # Dynamic Dropdown Search
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
                        # Logic to find price (Exact or Partial match)
                        price = tests.get(selected_test)
                        if not price:
                            for k, v in tests.items():
                                if selected_test.lower() in k.lower():
                                    price = v
                                    break
                        
                        if price:
                            st.success(f"Rs. {price}")
                            found = True
                        else:
                            st.info("Check Lab")
                
                if not found:
                    st.warning("Price not available in current database.")

            # Timestamp
            mtime = os.path.getmtime(json_path)
            dt = datetime.datetime.fromtimestamp(mtime).strftime("%Y-%m-%d %H:%M")
            st.caption(f"Last updated: {dt}")
            
        except Exception as e:
            st.error(f"Data Error: {e}")
    else:
        st.warning("⚠️ Database is updating. Please run the 'Daily Lab Price Update' workflow on GitHub.")
