from fastapi import FastAPI, HTTPException, status, Depends, BackgroundTasks, Request
from fastapi_mail import FastMail, MessageSchema
from pydantic import EmailStr
from sqlalchemy.orm import Session
from app.database import get_db, Base , engine
from app.models import User,ProductVariant
from app.schemas import UserCreate, UserLogin,ResetPasswordRequest
from app.utils import hash_password, verify_password , pwd_context, create_reset_token, verify_reset_token
from app.auth import create_access_token
from app.send_email import send_email_background
import os
from fastapi.responses import RedirectResponse
from app.routers import profile_address
from fastapi.security import OAuth2PasswordBearer
from fastapi.middleware.cors import CORSMiddleware
from app.rate_limiter import setup_rate_limiting
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware


from dotenv import load_dotenv
load_dotenv()






oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")
from app.routers.google_auth import router as outh2_router
from app.routers.admin import router as admin_router
from app.routers.categoryroute import router as category_router
from app.routers.productroute import router as product_router
from app.routers.sorting_product import router as sorting_router
# from app.routers.cart import router as cart_router
from app.routers.webhook import router as webhook_router
from app.routers.payment import router as payment_router
from app.routers.orders import router as order_router
from app.routers.reviews import router as review_router
from app.routers.shipping_details import router as shippingdetails_router
from app.routers.refund import router as refund
from app.routers.website_logo import router as website_logo_router


app=FastAPI()

app.add_middleware(SessionMiddleware, secret_key=os.getenv("SESSION_SECRET_KEY"))
app.mount("/media", StaticFiles(directory="media"), name="media")
app.add_middleware(SessionMiddleware, secret_key=os.getenv("SECRET_KEY", "default_secret_key"))
templates = Jinja2Templates(directory="static/")

@app.get("/")
async def login(request: Request):

    # return templates.TemplateResponse("pages/login/login.html", {"request": request})
    return ("Successfully Login", {"request": request})  # 


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  
    allow_credentials=True,
    allow_methods=["*"],  
    allow_headers=["*"],  
)

setup_rate_limiting(app)
Base.metadata.create_all(bind=engine)

#register & login start
@app.post("/register/")
def register(user:UserCreate,background_tasks:BackgroundTasks,db:Session=Depends(get_db)):
    if user.password != user.confirm_password:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Passwords do not match")
    existing_user=db.query(User).filter((User.username==user.username) | (User.email == user.email)).first()
    if existing_user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,detail="Username or Email already exists")
    new_user=User(
        name=user.name,
        username=user.username,
        email=user.email,
        hashed_password=hash_password(user.password),
        is_active=True,
        role="user"
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    background_tasks.add_task(
            send_email_background,background_tasks,
            "Welcome to our platform!",
            new_user.email,
            {"title":"Welcome!","name":new_user.username}
        )
    return {"message":"User registered successfully"}

@app.post("/login/")
def login(user: UserLogin, db: Session = Depends(get_db)):
    db_user = db.query(User).filter(
        (User.username == user.username) | (User.email == user.username)
    ).first()
    if not db_user or not verify_password(user.password, db_user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials"
        )
    if not db_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Your account is inactive"
        )
    
    access_token = create_access_token(db_user.id,role=db_user.role)

    return {"access_token": access_token, "token_type": "bearer"}

#register & login end

#forgot password reset start
FRONTEND_BASE_URL = os.getenv("FRONTEND_URL", "http://127.0.0.1:5173")
from app.send_email import conf
@app.post("/forgot-password/")
async def forgot_password(email: EmailStr, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    """User ko password reset email send karega, token save nahi hoga"""
    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise HTTPException(status_code=404, detail="Email not found")
    reset_token = create_reset_token(user.id)
    reset_link = f"http://192.168.1.85:8000/reset-password?token={reset_token}"
    email_body = f"""
    <html>
    <body>
        <h3>Password Reset Request</h3>
        <p>Click the link below to reset your password:</p>
        <a href="{reset_link}">{reset_link}</a>
    </body>
    </html>
    """
    message = MessageSchema(
        subject="Reset Your Password",
        recipients=[email],
        body=email_body,
        subtype="html"
    )
    fm = FastMail(conf)
    background_tasks.add_task(fm.send_message, message)
    return {"message": "Password reset link sent to your email", "token": reset_token}
@app.get("/reset-password/")
async def validate_token(token: str):
    """Token validate karega aur frontend pe redirect karega"""
    if not token:
        raise HTTPException(status_code=400, detail="Token is required")
    frontend_url = f"{"http://localhost:5173"}/reset-password?token={token}"
    return RedirectResponse(url=frontend_url)
@app.post("/reset-password/")
async def reset_password(data: ResetPasswordRequest, db: Session = Depends(get_db)):
    user_id = verify_reset_token(data.token)
    if not user_id:
        raise HTTPException(status_code=400, detail="Invalid or expired token")

    if data.new_password != data.confirm_password:
        raise HTTPException(status_code=400, detail="Passwords do not match")

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    user.hashed_password = hash_password(data.new_password)
    db.add(user)
    db.commit()

    return {"message": "Password updated successfully"}

#forgot password reset end

# Routers  

app.include_router(outh2_router)
app.include_router(profile_address.router, prefix="/user", tags=["User Profile & Address"])
app.include_router(admin_router)
app.include_router(website_logo_router)
app.include_router(product_router)
app.include_router(sorting_router)
app.include_router(category_router)
app.include_router(review_router)
# app.include_router(cart_router)
app.include_router(order_router)
app.include_router(shippingdetails_router)
app.include_router(payment_router)
app.include_router(webhook_router)
app.include_router(refund)