import pandas as pd
from sklearn.linear_model import LinearRegression
import joblib

data = {
    "hours": [1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
    "marks": [20, 30, 40, 50, 60, 70, 80, 90, 95, 100]
}

df = pd.DataFrame(data)

X = df[["hours"]]
y = df["marks"]

model = LinearRegression()
model.fit(X, y)

joblib.dump(model, "marks_model.joblib")

print("Model trained and saved as marks_model.joblib")