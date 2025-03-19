from datetime import timedelta, datetime
import jwt
from jose import JWTError, jwt

SECRET_KEY = "e5f8a7d9c2b44e5db11a6e3f9f6b7c8d9a4e5f2a1b3c4d5e6f7a8b9c0d1e2f3"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRES_MINUTES = 60

def create_access_token(data: dict, expires_delta: timedelta = None):
    to_encode = {"sub": data.get("sub")} 
    expire = datetime.utcnow() + (expires_delta if expires_delta else timedelta(minutes=ACCESS_TOKEN_EXPIRES_MINUTES))
    
    to_encode.update({"exp": expire})  # Update `to_encode` without overwriting
    
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

