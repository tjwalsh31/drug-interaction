import streamlit as st
import requests

API_URL = "http://localhost:8000/interactions"

st.title("Drug Interaction Explainer")

meds_input = st.text_input("Enter your medications (comma separated):")

if st.button("Check Interactions"):
    if meds_input:
        meds = [m.strip() for m in meds_input.split(",") if m.strip()]
        with st.spinner("Contacting AI for drug interaction explanation..."):
            try:
                response = requests.post(API_URL, json={"medications": meds})
                if response.status_code == 200:
                    explanation = response.json().get("explanation", "")
                    st.markdown("### Interaction Explanation")
                    st.markdown(explanation)
                else:
                    st.error(f"API error: {response.text}")
            except Exception as e:
                st.error(f"Error connecting to backend: {e}")
    else:
        st.warning("Please enter at least one medication.")
