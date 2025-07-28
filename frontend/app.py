"""
Drug Interaction Explainer (Streamlit Frontend)
------------------------------------------------
This Streamlit app allows users to:
1. Enter a list of medications and check for possible drug interactions using an AI-powered backend.
2. Get detailed pharmaceutical information about individual drugs including dosage, side effects, etc.

How it works:
- Users can switch between "Drug Interactions" and "Drug Information" tabs.
- Interaction tab: Enter medications (comma separated) and get interaction explanations.
- Drug Info tab: Enter a single drug and get comprehensive pharmaceutical information.
- Both tabs send requests to corresponding FastAPI backend endpoints.

Key features:
- Input validation: Warns if no medications are entered.
- Error handling: Displays API errors and connection issues.
- Loading spinner: Shows while waiting for backend response.
- Personalized dosing: Considers pregnancy status, height, and weight for dosage recommendations.

Usage:
- Run the backend server first (FastAPI).
- Run this Streamlit app (e.g., `streamlit run app.py`).
- Choose your desired tab and enter medication information.
"""

import streamlit as st
import requests
import re

API_URL_INTERACTIONS = "http://localhost:8000/interactions"
API_URL_DRUG_INFO = "http://localhost:8000/drug-info"

st.title("Drug Information & Interaction Explainer")

# --- Disclaimer ---
st.markdown("""
<div style='background:#fff3cd; border-left:6px solid #f9a825; padding:12px 18px; border-radius:8px; margin-bottom:18px; color:#222;'>
<b>Disclaimer:</b> This is not medical advice from a doctor. Always consult your doctor before taking any medications.
</div>
""", unsafe_allow_html=True)

# --- Create Tabs ---
tab1, tab2 = st.tabs(["🔍 Drug Interactions", "💊 Drug Information"])

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
    blocks = re.split(r"\n\*\*Interaction", explanation)   
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

def parse_drug_info(explanation):
    """
    Parse the drug information text into structured sections.
    This function now handles multi-line sections properly.
    """
    explanation = explanation.replace(r"\*\*", "**")
    
    # Initialize the drug info dictionary
    drug_info = {"description": "", "uses": "", "side_effects": "", "dosage": "", "names": "", "pregnancy": "", "personalized_dose": ""}
    
    # Split by double asterisk headers
    sections = re.split(r'\*\*(Description|Uses|Side Effects|Dosage|Names|Pregnancy|Personalized Dose)\*\*:', explanation)
    
    # Process the sections
    for i in range(1, len(sections), 2):
        if i + 1 < len(sections):
            section_name = sections[i].lower().replace(" ", "_")
            section_content = sections[i + 1].strip()
            
            # Clean up the content - remove extra newlines but keep paragraph structure
            section_content = re.sub(r'\n\s*\n', ' ', section_content)
            section_content = re.sub(r'\n', ' ', section_content)
            section_content = section_content.strip()
            
            # Map section names to our dictionary keys
            if section_name == "description":
                drug_info["description"] = section_content
            elif section_name == "uses":
                drug_info["uses"] = section_content
            elif section_name == "side_effects":
                drug_info["side_effects"] = section_content
            elif section_name == "dosage":
                drug_info["dosage"] = section_content
            elif section_name == "names":
                drug_info["names"] = section_content
            elif section_name == "pregnancy":
                drug_info["pregnancy"] = section_content
            elif section_name == "personalized_dose":
                drug_info["personalized_dose"] = section_content
    
    return drug_info

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

def format_drug_info_section(title, content, icon):
    """
    Format a drug information section in a styled box.
    """
    if not content:
        return
    
    st.markdown(f"""
        <div style='border:2px solid #4CAF50; border-radius:12px; margin-bottom:18px; background:#1e1e1e;'>
            <div style='height:8px; background:#4CAF50; border-top-left-radius:10px; border-top-right-radius:10px;'></div>
            <div style='padding:18px;'>
                <span style='font-size:1.25em; font-weight:700; color:#4CAF50;'>{icon} {title}</span><br>
                <span style='font-size:1.05em; color:#f9f9f9; line-height:1.6;'>{content}</span>
            </div>
        </div>
    """, unsafe_allow_html=True)

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

# --- Drug Interactions Tab ---
with tab1:
    st.header("Check Drug Interactions")
    meds_input = st.text_input("Enter your medications (comma separated):")

    if st.button("Check Interactions", key="interactions_btn"):
        if meds_input:
            # Split and clean input
            meds = [m.strip() for m in meds_input.split(",") if m.strip()]
            with st.spinner("Contacting your pharmacist..."):
                try:
                    response = requests.post(API_URL_INTERACTIONS, json={"medications": meds})
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

# --- Drug Information Tab ---
with tab2:
    st.header("Get Drug Information")
    
    # Drug input
    drug_input = st.text_input("Enter a medication name:")
    
    # Personal information for dosage calculation
    st.subheader("Personal Information (for dosage recommendations)")
    
    col1, col2 = st.columns(2)
    with col1:
        height_feet = st.number_input("Height (feet)", min_value=3, max_value=8, value=5, step=1)
        height_inches = st.number_input("Height (inches)", min_value=0, max_value=11, value=7, step=1)
        is_pregnant = st.checkbox("Are you pregnant?")
    
    with col2:
        weight = st.number_input("Weight (lbs)", min_value=66, max_value=440, value=154, step=1)
        age = st.number_input("Age (years)", min_value=1, max_value=120, value=30, step=1)

    if st.button("Get Drug Information", key="drug_info_btn"):
        if drug_input:
            # Convert imperial to metric for backend calculations
            height_cm = (height_feet * 12 + height_inches) * 2.54
            weight_kg = weight * 0.453592
            
            personal_info = {
                "height": height_cm,
                "weight": weight_kg,
                "age": age,
                "is_pregnant": is_pregnant,
                "height_display": f"{height_feet}'{height_inches}\"",
                "weight_display": f"{weight} lbs"
            }
            
            with st.spinner("Gathering pharmaceutical information..."):
                try:
                    response = requests.post(API_URL_DRUG_INFO, json={
                        "medication": drug_input.strip(),
                        "personal_info": personal_info
                    })
                    if response.status_code == 200:
                        explanation = response.json().get("explanation", "")
                        st.markdown("### Drug Information")
                        
                        # Debug: Show raw response (you can remove this later)
                        with st.expander("Debug: Raw API Response"):
                            st.text(explanation)
                        
                        drug_info = parse_drug_info(explanation)
                        
                        # Debug: Show parsed sections (you can remove this later)
                        with st.expander("Debug: Parsed Sections"):
                            st.json(drug_info)
                        
                        # Display each section with icons - only show if content exists
                        if drug_info["description"]:
                            format_drug_info_section("Description", drug_info["description"], "📋")
                        if drug_info["uses"]:
                            format_drug_info_section("Medical Uses", drug_info["uses"], "🎯")
                        if drug_info["names"]:
                            format_drug_info_section("Generic & Brand Names", drug_info["names"], "🏷️")
                        if drug_info["dosage"]:
                            format_drug_info_section("Standard Dosage", drug_info["dosage"], "💊")
                        if drug_info["personalized_dose"]:
                            format_drug_info_section("Personalized Dosage Recommendation", drug_info["personalized_dose"], "👤")
                        if drug_info["side_effects"]:
                            format_drug_info_section("Common Side Effects", drug_info["side_effects"], "⚠️")
                        
                        if is_pregnant and drug_info["pregnancy"]:
                            format_drug_info_section("Pregnancy Considerations", drug_info["pregnancy"], "🤱")
                        
                        # Fallback: if no sections were parsed, show raw response
                        if not any(drug_info.values()):
                            st.warning("Unable to parse response into sections. Showing raw response:")
                            st.text(explanation)
                            
                    else:
                        st.error(f"API error: {response.text}")
                except Exception as e:
                    st.error(f"Error connecting to backend: {e}")
        else:
            st.warning("Please enter a medication name.")