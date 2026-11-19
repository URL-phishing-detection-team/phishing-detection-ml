
import streamlit as st
import re
from urllib.parse import urlparse

# PAGE CONFIG

st.set_page_config(
    page_title="LinkGuard | URL Security",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# DARK BACKGROUND

st.markdown("""
<style>
.stApp {
    background-color: #0B1120;
}

.footer {
    width: 100%;
    text-align: center;
    margin-top: 45px;
    padding-top: 20px;
    border-top: 1px solid #263449;
}

/* URL INPUT CONTAINER */
div[data-testid="stForm"] {
    background-color: #151E2E;
    border: 1px solid #263449;
    border-radius: 16px;
    padding: 22px;
    margin-top: 18px;
}

/* URL INPUT */
div[data-testid="stTextInput"] input {
    background-color: #0B1120 !important;
    color: #F1F5F9 !important;
    border: 1px solid #334155 !important;
    border-radius: 10px !important;
}

/* INPUT LABEL */
div[data-testid="stTextInput"] label {
    color: #CBD5E1 !important;
}

/* FORM BUTTON */
div[data-testid="stFormSubmitButton"] button {
    background-color: #147F73 !important;
    color: white !important;
    border-radius: 10px !important;
    border: none !important;
    font-weight: 600 !important;
}

div[data-testid="stFormSubmitButton"] button:hover {
    background-color: #10695F !important;
}

</style>

</style>
""", unsafe_allow_html=True)

# CUSTOM CSS

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&display=swap');

html, body, [class*="css"] {
    font-family: 'DM Sans', sans-serif;
}

.stApp {
    background-color: #0B1120;
    color: #E5E7EB;
}

.block-container {
    max-width: 1150px;
    padding-top: 2rem;
    padding-bottom: 3rem;
}

header {
    visibility: hidden;
}

#MainMenu {
    visibility: hidden;
}

footer {
    visibility: hidden;
}

/* Header */
.brand {
    display: flex;
    align-items: center;
    gap: 12px;
    margin-bottom: 35px;
}

.brand-icon {
    background: #123B4A;
    color: white;
    width: 46px;
    height: 46px;
    border-radius: 14px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 23px;
}

.brand-name {
    font-size: 22px;
    font-weight: 700;
    color: #F1F5F9;
    letter-spacing: -0.5px;
}

.brand-caption {
    color: #8190A5;
    font-size: 12px;
    margin-top: -2px;
}

/* Hero */
.hero-label {
    color: #138779;
    font-size: 12px;
    font-weight: 700;
    letter-spacing: 1.8px;
    margin-bottom: 12px;
}

.hero-title {
    font-size: 42px;
    font-weight: 700;
    line-height: 1.2;
    letter-spacing: -1.5px;
    color: #F1F5F9;
}

.hero-description {
    color: #75849A;
    font-size: 15px;
    line-height: 1.8;
    max-width: 650px;
    margin-top: 14px;
    margin-bottom: 30px;
}

/* Cards */
.panel {
    background: #151E2E;
    border: 1px solid #263449;
    border-radius: 18px;
    padding: 26px;
    box-shadow: 0 5px 20px rgba(0, 0, 0, 0.15);
}

.panel-title {
    color: #E5E7EB;
    font-size: 17px;
    font-weight: 700;
    margin-bottom: 5px;
}

.panel-description {
    color: #94A3B8;
    font-size: 13px;
    margin-bottom: 22px;
}

/* Input */
.stTextInput label {
    color: #53657C !important;
    font-size: 13px !important;
    font-weight: 600 !important;
}

.stTextInput input {
    background-color: #0F172A !important;
    color: #F1F5F9 !important;
    border: 1px solid #334155 !important;
    border-radius: 10px !important;
    min-height: 48px;
}

.stTextInput input:focus {
    border-color: #14B8A6 !important;
    box-shadow: 0 0 0 2px rgba(20, 184, 166, 0.15) !important;
}

/* Button */
 {
    background: #147F73;
    color: white;
    border: none;
    border-radius: 10px;
    min-height: 46px;
    font-weight: 600;
    transition: 0.2s;
}


.stButton button,
.stFormSubmitButton button {
    background-color: #147F73 !important;
    color: #FFFFFF !important;
    border: none !important;
    border-radius: 10px !important;
    min-height: 48px;
    font-weight: 600;
}

.stButton button:hover,
.stFormSubmitButton button:hover {
    background-color: #10695F !important;
    color: #FFFFFF !important;
}

.small-label {
    color: #8795A8;
    font-size: 11px;
    font-weight: 700;
    letter-spacing: 1px;
}

.footer {
    width: 100%;
    text-align: center;
    margin-top: 45px;
    padding-top: 20px;
    border-top: 1px solid #263449;
}

/*LINKGUARD BACKGROUND*/
.stApp {
    background-color: #0B1120 !important;
    background-image:
        radial-gradient(
            circle at 5% 15%,
            rgba(20, 127, 115, 0.16),
            transparent 30%
        ),
        radial-gradient(
            circle at 95% 75%,
            rgba(59, 130, 246, 0.12),
            transparent 32%
        ),
        linear-gradient(
            rgba(255,255,255,0.025) 1px,
            transparent 1px
        ),
        linear-gradient(
            90deg,
            rgba(255,255,255,0.025) 1px,
            transparent 1px
        );

    background-size:
        auto,
        auto,
        40px 40px,
        40px 40px;
}

/*MAKE CONTENT WIDER*/
.block-container {
    max-width: 1200px !important;
    padding-left: 3rem !important;
    padding-right: 3rem !important;
}

/*CARD EFFECT*/
div[data-testid="stForm"],
.panel {
    box-shadow: 0 8px 30px rgba(0, 0, 0, 0.18);
}

/*ANALYSIS RESULT*/
.result-card {
    background: linear-gradient(
        135deg,
        #151E2E,
        #111827
    );
    border: 1px solid #263449;
    border-radius: 18px;
    padding: 25px;
    margin-top: 25px;
}

.result-header {
    display: flex;
    align-items: center;
    gap: 12px;
    margin-bottom: 20px;
}

.result-title {
    font-size: 20px;
    font-weight: 700;
    color: #F1F5F9;
}

.result-subtitle {
    color: #94A3B8;
    font-size: 13px;
}

.status-badge {
    display: inline-block;
    padding: 6px 12px;
    border-radius: 20px;
    background-color: rgba(20, 127, 115, 0.15);
    color: #2DD4BF;
    border: 1px solid rgba(45, 212, 191, 0.25);
    font-size: 12px;
    font-weight: 600;
}

.result-divider {
    border-top: 1px solid #263449;
    margin: 20px 0;
}

.metric-box {
    background-color: #0B1120;
    border: 1px solid #263449;
    border-radius: 12px;
    padding: 18px;
}

.metric-label {
    color: #94A3B8;
    font-size: 13px;
}

.metric-value {
    color: #F1F5F9;
    font-size: 22px;
    font-weight: 700;
    margin-top: 8px;
}

.result-description {
    color: #CBD5E1;
    font-size: 14px;
    line-height: 1.7;
}

</style>
""", unsafe_allow_html=True)

# HEADER

st.markdown("""
<div class="brand">
    <div class="brand-icon">🛡️</div>
    <div>
        <div class="brand-name">LinkGuard</div>
        <div class="brand-caption">Website Security Analyzer</div>
    </div>
</div>
""", unsafe_allow_html=True)

# HERO

st.markdown("""
<div class="hero-label">URL SECURITY ANALYSIS</div>

<div class="hero-title">
    Browse with confidence.<br>
    Check before you click.
</div>

<div class="hero-description">
    Analyze a website URL to help identify potential phishing threats.
    LinkGuard provides a security assessment and useful insights
    to help you make safer browsing decisions.
</div>
""", unsafe_allow_html=True)

# URL ANALYSIS FORM

st.markdown("""
<div class="panel">
    <div class="panel-title">Analyze a website</div>
    <div class="panel-description">
        Enter the URL you want to check below.
    </div>
</div>
""", unsafe_allow_html=True)

with st.form("url_analysis_form"):
    input_url = st.text_input(
        "Website URL",
        placeholder="https://example.com",
        help="Enter the complete website address."
    )

    submitted = st.form_submit_button(
        "Analyze URL  →",
        use_container_width=True
    )

# URL VALIDATION

def is_valid_url(url):
    try:
        url = url.strip()

        if not url:
            return False

        if not re.match(r"^https?://", url, re.IGNORECASE):
            url = "https://" + url

        parsed = urlparse(url)

        return (
            parsed.scheme in ["http", "https"]
            and bool(parsed.hostname)
            and "." in parsed.hostname
            and " " not in parsed.hostname
        )

    except Exception:
        return False


# RESULT AREA

if submitted:
    if not input_url.strip():
        st.warning("Please enter a URL first.")

    elif not is_valid_url(input_url):
        st.error("Invalid URL. Please enter a valid website address.")

    else:
        st.markdown("""
        <div class="result-card">
            <div class="result-header">
                <div>
                    <div class="result-title">Analysis Result</div>
                    <div class="result-subtitle">
                        URL submitted successfully
                    </div>
                </div>
            </div>
            <span class="status-badge">
                URL FORMAT VALID
            </span>
        </div>
        """, unsafe_allow_html=True)

        st.code(input_url)

        col1, col2 = st.columns(2)

        with col1:
            st.metric(
                label="Risk Score",
                value="—"
            )

        with col2:
            st.metric(
                label="Threat Status",
                value="Pending"
            )

        st.info(
            "The URL format is valid. However, the machine learning "
            "model has not been connected yet, so the phishing "
            "prediction is not available."
        )

# INFORMATION CARDS

st.markdown("<br>", unsafe_allow_html=True)

col1, col2, col3 = st.columns(3)

with col1:
    st.markdown("""
    <div class="panel">
        <div style="font-size:24px;">🔎</div>
        <div class="panel-title" style="margin-top:12px;">
            URL Analysis
        </div>
        <div class="panel-description" style="margin-bottom:0;">
            Examine website addresses to identify
            potential security concerns.
        </div>
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown("""
    <div class="panel">
        <div style="font-size:24px;">📊</div>
        <div class="panel-title" style="margin-top:12px;">
            Risk Assessment
        </div>
        <div class="panel-description" style="margin-bottom:0;">
            Display model-based risk scores
            after the ML model is integrated.
        </div>
    </div>
    """, unsafe_allow_html=True)

with col3:
    st.markdown("""
    <div class="panel">
        <div style="font-size:24px;">🔐</div>
        <div class="panel-title" style="margin-top:12px;">
            Safer Browsing
        </div>
        <div class="panel-description" style="margin-bottom:0;">
            Provide security guidance to help
            users avoid suspicious websites.
        </div>
    </div>
    """, unsafe_allow_html=True)

# FOOTER

st.markdown("""
<div class="footer">
    <div style="color:#F1F5F9; font-weight:700; font-size:14px;">
        LINKGUARD
    </div>
    <div style="color:#14B8A6; margin-top:6px; font-weight:600;">
        Stay alert. Browse safer.
    </div>
    <div style="color:#94A3B8; margin-top:6px; font-size:12px;">
        Phishing URL Detection · AI Security Project
    </div>
</div>
""", unsafe_allow_html=True)