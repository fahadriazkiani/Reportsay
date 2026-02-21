import streamlit as st
import google.generativeai as genai
from PIL import Image
import json
import os
import datetime
import requests
import tempfile
import re
import io

# ─────────────────────────────────────────────
# 1. PAGE CONFIG
# ─────────────────────────────────────────────
st.set_page_config(
    page_title="ReportSay – AI Medical Assistant",
    page_icon="https://i.postimg.cc/V6QMy94J/Without.png",
    layout="wide"
)

# ─────────────────────────────────────────────
# 2. CSS DESIGN SYSTEM
# ─────────────────────────────────────────────
st.markdown("""
<style>
/* ---------- BASE ---------- */
.main { background-color: #f4f8ff; }
header { visibility: hidden; }
.block-container { padding-top: 1rem; }

/* ---------- HERO ---------- */
.hero-container {
    display: flex; align-items: center; justify-content: center;
    background: linear-gradient(135deg, #e8f4ff 0%, #f0f7ff 100%);
    padding: 2.5rem; border-radius: 18px;
    box-shadow: 0 4px 20px rgba(0,123,255,0.08);
    margin-bottom: 28px; border: 1px solid #d0e8ff;
}
.hero-logo { width: 90px; height: auto; margin-right: 24px; }
.hero-title { font-size: 3.2rem; font-weight: 900; color: #005ecb !important;
    line-height: 1.1; margin: 0; font-family: 'Helvetica Neue', sans-serif; }
.hero-subtitle { font-size: 1.15rem; color: #4a6fa5; margin: 6px 0 0 0; font-weight: 400; }
.hero-badge {
    display: inline-block; background: #007BFF; color: white;
    font-size: 0.75rem; font-weight: 700; padding: 3px 10px;
    border-radius: 20px; margin-top: 8px; letter-spacing: 0.5px;
}

/* ---------- TABS ---------- */
.stTabs [data-baseweb="tab-list"] {
    gap: 8px; background-color: transparent;
    border-bottom: 2px solid #d0e0f7; padding-bottom: 0;
}
.stTabs [data-baseweb="tab"] {
    height: 50px; background-color: #ffffff;
    border-radius: 10px 10px 0 0; padding: 10px 20px;
    border: 1px solid #d0e0f7; border-bottom: none;
    color: #555; font-weight: 600; flex: 1;
}
.stTabs [data-baseweb="tab"][aria-selected="true"] {
    background-color: #e0f0ff !important; color: #005ecb !important;
    border: 2px solid #005ecb; border-bottom: none; font-weight: 800;
}
.stTabs [data-baseweb="tab"]:hover { color: #005ecb; background-color: #f0f7ff; }

/* ---------- SECTION HEADERS ---------- */
.section-header {
    font-size: 1.3rem; font-weight: 700; color: #333;
    margin-bottom: 12px; padding-bottom: 6px;
    border-bottom: 2px solid #e0eeff;
}

/* ---------- REPORT BOX ---------- */
.report-box {
    background: #ffffff; padding: 28px; border-radius: 14px;
    border-left: 5px solid #007BFF;
    box-shadow: 0 6px 20px rgba(0,123,255,0.07); margin-top: 20px;
}
.report-box h3 { color: #005ecb; margin-top: 0; }

/* ---------- DISCLAIMER BOX ---------- */
.disclaimer-box {
    background: #fff8e1; padding: 14px 18px; border-radius: 10px;
    border-left: 4px solid #ffc107; margin-top: 16px;
    font-size: 0.9rem; color: #7a5c00;
}

/* ---------- PRIVACY BADGE ---------- */
.privacy-badge {
    background: #e8f5e9; border: 1px solid #a5d6a7; border-radius: 8px;
    padding: 10px 14px; font-size: 0.85rem; color: #2e7d32;
    display: flex; align-items: center; gap: 8px; margin-top: 12px;
}

/* ---------- LAB CARDS ---------- */
.lab-card {
    background: #ffffff; border-radius: 14px; padding: 20px;
    margin-bottom: 15px; box-shadow: 0 4px 12px rgba(0,0,0,0.06);
    border: 1px solid #e1e8f5; text-align: center;
    transition: transform 0.2s, box-shadow 0.2s;
    height: 230px; display: flex; flex-direction: column;
    justify-content: space-between;
}
.lab-card:hover {
    transform: translateY(-5px);
    box-shadow: 0 12px 24px rgba(0,123,255,0.15);
    border-color: #007BFF;
}
.lab-name { font-size: 1rem; font-weight: 700; color: #333; }
.lab-price { font-size: 2rem; font-weight: 900; color: #1a7a3a; margin: 10px 0; }
.lab-price-missing { font-size: 1rem; color: #888; font-style: italic; margin: 15px 0; }
.lab-btn {
    display: block; width: 100%; padding: 10px 0;
    background: linear-gradient(135deg, #007BFF, #0056b3);
    color: white !important; text-decoration: none; border-radius: 8px;
    font-weight: 600; transition: opacity 0.2s; text-align: center;
}
.lab-btn:hover { opacity: 0.88; }

/* ---------- INFO CARDS ---------- */
.info-card {
    background: #f0f7ff; border-radius: 12px; padding: 18px;
    border: 1px solid #cce0ff; margin-bottom: 12px; font-size: 0.9rem; color: #334;
}

/* ---------- STEP BADGE ---------- */
.step-badge {
    display: inline-block; background: #007BFF; color: white;
    border-radius: 50%; width: 26px; height: 26px; text-align: center;
    line-height: 26px; font-weight: 800; font-size: 0.85rem; margin-right: 8px;
}
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# 3. API SETUP
# ─────────────────────────────────────────────
api_configured = False
if "MY_API_KEY" in st.secrets:
    try:
        genai.configure(api_key=st.secrets["MY_API_KEY"])
        api_configured = True
    except Exception as e:
        st.error(f"⚠️ API configuration failed: {e}")
else:
    st.error("⚠️ API Key missing. Please add `MY_API_KEY` to Streamlit Secrets.")

# ─────────────────────────────────────────────
# 4. SESSION STATE INIT
# ─────────────────────────────────────────────
if "analysis_result" not in st.session_state:
    st.session_state.analysis_result = None
if "analysis_language" not in st.session_state:
    st.session_state.analysis_language = "English"
if "last_filename" not in st.session_state:
    st.session_state.last_filename = None

# ─────────────────────────────────────────────
# 5. HERO HEADER
# ─────────────────────────────────────────────
st.markdown("""
<div class="hero-container">
    <img src="https://i.postimg.cc/V6QMy94J/Without.png" class="hero-logo">
    <div>
        <h1 class="hero-title">Reportsay</h1>
        <p class="hero-subtitle">AI Medical Report Analysis & Lab Price Comparison — Lahore, Pakistan</p>
        <span class="hero-badge">🔒 Private · Secure · Free to Try</span>
    </div>
</div>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# 6. HELPER FUNCTIONS
# ─────────────────────────────────────────────

def get_gemini_model():
    """Get best available Gemini model with proper error handling."""
    try:
        all_models = [
            m for m in genai.list_models()
            if 'generateContent' in m.supported_generation_methods
        ]
        # Prefer flash (fast & cheap), then pro
        for m in all_models:
            if 'flash' in m.name:
                return genai.GenerativeModel(m.name), m.name
        for m in all_models:
            if '1.5-pro' in m.name:
                return genai.GenerativeModel(m.name), m.name
        if all_models:
            return genai.GenerativeModel(all_models[0].name), all_models[0].name
        return None, None
    except Exception as e:
        return None, str(e)


def open_uploaded_file(uploaded_file):
    """
    Safely open uploaded file as a PIL Image.
    Handles JPG, PNG, and PDF (first page only).
    Returns (image, error_message).
    """
    MAX_SIZE_MB = 10
    file_bytes = uploaded_file.getvalue()

    if len(file_bytes) > MAX_SIZE_MB * 1024 * 1024:
        return None, f"File is too large ({len(file_bytes)//1024//1024} MB). Please upload a file under {MAX_SIZE_MB} MB."

    file_type = uploaded_file.type

    if file_type == "application/pdf":
        try:
            import fitz  # PyMuPDF
            doc = fitz.open(stream=file_bytes, filetype="pdf")
            if doc.page_count == 0:
                return None, "PDF appears to be empty."
            page = doc[0]
            pix = page.get_pixmap(dpi=150)
            image = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
            return image, None
        except ImportError:
            return None, "PDF support requires PyMuPDF. Please add `pymupdf` to requirements.txt."
        except Exception as e:
            return None, f"Could not read PDF: {e}"
    else:
        try:
            image = Image.open(io.BytesIO(file_bytes))
            image.verify()  # Check it's a valid image
            image = Image.open(io.BytesIO(file_bytes))  # Re-open after verify
            return image, None
        except Exception as e:
            return None, f"Could not open image: {e}"


def build_analysis_prompt(language: str) -> str:
    """Return a structured, consistent prompt for medical report analysis."""
    return f"""You are a professional medical lab report interpreter. A patient has uploaded their lab report.

Analyze the report carefully and respond ONLY in {language}.

Structure your response exactly as follows:

---
**🧪 Tests Detected**
List all tests found in the report (e.g., CBC, HbA1c, etc.)

**✅ Normal Results**
List each result that is within the normal reference range. Format: Test Name → Value (Normal Range)

**⚠️ Abnormal Results**
List each result outside the normal range. For each one, briefly explain in simple terms what it may suggest. Format: Test Name → Value (Normal Range) — What this means

**📋 Summary**
A 2–3 sentence plain-language summary of the overall report for a non-medical reader.

**💡 Suggested Next Steps**
What should the patient discuss with their doctor? List 2–3 specific points.

---
⚕️ **Important Disclaimer:** This analysis is generated by AI and is for informational purposes only. It does not constitute medical advice, diagnosis, or treatment. Always consult a qualified physician before making any health decisions.
"""


def generate_pdf_report(analysis_text: str, language: str) -> bytes:
    """
    Generate a clean PDF report.
    Uses reportlab for proper Unicode (Urdu) support.
    Falls back to FPDF for environments without reportlab.
    """
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import cm
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
        from reportlab.lib import colors
        from reportlab.lib.enums import TA_LEFT

        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4,
                                leftMargin=2*cm, rightMargin=2*cm,
                                topMargin=2*cm, bottomMargin=2*cm)

        styles = getSampleStyleSheet()
        title_style = ParagraphStyle('title', fontSize=18, fontName='Helvetica-Bold',
                                     textColor=colors.HexColor('#005ecb'), spaceAfter=6)
        sub_style = ParagraphStyle('sub', fontSize=10, fontName='Helvetica',
                                   textColor=colors.HexColor('#666666'), spaceAfter=14)
        body_style = ParagraphStyle('body', fontSize=11, fontName='Helvetica',
                                    leading=16, spaceAfter=6, alignment=TA_LEFT)

        # Clean markdown for PDF
        clean = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', analysis_text)
        clean = re.sub(r'\*(.*?)\*', r'<i>\1</i>', clean)
        clean = re.sub(r'^#+\s+', '', clean, flags=re.MULTILINE)

        story = [
            Paragraph("ReportSay", title_style),
            Paragraph(f"AI Medical Report Analysis · Generated {datetime.datetime.now().strftime('%d %b %Y, %H:%M')} · Language: {language}", sub_style),
            Spacer(1, 0.3*cm),
        ]

        for line in clean.split('\n'):
            line = line.strip()
            if line == '---':
                story.append(Spacer(1, 0.3*cm))
            elif line:
                try:
                    story.append(Paragraph(line, body_style))
                except Exception:
                    story.append(Paragraph(line.encode('ascii', 'replace').decode(), body_style))

        doc.build(story)
        return buffer.getvalue()

    except ImportError:
        # Fallback: FPDF (latin-1 only, Urdu will be replaced with ?)
        from fpdf import FPDF
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", 'B', 16)
        pdf.cell(0, 10, "ReportSay – AI Analysis", ln=True, align='C')
        pdf.set_font("Arial", size=10)
        pdf.cell(0, 8, f"Generated: {datetime.datetime.now().strftime('%d %b %Y %H:%M')}   Language: {language}", ln=True, align='C')
        pdf.ln(5)
        pdf.set_font("Arial", size=11)
        clean = re.sub(r'\*\*|__|\*|_|^#+\s+', '', analysis_text, flags=re.MULTILINE)
        safe = clean.encode('latin-1', 'replace').decode('latin-1')
        pdf.multi_cell(0, 7, txt=safe)
        return pdf.output(dest='S').encode('latin-1')


# ─────────────────────────────────────────────
# 7. PRICE DATABASE FALLBACK
# ─────────────────────────────────────────────
FALLBACK_PRICES = {
    "Chughtai Lab": {
        "CBC": 700, "HbA1c": 1200, "Glucose Profile": 500,
        "Lipid Profile": 1800, "LFTs": 2200, "RFTs": 1600,
        "Thyroid Profile": 2500, "Vitamins": 1800
    },
    "Shaukat Khanum": {
        "CBC": 900, "HbA1c": 1500, "Glucose Profile": 600,
        "Lipid Profile": 2200, "LFTs": 2800, "RFTs": 2000,
        "Thyroid Profile": 3000, "Vitamins": 2200
    },
    "Mughal Labs": {
        "CBC": 800,
    "HbA1c": 2300,
    "Glucose Profile": 450,
    "Lipid Profile": 2500,
    "LFTs": 2200,
    "RFTs": 1650,
    "Cardiac Profile": 6400,
    "Thyroid Profile": 3950,
    "Vitamins": 3950
    },
    "IDC": {
        "CBC": 650, "HbA1c": 1100, "Glucose Profile": 450,
        "Lipid Profile": 1700, "LFTs": 2000, "RFTs": 1500,
        "Thyroid Profile": 2400, "Vitamins": 1700
    },
    "Al-Noor": {
        "CBC": 450, "HbA1c": 850, "Glucose Profile": 350,
        "Lipid Profile": 1300, "LFTs": 1600, "RFTs": 1100,
        "Thyroid Profile": 1900, "Vitamins": 1400
    },
    "Excel Labs": {
        "CBC": 600, "HbA1c": 1000, "Glucose Profile": 420,
        "Lipid Profile": 1600, "LFTs": 1900, "RFTs": 1400,
        "Thyroid Profile": 2300, "Vitamins": 1600
    }
}

LAB_LOCATIONS = {
    "Mughal Labs":      "https://www.google.com/maps/search/Mughal+Labs+Lahore",
    "Shaukat Khanum":   "https://www.google.com/maps/search/Shaukat+Khanum+Laboratory+Lahore",
    "IDC":              "https://www.google.com/maps/search/Islamabad+Diagnostic+Centre+Lahore",
    "Chughtai Lab":     "https://www.google.com/maps/search/Chughtai+Lab+Lahore",
    "Al-Noor":          "https://www.google.com/maps/search/Al-Noor+Diagnostic+Centre+Lahore",
    "Excel Labs":       "https://www.google.com/maps/search/Excel+Labs+Lahore"
}

COMMON_TESTS = [
    "Select a test...", "CBC", "HbA1c", "Glucose Profile",
    "Lipid Profile", "LFTs", "RFTs", "Cardiac Profile",
    "Thyroid Profile", "Vitamins"
]

# ─────────────────────────────────────────────
# 8. TABS
# ─────────────────────────────────────────────
tab1, tab2, tab3 = st.tabs([
    "📄 AI Report Analysis",
    "💰 Smart Price Checker",
    "ℹ️ How It Works"
])

# ══════════════════════════════════════════════
# TAB 1 — AI REPORT ANALYSIS
# ══════════════════════════════════════════════
with tab1:

    # Privacy notice
    st.markdown("""
    <div class="privacy-badge">
        🔒 Your document is sent directly to Google Gemini AI for analysis and is <strong>not stored</strong> on our servers.
        Do not upload documents containing your full name, CNIC, or address.
    </div>
    """, unsafe_allow_html=True)

    st.write("")

    col1, col2 = st.columns([1, 1], gap="large")

    with col1:
        st.markdown('<div class="section-header">📤 Upload Your Report</div>', unsafe_allow_html=True)
        uploaded_file = st.file_uploader(
            "Upload Image or PDF",
            type=['png', 'jpg', 'jpeg', 'pdf'],
            help="Supported: PNG, JPG, JPEG, PDF. Max size: 10 MB."
        )
        st.caption("📌 Tip: For PDFs, only the **first page** is analyzed. Crop or photograph a single report page for best results.")

    with col2:
        st.markdown('<div class="section-header">🌐 Language</div>', unsafe_allow_html=True)
        language = st.selectbox(
            "Select Interpretation Language",
            ["English", "Urdu (اردو)"],
            help="AI will interpret and explain results in your chosen language."
        )
        st.caption("Urdu support is in beta. Medical terms may still appear in English.")

    # ── File processing ──
    if uploaded_file:

        # Reset results if a new file is uploaded
        if uploaded_file.name != st.session_state.last_filename:
            st.session_state.analysis_result = None
            st.session_state.last_filename = uploaded_file.name

        st.markdown("---")

        image, error = open_uploaded_file(uploaded_file)

        if error:
            st.error(f"❌ {error}")
        else:
            # Preview
            col_img1, col_img2, col_img3 = st.columns([1, 2, 1])
            with col_img2:
                st.markdown('<div style="background:white;padding:15px;border-radius:12px;border:1px solid #ddd;box-shadow:0 4px 6px rgba(0,0,0,0.05);">', unsafe_allow_html=True)
                st.image(image, caption="Document Preview (Page 1)", use_container_width=True)
                st.markdown('</div>', unsafe_allow_html=True)

            st.write("")

            # Analyze button
            if st.button("✨ Analyze Report Now", use_container_width=True, type="primary"):
                if not api_configured:
                    st.error("API key is not configured. Cannot analyze.")
                else:
                    with st.spinner("🤖 AI is reading your report — this takes 10–20 seconds..."):
                        model, model_name = get_gemini_model()
                        if model is None:
                            st.error(f"⚠️ Could not connect to AI model. Details: {model_name}")
                        else:
                            try:
                                prompt = build_analysis_prompt(language)
                                response = model.generate_content([prompt, image])
                                st.session_state.analysis_result = response.text
                                st.session_state.analysis_language = language
                                st.success(f"✅ Analysis complete using {model_name.split('/')[-1]}")
                            except Exception as e:
                                err = str(e)
                                if "429" in err:
                                    st.warning("🚦 API rate limit reached. Please wait 30–60 seconds and try again.")
                                elif "400" in err:
                                    st.error("❌ The image could not be processed. Try a clearer photo or different format.")
                                else:
                                    st.error(f"❌ AI Error: {err}")

            # ── Show result (persists in session) ──
            if st.session_state.analysis_result:
                st.markdown(f"""
                <div class="report-box">
                    <h3>📝 AI Analysis Result</h3>
                    {st.session_state.analysis_result.replace(chr(10), '<br>')}
                </div>
                """, unsafe_allow_html=True)

                st.markdown("""
                <div class="disclaimer-box">
                    ⚕️ <strong>Disclaimer:</strong> This is an AI-generated interpretation for informational use only.
                    It is not a substitute for professional medical advice. Always consult your doctor.
                </div>
                """, unsafe_allow_html=True)

                # PDF Download
                st.write("")
                try:
                    pdf_bytes = generate_pdf_report(
                        st.session_state.analysis_result,
                        st.session_state.analysis_language
                    )
                    st.download_button(
                        label="📥 Download Analysis as PDF",
                        data=pdf_bytes,
                        file_name=f"ReportSay_Analysis_{datetime.datetime.now().strftime('%Y%m%d_%H%M')}.pdf",
                        mime="application/pdf",
                        use_container_width=True
                    )
                except Exception as e:
                    st.warning(f"PDF generation failed: {e}. You can copy the text above manually.")

                # Clear button
                if st.button("🗑️ Clear & Analyze Another Report", use_container_width=True):
                    st.session_state.analysis_result = None
                    st.session_state.last_filename = None
                    st.rerun()

# ══════════════════════════════════════════════
# TAB 2 — SMART PRICE CHECKER
# ══════════════════════════════════════════════
with tab2:
    st.markdown("### 🏥 Compare Lab Test Prices in Lahore")
    st.caption("Prices shown are approximate. Contact labs directly to confirm current rates.")

    # Load from JSON if available, otherwise use fallback
    json_path = 'data/lab_prices.json'
    data_source = "static fallback"
    lab_data = FALLBACK_PRICES

    if os.path.exists(json_path):
        try:
            with open(json_path, 'r') as f:
                lab_data = json.load(f)
            mtime = os.path.getmtime(json_path)
            dt = datetime.datetime.fromtimestamp(mtime).strftime("%d %b %Y %H:%M")
            data_source = f"live database (updated {dt})"
        except Exception:
            st.warning("⚠️ Could not load live price database. Showing approximate prices.")

    st.caption(f"📊 Source: {data_source}")

    selected_test = st.selectbox("Select a Test:", options=COMMON_TESTS)

    if selected_test and selected_test != "Select a test...":
        st.markdown(f"#### 💰 Price Comparison for: **{selected_test}**")

        cols = st.columns(3)
        prices_found = []

        for idx, (lab_name, tests) in enumerate(lab_data.items()):
            price = tests.get(selected_test)
            if not price:
                for k, v in tests.items():
                    if selected_test.lower() in k.lower() and len(k) < 30:
                        price = v
                        break

            if price:
                prices_found.append(int(price))

            try:
                price_display = f'<div class="lab-price">Rs. {int(price):,}</div>' if price else '<div class="lab-price-missing">Call to confirm</div>'
            except (ValueError, TypeError):
                price_display = f'<div class="lab-price">Rs. {price}</div>' if price else '<div class="lab-price-missing">Call to confirm</div>'
            map_link = LAB_LOCATIONS.get(lab_name, "https://www.google.com/maps/search/diagnostic+labs+lahore")

            with cols[idx % 3]:
                st.markdown(f"""
                <div class="lab-card">
                    <div class="lab-name">{lab_name}</div>
                    {price_display}
                    <a href="{map_link}" target="_blank" class="lab-btn">📍 Get Directions</a>
                </div>
                """, unsafe_allow_html=True)

        # Price summary
        if prices_found:
            min_p, max_p = min(prices_found), max(prices_found)
            avg_p = sum(prices_found) // len(prices_found)
            st.markdown(f"""
            <div class="info-card" style="margin-top:20px;">
                💡 <strong>Price Summary for {selected_test}:</strong> &nbsp;
                Lowest: <strong>Rs. {min_p:,}</strong> &nbsp;|&nbsp;
                Highest: <strong>Rs. {max_p:,}</strong> &nbsp;|&nbsp;
                Average: <strong>Rs. {avg_p:,}</strong>
            </div>
            """, unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("""
    <div class="info-card">
        📞 <strong>Tip:</strong> Many labs offer home sample collection for an additional Rs. 200–500.
        Call ahead to book a slot and confirm prices, as they may vary by branch.
    </div>
    """, unsafe_allow_html=True)

# ══════════════════════════════════════════════
# TAB 3 — HOW IT WORKS
# ══════════════════════════════════════════════
with tab3:
    st.markdown("### ℹ️ How ReportSay Works")

    col_a, col_b = st.columns(2, gap="large")

    with col_a:
        st.markdown("""
        <div class="info-card">
            <b><span class="step-badge">1</span> Upload Your Report</b><br><br>
            Take a clear photo of your lab report or scan it as a PDF.
            Upload it using the file uploader on the Analysis tab.
        </div>
        <div class="info-card">
            <b><span class="step-badge">2</span> Choose Your Language</b><br><br>
            Select English or Urdu. The AI will explain your results
            in plain, easy-to-understand language.
        </div>
        <div class="info-card">
            <b><span class="step-badge">3</span> Get Your Analysis</b><br><br>
            Our AI (powered by Google Gemini) reads the report, identifies
            normal and abnormal values, and explains what they may mean.
        </div>
        <div class="info-card">
            <b><span class="step-badge">4</span> Download & Share</b><br><br>
            Download a clean PDF of the analysis to share with your
            family or bring to your doctor's appointment.
        </div>
        """, unsafe_allow_html=True)

    with col_b:
        st.markdown("""
        <div class="info-card">
            <b>🔒 Privacy & Data</b><br><br>
            Your report image is sent directly to Google's Gemini API for analysis.
            <strong>We do not store, log, or save your report.</strong>
            Avoid uploading documents with your full name, CNIC number, or home address.
        </div>
        <div class="info-card">
            <b>⚕️ Medical Disclaimer</b><br><br>
            ReportSay is an AI tool for general information only.
            It does <strong>not</strong> provide medical diagnoses.
            Always consult a qualified doctor before making any health decisions.
            In an emergency, call <strong>1122</strong> (Pakistan Emergency Services).
        </div>
        <div class="info-card">
            <b>💰 Price Checker</b><br><br>
            Lab prices shown are approximate and sourced from publicly available rate cards.
            Prices may vary by branch, time of year, and whether you book online or walk in.
            Always call the lab to confirm the exact rate.
        </div>
        """, unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("""
    <div style="text-align:center; color:#888; font-size:0.85rem; padding: 10px 0 20px 0;">
        Built with ❤️ for Pakistan · Powered by Google Gemini AI ·
        <a href="mailto:hello@reportsay.com" style="color:#007BFF;">Contact Us</a>
    </div>
    """, unsafe_allow_html=True)
