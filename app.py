import streamlit as st
import google.generativeai as genai
from PyPDF2 import PdfReader
import re
import plotly.graph_objects as go
import time
import os

# --- 1. CONFIGURATION & BRANDING ---
# We check if a logo file exists to use it as the browser favicon
logo_path = "logo.png"
favicon = logo_path if os.path.exists(logo_path) else "📉"

st.set_page_config(
    page_title="EarningsCall.ai Pro", 
    page_icon=favicon, 
    layout="wide"
)

#⚠️ PASTE YOUR KEY BELOW
api_key = None

# Logic for Streamlit Cloud vs Local
try:
    if "GOOGLE_API_KEY" in st.secrets:
        api_key = st.secrets["GOOGLE_API_KEY"]
except:
    st.error("Missing API Key. Please configure secrets.")

try:
    genai.configure(api_key=api_key)
except Exception as e:
    st.error(f"⚠️ API Key Error: {e}")

# --- 2. PROFESSIONAL CSS (Cards, Layouts & Loader) ---
st.markdown("""
<style>
    /* Main Background */
    .stApp {
        background-color: #F8F9FA;
    }
    
    /* UNIVERSAL CARD STYLE */
    .feature-card {
        border-radius: 12px;
        padding: 20px;
        height: 180px; 
        box-shadow: 0 4px 6px rgba(0,0,0,0.05);
        display: flex;
        flex-direction: column;
        justify-content: flex-start;
        margin-bottom: 20px;
    }
    
    /* Card Colors */
    .card-blue { background-color: #E3F2FD; border: 1px solid #BBDEFB; }
    .card-yellow { background-color: #FFF9C4; border: 1px solid #FFF59D; }
    .card-green { background-color: #E8F5E9; border: 1px solid #C8E6C9; }
    .card-red { background-color: #FFEBEE; border: 1px solid #FFCDD2; }
    .card-purple { background-color: #F3E5F5; border: 1px solid #E1BEE7; }
    .card-gray { background-color: #F5F5F5; border: 1px solid #E0E0E0; }

    /* Card Typography */
    .feature-card h4 {
        color: #1A202C;
        font-size: 1.1rem;
        font-weight: 700;
        margin-bottom: 10px;
    }
    .feature-card p {
        color: #4A5568;
        font-size: 0.95rem;
        line-height: 1.5;
        margin: 0;
    }

    /* BUTTON STYLING */
    .stButton>button {
        width: 100%;
        border-radius: 8px;
        height: 3.5em;
        background: #2962FF !important; 
        border: none;
        box-shadow: 0 4px 6px rgba(41, 98, 255, 0.2);
        transition: all 0.3s ease;
    }
    .stButton>button p {
        color: #FFFFFF !important;
        font-weight: 700 !important;
        font-size: 16px !important;
    }
    .stButton>button:hover {
        background: #0039CB !important;
        box-shadow: 0 6px 12px rgba(41, 98, 255, 0.4);
        transform: translateY(-2px);
    }

    /* CUSTOM LOADING OVERLAY */
    .loader-container {
        position: fixed;
        top: 50%;
        left: 50%;
        transform: translate(-50%, -50%);
        background: white;
        padding: 40px;
        border-radius: 15px;
        box-shadow: 0 10px 25px rgba(0,0,0,0.1);
        z-index: 9999;
        text-align: center;
        width: 300px;
    }
    .loader-text {
        font-family: 'Inter', sans-serif;
        color: #1A202C;
        margin-bottom: 15px;
        font-weight: 600;
    }
    /* Simple CSS Spinner/Progress Bar */
    .progress-bar-container {
        width: 100%;
        background-color: #e0e0e0;
        border-radius: 5px;
        height: 8px;
        overflow: hidden;
    }
    .progress-bar-fill {
        height: 100%;
        background-color: #2962FF;
        width: 0%;
        animation: progress 2s infinite ease-in-out;
        border-radius: 5px;
    }
    @keyframes progress {
        0% { width: 0%; margin-left: 0%; }
        50% { width: 50%; margin-left: 25%; }
        100% { width: 100%; margin-left: 100%; }
    }
</style>
""", unsafe_allow_html=True)

# --- 3. HELPER: GAUGE CHART ---
def create_gauge(score):
    color = "#EF4444" if score > 70 else "#F59E0B" if score > 30 else "#10B981"
    
    fig = go.Figure(go.Indicator(
        mode = "gauge+number",
        value = score,
        domain = {'x': [0, 1], 'y': [0, 1]},
        title = {'text': "RISK METER", 'font': {'size': 14, 'color': "#64748B"}},
        number = {'font': {'size': 40, 'weight': 'bold', 'color': "#1E293B"}},
        gauge = {
            'axis': {'range': [0, 100], 'tickwidth': 1, 'tickcolor': "white"},
            'bar': {'color': color},
            'bgcolor': "white",
            'borderwidth': 2,
            'bordercolor': "#F1F5F9",
            'steps': [
                {'range': [0, 30], 'color': "#D1FAE5"},
                {'range': [30, 70], 'color': "#FEF3C7"},
                {'range': [70, 100], 'color': "#FEE2E2"}
            ],
        }
    ))
    fig.update_layout(height=250, margin=dict(l=20, r=20, t=30, b=20), paper_bgcolor="rgba(0,0,0,0)")
    return fig

# --- 4. SIDEBAR ---
with st.sidebar:
    # BRANDING SECTION
    # Checks for logo.png, otherwise uses text header
    if os.path.exists("logo.png"):
        st.image("logo.png", width=60) 
        st.markdown("### EarningsCall.ai")
    else:
        st.header("EarningsCall.ai")
    
    st.caption("INSTITUTIONAL GRADE v8.0")
    st.write("")
    
    uploaded_file = st.file_uploader("Upload Transcript (PDF)", type=["pdf"])
    
    st.markdown("---")
    with st.expander("ℹ️ Quick Guide", expanded=False):
        st.markdown("""
        **1. Upload:** Drag & Drop a PDF.
        **2. Analyze:** Click the blue button.
        **3. Review:** Check the Risk Meter & Red Flags.
        """)

# --- 5. MAIN APP ---
if uploaded_file is None:
    # LANDING PAGE
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("<h1 style='text-align: center;'>Reveal the Risks Wall Street Misses</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; font-size: 1.2rem; color: #64748B;'>The AI Analyst that reads between the lines of every earnings call.</p>", unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)

    # --- FEATURE CARDS ---
    c1, c2, c3 = st.columns(3)
    
    with c1:
        st.markdown("""
        <div class="feature-card card-blue">
            <h4>🔍 Deception Detection</h4>
            <p>Identifies vague phrasing like "we hope", "trying to", or "challenging environment" that signals lack of confidence.</p>
        </div>
        """, unsafe_allow_html=True)
        
    with c2:
        st.markdown("""
        <div class="feature-card card-yellow">
            <h4>📉 Non-GAAP Scan</h4>
            <p>Flags when management excessively uses "Adjusted EBITDA" or "Pro-Forma" numbers to mask actual Net Income losses.</p>
        </div>
        """, unsafe_allow_html=True)
        
    with c3:
        st.markdown("""
        <div class="feature-card card-green">
            <h4>🗣️ Tone Analysis</h4>
            <p>Compares the polished, scripted prepared remarks against the unscripted, nervous answers during the Q&A session.</p>
        </div>
        """, unsafe_allow_html=True)

    c4, c5, c6 = st.columns(3)
    
    with c4:
        st.markdown("""
        <div class="feature-card card-red">
            <h4>🌫️ Fog Index</h4>
            <p>Quantifies how confusing the CEO's language is. A high Fog Index often correlates with hiding bad news.</p>
        </div>
        """, unsafe_allow_html=True)
        
    with c5:
        st.markdown("""
        <div class="feature-card card-purple">
            <h4>⚡ Q&A Divergence</h4>
            <p>Detects specific moments where executive sentiment drops significantly when facing tough analyst questions.</p>
        </div>
        """, unsafe_allow_html=True)
        
    with c6:
        st.markdown("""
        <div class="feature-card card-gray">
            <h4>🔭 Future Sentiment</h4>
            <p>Measures the ratio of Future Tense (Growth plans) versus Past Tense (Excuses for poor performance).</p>
        </div>
        """, unsafe_allow_html=True)

    # --- HOW IT WORKS SECTION ---
    st.markdown("<br><hr><br>", unsafe_allow_html=True)
    st.markdown("### 🎯 How to Master Earnings Season")
    
    col_a, col_b, col_c = st.columns(3)
    with col_a:
        st.markdown("#### 1. The Problem")
        st.info("CEOs are trained to hide bad news in boring paragraphs. Retail traders often only read the headlines, missing the structural risks buried in page 14.")
    with col_b:
        st.markdown("#### 2. Get Transcripts")
        st.write("You don't need expensive terminals. Download free PDF transcripts from **Investor Relations** pages (e.g., apple.com/investor) or apps like **Quarterr**.")
    with col_c:
        st.markdown("#### 3. The Edge")
        st.success("Our AI scans for hesitation, contradictions, and psychological cues that indicate a stock is about to crash—metrics that charts can't show you.")

else:
    # --- PROCESSING STATE ---
    with st.spinner("Processing PDF Document..."):
        try:
            reader = PdfReader(uploaded_file)
            text = ""
            for page in reader.pages:
                text += page.extract_text()
        except Exception as e:
            st.error(f"Error reading PDF: {e}")
            st.stop()

    # --- THE INSTITUTIONAL PROMPT ---
    system_prompt = """
    You are a veteran Wall Street Analyst (Goldman Sachs/Morgan Stanley level). Analyze this earnings call transcript.
    
    STEP 1: CALCULATE ADVANCED METRICS (Strict JSON format)
    - RISK_SCORE: (0-100) based on negative sentiment and vague answers.
    - FOG_INDEX: (Low/Medium/High) - Is the language simple or intentionally confusing?
    - NON_GAAP_INTENSITY: (Low/Medium/High) - How heavily do they rely on "Adjusted" or "Non-GAAP" metrics?
    - FUTURE_FOCUS: (Positive/Neutral/Negative) - Are they talking about "growth/expansion" (Future) or "challenges/impacts" (Past)?
    
    STEP 2: EXECUTIVE SUMMARY
    - Headline: A WSJ-style headline (max 10 words).
    - Verdict: (Bullish / Bearish / Neutral)
    
    STEP 3: DEEP DIVE
    - 🚩 Red Flags: List 3 specific concerns with quotes.
    - 🛡️ The Defense: What is the company's main positive argument?
    - 🗣️ Q&A Analysis: Did they dodge any specific analyst questions?
    
    OUTPUT FORMAT:
    [METRICS]
    RISK_SCORE: 82
    FOG_INDEX: High
    NON_GAAP_INTENSITY: High
    FUTURE_FOCUS: Negative
    [END METRICS]
    
    [HEADLINE]
    Management struggles to explain margin compression amid rising costs.
    [VERDICT]
    Bearish
    [ANALYSIS]
    ... (Rest of the analysis)
    """

    # --- ANALYSIS TRIGGER ---
    if st.button("🚀 Run Institutional Analysis"):
        if "PASTE_YOUR_KEY" in api_key:
             st.error("⚠️ Please insert your API Key in the code.")
        else:
            # 1. CREATE LOADING PLACEHOLDER (Center Screen)
            loader_placeholder = st.empty()
            loader_placeholder.markdown("""
            <div class="loader-container">
                <div class="loader-text">Analyzing Executive Tone...</div>
                <div class="progress-bar-container">
                    <div class="progress-bar-fill"></div>
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            try:
                # 2. RUN AI (This takes a few seconds)
                model = genai.GenerativeModel('gemini-2.5-flash') 
                response = model.generate_content(system_prompt + "\n\nTRANSCRIPT:\n" + text)
                raw_text = response.text
                
                # 3. SMOOTH FINISH
                loader_placeholder.markdown("""
                <div class="loader-container">
                    <div class="loader-text" style="color: green;">Analysis Complete!</div>
                    <div class="progress-bar-container">
                        <div class="progress-bar-fill" style="width: 100%; animation: none;"></div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
                time.sleep(0.8) 
                
                # 4. REMOVE LOADER
                loader_placeholder.empty()

                # --- PARSING & DISPLAY RESULTS ---
                risk_match = re.search(r"RISK_SCORE:\s*(\d+)", raw_text)
                fog_match = re.search(r"FOG_INDEX:\s*(.*)", raw_text)
                non_gaap_match = re.search(r"NON_GAAP_INTENSITY:\s*(.*)", raw_text)
                future_match = re.search(r"FUTURE_FOCUS:\s*(.*)", raw_text)
                
                verdict_match = re.search(r"\[VERDICT\]\s*(.*)", raw_text)
                headline_match = re.search(r"\[HEADLINE\]\s*(.*)", raw_text)
                
                # Safe Defaults
                risk_score = int(risk_match.group(1)) if risk_match else 50
                fog_index = fog_match.group(1).strip() if fog_match else "Medium"
                non_gaap = non_gaap_match.group(1).strip() if non_gaap_match else "Medium"
                future_focus = future_match.group(1).strip() if future_match else "Neutral"
                
                verdict = verdict_match.group(1).strip() if verdict_match else "Neutral"
                headline = headline_match.group(1).strip() if headline_match else "Analysis Complete"
                analysis_text = raw_text.split("[ANALYSIS]")[-1].strip()

                # --- UI DASHBOARD ---
                
                # Header
                st.markdown(f"## {headline}")
                st.caption(f"AI Verdict: {verdict.upper()}")
                
                # Metrics
                m1, m2, m3, m4 = st.columns(4)
                with m1: st.metric("Non-GAAP Intensity", non_gaap, help="High reliance on 'Adjusted' numbers is a red flag.")
                with m2: st.metric("Future Sentiment", future_focus, delta_color="normal" if future_focus=="Positive" else "inverse")
                with m3: st.metric("CEO Fog Index", fog_index, help="High = Confusing/Evasive Language")
                with m4: st.metric("Transcript Size", f"{len(text)/1000:.1f}k chars")
                
                st.markdown("---")

                # Layout
                col_left, col_right = st.columns([1, 2])
                with col_left:
                    st.markdown("#### ⚠️ Risk Meter")
                    st.plotly_chart(create_gauge(risk_score), width="stretch")
                    with st.container(border=True):
                        st.markdown("**What this means:**")
                        if risk_score > 75:
                            st.error("Management is evasive. High probability of downside.")
                        elif risk_score < 30:
                            st.success("Management is confident. Execution risk is low.")
                        else:
                            st.warning("Mixed signals. Monitor next quarter closely.")

                with col_right:
                    tab1, tab2 = st.tabs(["📝 Key Findings", "🔍 Raw Analysis"])
                    with tab1: st.markdown(analysis_text)
                    with tab2: st.text_area("Raw AI Output", raw_text, height=400)

            except Exception as e:
                loader_placeholder.empty() # Clear loader if error
                st.error(f"Analysis Error: {e}")