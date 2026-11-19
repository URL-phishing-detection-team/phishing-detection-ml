# LINKGUARD
### Stay alert. Browse safer.

**LinkGuard** is an AI-based phishing URL detection project designed to help users identify potentially suspicious website links.

This application is developed using Python and Streamlit. Users can enter a website URL and check whether the URL format is valid before the machine learning model is integrated.

> **Project Status:** The web application is currently under development. Machine learning prediction is not yet available.

## Features

- URL input and validation
- Invalid URL detection
- Interactive web interface using Streamlit
- Dark-themed cybersecurity dashboard
- Machine learning integration (in progress)

## Technologies Used

- Python
- Streamlit
- Pandas
- Scikit-learn
- Joblib
- NumPy

## Project Structure

```text
phishing_detection/
│
├── app.py
├── requirements.txt
├── README.md
│
└── models/
    └── (model files will be added)
```

## Installation

1. Clone this repository:

```bash
git clone https://github.com/USERNAME/phishing_detection.git
```

2. Navigate to the project folder:

```bash
cd phishing_detection
```

3. Install the required libraries:

```bash
pip install -r requirements.txt
```

## How to Run

Run the application using:

```bash
streamlit run app.py
```

Then open the local URL provided by Streamlit in your browser.

## Current Development

The current version supports URL input and basic validation.

The machine learning model, risk score, and phishing detection results will be added after model integration.

## Disclaimer

LinkGuard is an academic project developed for educational purposes. The current version does not provide actual phishing detection predictions.

---

**LinkGuard — Phishing URL Detection | AI Security Project**
