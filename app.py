
import streamlit as st
import re
from pathlib import Path
import json

import joblib
import pandas as pd

from utils import (
    FEATURE_NAMES,
    extract_url_features,
    features_as_dict,
    validate_url_input,
)

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
        width="stretch"
    )

# MODEL

BASE_DIR = Path(__file__).parent


@st.cache_resource
def load_artifacts():
    json_path = BASE_DIR / "models" / "phishing_model.json"
    if json_path.exists():
        from xgboost import XGBClassifier
        model = XGBClassifier()
        model.load_model(str(json_path))
    else:
        model = joblib.load(BASE_DIR / "models" / "phishing_model.pkl")
    scaler = joblib.load(BASE_DIR / "models" / "scaler.pkl")
    with open(BASE_DIR / "models" / "config.json") as f:
        config = json.load(f)
    return model, scaler, config


def predict_url(url):
    """Return (risk score 0-1, is_phishing, threshold)."""
    model, scaler, config = load_artifacts()
    x = pd.DataFrame([extract_url_features(url)], columns=FEATURE_NAMES)
    risk = float(model.predict_proba(scaler.transform(x))[0, 1])
    return risk, risk >= config["threshold"], config["threshold"]


def notable_characteristics(url):
    """Simple rules that point out suspicious traits of the URL (not model internals)."""
    f = features_as_dict(url)
    notes = []
    if f["has_ip"]:
        notes.append("The address uses an IP address instead of a domain name.")
    if f["is_shortened"]:
        notes.append("The link uses a URL shortener, which hides the real destination.")
    if f["count_at"] > 0:
        notes.append("The URL contains an '@' character, which can disguise the real host.")
    if f["has_sensitive_word"]:
        notes.append("The URL contains sensitive words such as login, verify, account, or secure.")
    if f["subdomain_count"] >= 3:
        notes.append("The URL has many subdomains, a common trick to imitate trusted sites.")
    if f["count_hyphen"] >= 3:
        notes.append("The URL contains many hyphens.")
    if f["url_length"] > 75:
        notes.append("The URL is unusually long.")
    return notes


# RESULT AREA

if submitted:
    valid, message = validate_url_input(input_url)

    if not valid:
        st.error(message)

    else:
        try:
            risk, is_phishing, threshold = predict_url(input_url)
        except FileNotFoundError:
            st.error("Model files not found. Run `python train_model.py` first.")
            st.stop()

        st.markdown("""
        <div class="result-card">
            <div class="result-title">Analysis Result</div>
            <div class="result-subtitle">Prediction from the trained model</div>
        </div>
        """, unsafe_allow_html=True)

        st.code(input_url)

        col1, col2 = st.columns(2)
        with col1:
            st.metric(label="Risk Score", value=f"{risk:.0%}")
        with col2:
            st.metric(
                label="Threat Status",
                value="PHISHING" if is_phishing else "SAFE",
            )
        st.progress(min(max(risk, 0.0), 1.0))

        notes = notable_characteristics(input_url)

        if is_phishing:
            st.error(
                "This URL is classified as **phishing**. "
                "Do not open it or enter any credentials."
            )
            st.markdown("**Recommended actions**")
            st.markdown(
                "- Do not click the link or enter a username, password, PIN, or OTP.\n"
                "- Open the official website by typing its address yourself.\n"
                "- If you already entered credentials, change your password immediately.\n"
                "- Report the link to the impersonated service or your IT/security team."
            )
        else:
            st.success(
                "This URL is classified as **safe** by the model. "
                "No strong phishing pattern was found."
            )
            st.markdown("**Recommended actions**")
            st.markdown(
                "- Stay alert: the model only checks the URL text, not the page content.\n"
                "- Check that the domain matches the service you intend to visit.\n"
                "- Never share OTP or passwords through links you received unexpectedly."
            )

        if notes:
            st.markdown("**Notable URL characteristics**")
            for note in notes:
                st.markdown(f"- {note}")

        with st.expander("Extracted features"):
            st.dataframe(
                pd.DataFrame(
                    list(features_as_dict(input_url).items()),
                    columns=["Feature", "Value"],
                ),
                hide_index=True,
            )

        st.caption(
            f"The risk score is the model's estimated probability. "
            f"URLs with a score of {threshold:.0%} or higher are flagged as phishing. "
            "This is an estimate, not a guarantee."
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
            Display a model-based risk score
            for every analyzed URL.
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