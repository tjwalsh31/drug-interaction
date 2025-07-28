from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import os
import openai
from dotenv import load_dotenv
from typing import List
import requests
import re

# Load the correct env file
load_dotenv("key.env")
openai.api_key = os.getenv("OPENAI_API_KEY")

app = FastAPI()

class MedsRequest(BaseModel):
    medications: List[str]

def get_rxcui(drug_name):
    """Get RxCUI code for a given drug"""
    url = f"https://rxnav.nlm.nih.gov/REST/rxcui.json?name={drug_name}"
    resp = requests.get(url)
    rxcui = resp.json().get("idGroup", {}).get("rxnormId", [])
    return rxcui[0] if rxcui else None

def get_interactions(rxcui_list):
    """Get interactions for a list of RxCUIs"""
    rxcuis = "+".join(rxcui_list)
    url = f"https://rxnav.nlm.nih.gov/REST/interaction/list.json?rxcuis={rxcuis}"
    resp = requests.get(url)
    if resp.status_code != 200:
        raise HTTPException(status_code=resp.status_code, detail="Error fetching interactions from RxNav")
    # Debugging to check response
    print(resp.json())
    return resp.json()

def build_prompt(meds: List[str]) -> str:
    meds_str = ", ".join(meds)
    prompt = f"""
You are a licensed clinical pharmacist tasked with explaining potential drug interactions to patients in plain English.

The patient has listed the following medications: {meds_str}

Your job is to:

1. Identify if there are any known drug interactions among these medications.
2. For each interaction:
   - Describe what happens (the mechanism or risk)
   - Rate the severity as mild, moderate, or severe
   - Explain possible symptoms or consequences the patient might experience
3. Use simple, clear language without medical jargon.
4. If possible, suggest a safer alternative medication or precautions (e.g., spacing doses, consulting a doctor).
5. If any medication name is unclear or unknown, politely mention it and recommend verifying with a healthcare professional.
6. USE RXCUIS API FOR ACCURACY.

Format the response STRICTLY like this :

**Interaction 1**: {{Drug A}} + {{Drug B}}

**Severity**: {{mild/moderate/severe}}

**What happens**: {{brief mechanism}}

**Risks or symptoms**: {{patient-friendly explanation}}

**Advice**: {{recommendation or safer alternative}}

If there are no known interactions, respond with:
>No known interactions were found between these medications. Always check with a doctor or pharmacist.

Do not use extra Markdown, code blocks, or HTML. Do not add extra whitespace or blank lines. Do not use bullet points. Keep the format strict and consistent.

You must capitalize the first letter of each medication.

Begin when ready.
"""
    return prompt

def uppercase_severity(text):
    # Replace '**Severity**: value' with uppercase value
    def repl(match):
        return f"**Severity**: {match.group(1).upper()}"
    return re.sub(r"\*\*Severity\*\*: (mild|moderate|severe|unknown)", repl, text, flags=re.IGNORECASE)

def capitalize_medications(text):
    # Capitalize the first letter of each medication in '**Interaction N**: ...' line
    def repl(match):
        drugs = match.group(2)
        # Split by +, strip, capitalize first letter of each drug
        drugs_cap = ' + '.join([d.strip().capitalize() for d in drugs.split('+')])
        return f"**Interaction {match.group(1)}**: {drugs_cap}"
    return re.sub(r"\*\*Interaction (\d+)\*\*: ([^\n]+)", repl, text)

@app.post("/interactions")
async def get_interactions(request: MedsRequest):
    prompt = build_prompt(request.medications)

    try:
        response = openai.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a helpful clinical pharmacist."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=600,
            temperature=0.7
        )
        answer = response.choices[0].message.content.strip()
        # Post-process: remove extra blank lines, ensure double newlines between sections
        answer = re.sub(r"\n{3,}", "\n\n", answer)
        answer = re.sub(r" +", " ", answer)
        answer = uppercase_severity(answer)
        answer = capitalize_medications(answer)
        return {"explanation": answer}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

