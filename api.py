from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
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


class StudentInput(BaseModel):
    hours: float


@app.get("/")
def home():
    return {"message": "Student Marks Predictor API is running"}


@app.get("/about")
def about():
    return {"message": "This API predicts student marks based on study hours"}


@app.post("/predict")
def predict(data: StudentInput):
    hours = data.hours

    input_df = pd.DataFrame({
        "hours": [hours]
    })

    prediction = model.predict(input_df)

    predicted_marks = round(float(prediction[0]), 2)

    return {
        "study_hours": hours,
        "predicted_marks": predicted_marks
    }