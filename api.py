from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer
from pydantic import BaseModel
import joblib
import pandas as pd
from passlib.context import CryptContext
from jose import jwt, JWTError
from datetime import datetime, timedelta, timezone
from pathlib import Path
from fastapi.responses import FileResponse
import os
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

try:
    from database import users_collection, predictions_collection
    DB_AVAILABLE = True
except Exception as e:
    print(f"Database connection failed: {e}")
    DB_AVAILABLE = False
    users_collection = None
    predictions_collection = None

try:
    model = joblib.load(BASE_DIR / "marks_model.joblib")
    MODEL_AVAILABLE = True
except Exception as e:
    print(f"Model loading failed: {e}")
    MODEL_AVAILABLE = False
    model = None

SECRET_KEY = os.getenv("SECRET_KEY", "fallback-secret-key-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

class User(BaseModel):
    username: str
    password: str

class StudentInput(BaseModel):
    hours: float

def truncate_password(password: str) -> str:
    """Truncate password to 72 bytes for bcrypt compatibility"""
    pwd_bytes = password.encode('utf-8')
    if len(pwd_bytes) > 72:
        pwd_bytes = pwd_bytes[:72]
    return pwd_bytes.decode('utf-8', errors='ignore')

def create_access_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
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

@app.get("/health")
def health_check():
    return {
        "status": "ok",
        "database": DB_AVAILABLE,
        "model": MODEL_AVAILABLE
    }

@app.post("/signup")
def signup(user: User):
    if not DB_AVAILABLE:
        return {"error": "Database not available"}
    
    try:
        existing_user = users_collection.find_one({"username": user.username})
        if existing_user:
            return {"error": "User already exists"}
        
        safe_password = truncate_password(user.password)
        hashed_password = pwd_context.hash(safe_password)

        users_collection.insert_one({
            "username": user.username,
            "password": hashed_password
        })

        return {"message": "Signup successful"}
    except Exception as e:
        print(f"Signup error: {e}")
        return {"error": str(e)}

@app.post("/login")
def login(user: User):
    if not DB_AVAILABLE:
        return {"error": "Database not available"}
    
    try:
        found_user = users_collection.find_one({"username": user.username})
        if not found_user:
            return {"error": "User not found"}
        
        safe_password = truncate_password(user.password)
        
        if not pwd_context.verify(safe_password, found_user["password"]):
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
        print(f"Login error: {e}")
        return {"error": str(e)}

@app.post("/predict")
def predict(data: StudentInput, current_user: str = Depends(get_current_user)):
    if not MODEL_AVAILABLE:
        return {"error": "Model not available"}
    
    try:
        hours = data.hours
        prediction = model.predict(pd.DataFrame({"hours": [hours]}))
        predicted_marks = round(float(prediction[0]), 2)

        if DB_AVAILABLE:
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
    if not DB_AVAILABLE:
        return {"error": "Database not available"}
    
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
    if not DB_AVAILABLE:
        return {"error": "Database not available"}
    
    try:
        if username != current_user:
            raise HTTPException(status_code=403, detail="Not authorized")
        
        predictions_collection.delete_many({"username": username})
        return {"message": "History cleared"}
    except Exception as e:
        return {"error": str(e)}
