import os
import httpx
import urllib.parse
from uuid import uuid4
from datetime import date
from fastapi import APIRouter, Request, HTTPException, Depends
from fastapi.responses import RedirectResponse
from google.oauth2 import id_token
from google.auth.transport import requests
from sqlalchemy.orm import Session
from dotenv import load_dotenv
from passlib.context import CryptContext

from app.database import get_db
from app.models import User, UserProfile, UserRole  

load_dotenv()

router = APIRouter(prefix="/api/authentication", tags=["auth"])

GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")
FRONTEND_URL = os.getenv("FRONTEND_URL")
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str):
    return pwd_context.hash(password)


@router.get("/login")
async def login(request: Request):
    # redirect_uri = urllib.parse.quote(str(request.url_for('auth_callback')), safe="")
    # google_auth_url = (

    #     f"https://accounts.google.com/o/oauth2/auth?client_id={GOOGLE_CLIENT_ID}"
    #     f"&redirect_uri={redirect_uri}&response_type=code&scope=openid email profile"
    # )
    redirect_uri = urllib.parse.quote(str(request.url_for('auth_callback')), safe="")
    google_auth_url = (
        f"https://accounts.google.com/o/oauth2/auth?"
        f"client_id={GOOGLE_CLIENT_ID}"
        f"&redirect_uri={redirect_uri}"
        f"&response_type=code"
        f"&scope=openid email profile"
        f"&prompt=consent"
        f"&access_type=offline"
    )
    return RedirectResponse(url=google_auth_url)


@router.get("/callback")
async def auth_callback(code: str, request: Request, db: Session = Depends(get_db)):
    token_request_uri = "https://oauth2.googleapis.com/token"
    data = {
        'code': code,
        'client_id': GOOGLE_CLIENT_ID,
        'client_secret': GOOGLE_CLIENT_SECRET,
        'redirect_uri': request.url_for('auth_callback'),
        'grant_type': 'authorization_code',
    }

    async with httpx.AsyncClient() as client:
        response = await client.post(token_request_uri, data=data)
        response.raise_for_status()
        token_response = response.json()

    id_token_value = token_response.get('id_token')
    if not id_token_value:
        raise HTTPException(status_code=400, detail="Missing id_token in response.")

    try:
        id_info = id_token.verify_oauth2_token(id_token_value, requests.Request(), GOOGLE_CLIENT_ID)
        name = id_info.get('name')
        email = id_info.get('email')
        picture = id_info.get('picture')
        username = email.split('@')[0]  

        # 1. Check if user exists
        user = db.query(User).filter(User.email == email).first()
        if not user:
           
            user = User(
                name=name,
                username=username,
                email=email,
                hashed_password=hash_password(uuid4().hex),
                is_active=True,
                role=UserRole.user,
            )
            db.add(user)
            db.commit()
            db.refresh(user)

            # 3. Create user profile with dummy data
            profile = UserProfile(
                user_id=user.id,
                first_name=name.split(" ")[0],
                last_name=(name.split(" ")[1] if len(name.split(" ")) > 1 else "Unknown"),
                date_birth=date(2000, 1, 1),
                phone="0000000000",
                age=25,
                profile_picture=picture or None,
            )
            db.add(profile)
            db.commit()

        request.session['user_name'] = name

        if not FRONTEND_URL:
            raise HTTPException(status_code=500, detail="FRONTEND_URL is not defined in the environment variables.")
        # return RedirectResponse(url=f"{FRONTEND_URL}/welcome")
        return RedirectResponse(url=f"{response.url}/welcome?name={name}")

    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid id_token: {str(e)}")

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")
