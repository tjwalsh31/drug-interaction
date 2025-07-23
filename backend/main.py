from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import os
import openai
from dotenv import load_dotenv
from typing import List

# Load the correct env file
load_dotenv("key.env")
openai.api_key = os.getenv("OPENAI_API_KEY")

app = FastAPI()

class MedsRequest(BaseModel):
    medications: List[str]

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

Format the response exactly like this:

**Interaction 1:** {{Drug A}} + {{Drug B}}  
- **Severity**: {{mild/moderate/severe}}  
- **What happens**: {{brief mechanism}}  
- **Risks or symptoms**: {{patient-friendly explanation}}  
- **Advice**: {{recommendation or safer alternative}}

If there are no known interactions, respond with:  
> “No known interactions were found between these medications. Always check with a doctor or pharmacist.”

Begin when ready.
"""
    return prompt

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
        return {"explanation": answer}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

