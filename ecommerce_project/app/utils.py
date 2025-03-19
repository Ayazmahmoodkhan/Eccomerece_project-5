from passlib.context import CryptContext
import jwt
from datetime import datetime, timedelta
from passlib.context import CryptContext
ALGORITHM = "HS256"
SECRET_KEY = "e5f8a7d9c2b44e5db11a6e3f9f6b7c8d9a4e5f2a1b3c4d5e6f7a8b9c0d1e2f3"
pwd_context=CryptContext(schemes=["bcrypt"], deprecated="auto")
def hash_password(password:str)->str:
    return pwd_context.hash(password)
def verify_password(plain_password:str,hashed_password:str)->bool:
    return pwd_context.verify(plain_password,hashed_password)
def create_reset_token(user_id: int) -> str:
    """Generate reset token"""
    expire = datetime.utcnow() + timedelta(minutes=15)
    payload = {"sub": str(user_id), "exp": expire}
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

def verify_reset_token(token: str):
    """Verify reset token and return user ID"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return int(payload["sub"])
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None