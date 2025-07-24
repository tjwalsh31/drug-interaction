"""
Drug Interaction Explainer (Streamlit Frontend)
------------------------------------------------
This Streamlit app allows users to enter a list of medications and checks for possible drug interactions using an AI-powered backend.

How it works:
- Users enter medications (comma separated) in the text input field.
- When the 'Check Interactions' button is pressed, the app sends the list to a FastAPI backend at API_URL.
- The backend checks for drug interactions using RxNav and explains them using OpenAI.
- Results are displayed in a user-friendly format.

Key features:
- Input validation: Warns if no medications are entered.
- Error handling: Displays API errors and connection issues.
- Loading spinner: Shows while waiting for backend response.

Usage:
- Run the backend server first (FastAPI).
- Run this Streamlit app (e.g., `streamlit run app.py`).
- Enter medications and view interaction explanations.
"""

import streamlit as st
import requests
import re

API_URL = "http://localhost:8000/interactions"

st.title("Drug Interaction Explainer")

# --- Helper Functions ---
def parse_interactions(explanation):
    """
    Parse the explanation text into a list of interaction dicts with sections.
    - Unescapes asterisks so section headers are recognized
    - Handles the case where there are no interactions
    - Splits by '**Interaction' and then by single newlines for sections
    """
    explanation = explanation.replace(r"\*\*", "**")
    if explanation.strip().startswith('>'):
        # No interactions found
        return [{"severity": "info", "interaction": "", "what": "", "risks": "", "advice": "", "message": explanation.strip()}]
    interactions = []
    blocks = re.split(r"\n?\*\*Interaction", explanation)
    for block in blocks:
        block = block.strip()
        if not block:
            continue
        block = "**Interaction" + block if not block.startswith("**Interaction") else block
        sections = re.split(r"\n", block)
        inter = {"interaction": "", "severity": "", "what": "", "risks": "", "advice": "", "message": ""}
        for sec in sections:
            sec = sec.strip()
            if not sec:
                continue
            # Parse each section by its header
            if sec.startswith("**Interaction"):
                inter["interaction"] = re.sub(r"^\*\*Interaction ?\d+\*\*: ?", "", sec).strip()
            elif sec.startswith("**Severity**:"):
                inter["severity"] = re.sub(r"^\*\*Severity\*\*: ?", "", sec).strip()
            elif sec.startswith("**What happens**:"):
                inter["what"] = re.sub(r"^\*\*What happens\*\*: ?", "", sec).strip()
            elif sec.startswith("**Risks or symptoms**:"):
                inter["risks"] = re.sub(r"^\*\*Risks or symptoms\*\*: ?", "", sec).strip()
            elif sec.startswith("**Advice**:"):
                inter["advice"] = re.sub(r"^\*\*Advice\*\*: ?", "", sec).strip()
        interactions.append(inter)
    return interactions


def format_interaction_text(inter, emoji):
    """
    Format a single interaction for display in the colored box.
    - Shows severity (with emoji) at the top
    - Drug names below, bold and large
    - Each section (what, risks, advice) on its own line
    """
    if inter.get("message"):
        # Info message for 'no interactions'
        return f"<span style='font-size:1.15em; color:#f9f9f9'>{inter['message']}</span>"
    severity_md = f"<span style='font-size:1.35em; font-weight:700; color:#fff;'>{emoji} {inter['severity']}</span>"
    drug_names_md = f"<span style='font-size:1.25em; font-weight:700; color:#f9f9f9'><b>{inter['interaction']}</b></span>" if inter['interaction'] else ""
    what_md = f"<span style='font-size:1.05em;'><b>What happens:</b> {inter['what']}</span>" if inter['what'] else ""
    risks_md = f"<span style='font-size:1.05em;'><b>Risks or symptoms:</b> {inter['risks']}</span>" if inter['risks'] else ""
    advice_md = f"<span style='font-size:1.05em;'><b>Advice:</b> {inter['advice']}</span>" if inter['advice'] else ""
    return f"{severity_md}<br>{drug_names_md}<br>{what_md}<br>{risks_md}<br>{advice_md}"


def severity_box(severity, inter):
    """
    Display a single interaction in a modern, eye-catching colored box with accent bar and emoji.
    - Severity determines color and emoji
    - Uses HTML for custom styling
    """
    sev = severity.lower()
    if inter.get("message"):
        st.info(inter["message"])
        return
    # Set accent color and emoji by severity
    if "severe" in sev:
        accent = "#b71c1c"; emoji = "🛑"
    elif "moderate" in sev:
        accent = "#f9a825"; emoji = "⚠️"
    elif "mild" in sev:
        accent = "#388e3c"; emoji = "✅"
    else:
        accent = "#343a40"; emoji = "❓"
    box_bg = "#22272e"
    st.markdown(f"""
        <div style='border:2.5px solid {accent}; border-radius:12px; margin-bottom:18px; box-shadow:0 2px 8px rgba(0,0,0,0.08); background:{box_bg};'>
            <div style='height:12px; background:{accent}; border-top-left-radius:10px; border-top-right-radius:10px;'></div>
            <div style='padding:18px;'>
                {format_interaction_text(inter, emoji)}
            </div>
        </div>
    """, unsafe_allow_html=True)

# --- Main App Logic ---
meds_input = st.text_input("Enter your medications (comma separated):")

if st.button("Check Interactions"):
    if meds_input:
        # Split and clean input
        meds = [m.strip() for m in meds_input.split(",") if m.strip()]
        with st.spinner("Contacting AI for drug interaction explanation..."):
            try:
                response = requests.post(API_URL, json={"medications": meds})
                if response.status_code == 200:
                    explanation = response.json().get("explanation", "")
                    st.markdown("### Interaction Explanation")
                    interactions = parse_interactions(explanation)
                    if not interactions:
                        st.info("No interactions found.")
                    for inter in interactions:
                        severity_box(inter["severity"], inter)
                        st.markdown("---")  # Divider between interactions
                else:
                    st.error(f"API error: {response.text}")
            except Exception as e:
                st.error(f"Error connecting to backend: {e}")
    else:
        st.warning("Please enter at least one medication.")
