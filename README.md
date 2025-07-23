# drug-interaction
To get it running:
Run backend:
/////////////////////////////////////////
cd backend
source venv/bin/activate       # activate venv again if needed
uvicorn main:app --reload
///////////////////////////////////////

Run frontend (in a separate terminal):
/////////////////////////////////////
cd frontend
source venv/bin/activate
streamlit run app.py
//////////////////////////////////////

NOTES:
backend runs on http://localhost:8000 (by default)
frontend runs on http://localhost:8501