from fastapi import FastAPI
from pydantic import BaseModel, field_validator, Field
from passlib.context import CryptContext
from jose import jwt
from jose.exceptions import JWTError
from datetime import datetime, timedelta

app = FastAPI()

SECRET_KEY = "your_secret_key"
ALGORITHM = "HS256"
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class User(BaseModel):
    username: str
    password: str = Field(..., max_length=200)
    
    @field_validator('password', mode='before')
    @classmethod
    def truncate_password(cls, v):
        if not v:
            return v
        if isinstance(v, str):
            password_bytes = v.encode('utf-8')[:72]
            return password_bytes.decode('utf-8', errors='ignore')
        return v

@app.get("/")
def home():
    return {"message": "API is working"}

@app.post("/signup")
def signup(user: User):
    return {"message": f"User {user.username} registered"}

print("Basic imports work!")