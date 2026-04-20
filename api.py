from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
import joblib
import pandas as pd
from sklearn.linear_model import LinearRegression
from database import users_collection, predictions_collection
from passlib.context import CryptContext
from jose import jwt, JWTError
from datetime import datetime, timedelta
from pathlib import Path
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from datetime import datetime
from fastapi.security import OAuth2PasswordBearer

import warnings
warnings.filterwarnings("ignore")

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

BASE_DIR = Path(__file__).resolve().parent

# Try to load existing model, if fails, train a new one
try:
    model = joblib.load(BASE_DIR / "marks_model.joblib")
except Exception as e:
    print(f"Failed to load model: {e}. Training new model...")
    
    # Training data
    data = {
        "hours": [1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
        "marks": [20, 30, 40, 50, 60, 70, 80, 90, 95, 100]
    }
    df = pd.DataFrame(data)
    X = df[["hours"]]
    y = df["marks"]
    
    model = LinearRegression()
    model.fit(X, y)
    
    # Save the model
    try:
        joblib.dump(model, BASE_DIR / "marks_model.joblib")
        print("New model trained and saved successfully")
    except Exception as save_error:
        print(f"Could not save model: {save_error}")

SECRET_KEY = "RAMTEJA123"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

security = HTTPBearer()

class User(BaseModel):
    username: str
    password: str

class StudentInput(BaseModel):
    hours: float

def create_access_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def get_current_user(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate token"
    )

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username = payload.get("sub")
        if username is None:
            raise credentials_exception
        return username
    except JWTError:
        raise credentials_exception

@app.get("/", include_in_schema=False)
def serve_frontend():
    return FileResponse(BASE_DIR / "index.html")

@app.post("/signup")
def signup(user: User):
    try:
        existing_user = users_collection.find_one({"username": user.username})

        if existing_user:
            return {"error": "User already exists"}
        
        
        hashed_password = pwd_context.hash(user.password)

        users_collection.insert_one({
            "username": user.username,
            "password": hashed_password
        })

        return {"message": "Signup successful"}
    
    except Exception as e:
        return {"error": str(e)}
    
@app.post("/login")
def login(user: User):
    try:
        users = list(users_collection.find({"username": user.username}))

        found_user = users[-1] if users else None

        if not found_user:
            return {"error": "User not found"}
        
        stored_password = found_user["password"]

        if not str(stored_password).startswith("$2"):
            return {"error": "Old user record found. Please signup again"}
        
        # Truncate password to 72 bytes for bcrypt
        password_bytes = user.password.encode('utf-8')[:72]
        if not pwd_context.verify(password_bytes, found_user["password"]):
            return {"error": "Invalid password"}
        
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": user.username},
            expires_delta=access_token_expires
        )
        
        return {
            "message": "Login successful",
            "access_token": access_token,
            "token_type": "bearer",
            "username": user.username
        }
    except Exception as e:
        return {"error": str(e)}
    
@app.post("/predict")
def predict(data: StudentInput, current_user: str = Depends(get_current_user)):
    try:
        hours = data.hours
        prediction = model.predict(pd.DataFrame({"hours": [hours]}))
        predicted_marks = round(float(prediction[0]), 2)

        predictions_collection.insert_one({
            "username": current_user,
            "hours": hours,
            "predicted_marks": predicted_marks
        })
        
        return {
            "study_hours": hours,
            "predicted_marks": predicted_marks
        }
    
    except Exception as e:
        return {"error": str(e)}
    
@app.get("/history/{username}")
def get_history(username: str, current_user: str = Depends(get_current_user)):
    try:
        if username != current_user:
            raise HTTPException(status_code=403, detail="Not authorized")
        
        data = list(predictions_collection.find(
            {"username": username},
            {"_id": 0}
        ))
        return {"history": data}
    except Exception as e:
        return {"error": str(e)}

@app.delete("/history/{username}")
def clear_history(username: str, current_user: str = Depends(get_current_user)):
    try:
        if username != current_user:
            raise HTTPException(status_code=403, detail="Not authorized")
        
        predictions_collection.delete_many({"username": username})
        return {"message": "History cleared"}
    except Exception as e:
        return {"error": str(e)}
    
