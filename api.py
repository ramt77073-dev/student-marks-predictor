from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import joblib
import pandas as pd

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

model = joblib.load("marks_model.joblib")

@app.get("/")
def home():
    return {"message": "Student Marks Predictor API is running"}

@app.get("/about")
def about():
    return {"message": "This API predicts student marks based  on study hours"}

@app.post("/predict")
def predict(data: dict):
    hours = data["hours"]

    prediction = model.predict(pd.DataFrame({"hours": [hours]}))

    predicted_marks = round(float(prediction[0]), 2)

    return {
        "study_hours": hours,
        "predicted_marks": predicted_marks
    }