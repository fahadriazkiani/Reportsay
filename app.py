import streamlit as st
import google.generativeai as genai
from PIL import Image
import json
import os
import datetime
from fpdf import FPDF
import io
import requests
import tempfile

# --- 1. PAGE CONFIGURATION & STYLING ---
st.set_page_config(page_title="ReportSay - AI Lab Assistant", page_icon="🔬", layout="wide")

# Custom CSS for Professional Blue Theme
st.markdown("""
    <style>
    .main { background-color: #f8f9fa; }
    h1 { color: #007BFF; font-family: 'Helvetica Neue', sans-serif; }
    h2, h3 { color: #333; }
    .stButton>button { 
        background-color: #007BFF; 
        color: white; 
        border-radius: 8px; 
        height: 3em; 
        font-weight: bold;
    }
    .stButton>button:hover { background-color: #0056b3; }
    .report-box { 
        background-color: #ffffff; 
        padding: 20px; 
        border-radius: 10px; 
        border-left: 5px solid #007BFF; 
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    </style>
    """, unsafe_allow_html=True)

# --- 2. SECURE API SETUP ---
if "MY_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["MY_API_KEY"])
else:
    st.error("⚠️ API Key missing! Please check Streamlit Secrets.")

# --- 3. SIDEBAR ---
with st.sidebar:
    try:
        st.image("https://i.postimg.cc/VLmw1MPY/logo.png", use_container_width=True) 
    except:
        st.header("🔬 ReportSay")
    
    st.markdown("### 🏥 About ReportSay")
    st.info(
        "ReportSay helps patients understand medical lab reports using AI and compares test prices "
        "across top labs in Lahore like Mughal, SKM, and Chughtai."
    )
    st.markdown("---")
    st.caption("Developed by Fahad Riaz | Medical Lab Sciences")

# --- 4. MAIN TABS ---
tab1, tab2 = st.tabs(["📄 AI Report Analysis", "💰 Smart Price Checker"])

# ==========================================
# TAB 1: AI REPORT ANALYSIS
# ==========================================
with tab1:
    st.title("📊 Report Interpretation")
    st.markdown("Upload your medical lab report (Image or PDF) for a simple, AI-powered explanation.")

    col1, col2 = st.columns([1, 1])
    
    with col1:
        uploaded_file = st.file_uploader("📂 Upload Report", type=['png', 'jpg', 'jpeg', 'pdf'])
    
    with col2:
        language = st.selectbox("🌐 Select Language", ["English", "Urdu (اردو)"])

    if uploaded_file:
        try:
            image = Image.open(uploaded_file)
            st.image(image, caption="Uploaded Report", use_container_width=True)
            
            if st.button("🔍 Analyze Report"):
                with st.spinner("🤖 AI is analyzing your report..."):
                    # Gemini 1.5 Flash Model
                    model = genai.GenerativeModel('gemini-1.5-flash')
                    prompt = (
                        f"You are a helpful medical assistant. Analyze this lab report and explain it in {language}. "
                        "1. Summary of key findings.\n"
                        "2. Highlight any abnormal values (High/Low).\n"
                        "3. Simple explanation of what these tests mean.\n"
                        "4. Disclaimer: Consult a doctor for medical advice."
                    )
                    response = model.generate_content([prompt, image])
                    
                    # Display Result in Styled Box
                    st.markdown(f"""<div class="report-box"><h3>📝 AI Analysis</h3>{response.text}</div>""", unsafe_allow_html=True)
                    
                    # --- PDF GENERATION WITH LOGO ---
                    pdf = FPDF()
                    pdf.add_page()
                    
                    # 1. Download Logo Temporarily
                    logo_url = "https://i.postimg.cc/VLmw1MPY/logo.png"
                    try:
                        response_img = requests.get(logo_url)
                        if response_img.status_code == 200:
                            with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmp_file:
                                tmp_file.write(response_img.content)
                                tmp_logo_path = tmp_file.name
                            
                            # Add Logo (x, y, width) - Centered or Top Left
                            pdf.image(tmp_logo_path, x=10, y=8, w=40)
                            pdf.ln(20) # Add 20 units of space after logo
                        else:
                            pdf.ln(10) # Fallback spacing if logo fails
                    except:
                        pdf.ln(10)

                    # 2. Add Title & Content
                    pdf.set_font("Arial", 'B', 16)
                    pdf.cell(0, 10, txt="ReportSay - AI Analysis Report", ln=True, align='C')
                    pdf.ln(10) # More space
                    
                    pdf.set_font("Arial", size=11)
                    # Encode text to handle special characters
                    text_content = response.text.encode('latin-1', 'replace').decode('latin-1')
                    pdf.multi_cell(0, 7, txt=text_content)
                    
                    # 3. Footer / Disclaimer
                    pdf.ln(10)
                    pdf.set_font("Arial", 'I', 8)
                    pdf.cell(0, 10, txt="Generated by ReportSay. Consult a doctor for medical advice.", align='C')

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
    st.title("💰 Smart Price Checker")
    st.markdown("Compare live prices across **Mughal, SKM, Al-Noor, IDC, and Chughtai**.")

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
                "🔎 Search for a Lab Test:",
                options=[""] + sorted(list(all_tests)),
                format_func=lambda x: "Select a test..." if x == "" else x
            )
            
            if selected_test:
                st.markdown(f"### Results for: **{selected_test}**")
                cols = st.columns(3)
                found = False
                
                for idx, (lab_name, tests) in enumerate(lab_data.items()):
                    with cols[idx % 3]:
                        st.markdown(f"#### 🏥 {lab_name}")
                        # Case-insensitive matching
                        price = tests.get(selected_test)
                        if not price:
                            # Try flexible match if exact match fails
                            for k, v in tests.items():
                                if selected_test.lower() in k.lower():
                                    price = v
                                    break
                        
                        if price:
                            st.success(f"**Rs. {price}**")
                            found = True
                        else:
                            st.caption("Not listed")
                
                if not found:
                    st.warning("Price not available for this specific test in the current database.")

            # Last Updated Timestamp
            mtime = os.path.getmtime(json_path)
            dt = datetime.datetime.fromtimestamp(mtime).strftime("%Y-%m-%d %H:%M")
            st.caption(f"🕒 Prices updated: {dt}")
            
        except Exception as e:
            st.error(f"Data Error: {e}")
    else:
        st.warning("⚠️ Price database is empty. Please run the 'Daily Lab Price Update' workflow on GitHub.")
        st.info("💡 Tip: Go to GitHub > Actions > Daily Lab Price Update > Run workflow")
