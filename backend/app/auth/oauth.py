from fastapi import Depends, HTTPException, status, Request, Cookie
from fastapi.security import OAuth2AuthorizationCodeBearer
from typing import Optional
import os
import logging

# Setup logging
logger = logging.getLogger(__name__)

# Try to import Google OAuth libraries
try:
    from google.oauth2 import id_token
    from google.auth.transport import requests
    GOOGLE_AUTH_AVAILABLE = True
    logger.info("Google Auth libraries successfully imported")
except ImportError:
    GOOGLE_AUTH_AVAILABLE = False
    logger.warning("Google Auth libraries not available - using local mode only")
import os
from jose import JWTError, jwt
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from typing import Optional
from app.database import get_db
from app.models.user import User

# Security configurations
SECRET_KEY = os.getenv("SECRET_KEY", "4f0157c5c84d5a3daa5d0005f5db93c0b2e02b31d0eba048e4aa95337d36189a")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7  # 7 days
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")

oauth2_scheme = OAuth2AuthorizationCodeBearer(
    authorizationUrl="auth/google/authorize",
    tokenUrl="auth/google/callback"
)

# For local development and testing
ENVIRONMENT = os.getenv("ENV", "local")
LOCAL_TEST_USER = os.getenv("LOCAL_TEST_USER", "guest@example.com")

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def verify_token(token: str):
    try:
        logger.info(f"Verifying token: {token[:10]}...")
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            logger.info("Token verification failed: no email in payload")
            return None
        logger.info(f"Token verified for email: {email}")
        return email
    except JWTError as e:
        logger.info(f"Token verification failed: {str(e)}")
        return None

async def get_token(request: Request, access_token: Optional[str] = Cookie(None)):
    """Extract token from cookie or authorization header"""
    # Dodaj logowanie
    logger.info(f"Cookies: {request.cookies}")
    logger.info(f"Headers: {request.headers}")
    
    # Try to get token from cookie first
    if access_token:
        # Cookie nie ma prefiksu "Bearer "
        logger.info(f"Found access_token in cookie: length={len(access_token)}")
        return access_token
    
    # Try to get token from authorization header
    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.startswith("Bearer "):
        token = auth_header.replace("Bearer ", "")
        logger.info(f"Found token in Authorization header: length={len(token)}")
        return token
    
    # In local environment, create a mock token
    if ENVIRONMENT == "local":
        token = create_access_token(data={"sub": LOCAL_TEST_USER})
        logger.info(f"Created mock token for local environment: length={len(token)}")
        return token
    
    logger.info("No token found in request")
    return None

def get_current_user(request: Request, token: Optional[str] = Depends(get_token), db: Session = Depends(get_db)):
    # For local development without authentication
    if ENVIRONMENT == "local":
        # Auto-login as test user in local environment
        user = db.query(User).filter(User.email == LOCAL_TEST_USER).first()
        if user:
            return user
        
        # If no test user, create a guest user
        new_user = User(
            email=LOCAL_TEST_USER,
            name="Guest User",
            is_guest=True,
            locale="en"
        )
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        return new_user
    
    # Normal token verification for production
    if token:
        email = verify_token(token)
        if email:
            user = db.query(User).filter(User.email == email).first()
            if user:
                return user
    
    # If no valid token or user not found, raise error
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid authentication credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

def verify_google_token(token: str):
    # If Google Auth is not available, return an error
    if not GOOGLE_AUTH_AVAILABLE:
        logger.error("Attempted to verify Google token but Google Auth libraries are not available")
        raise HTTPException(
            status_code=501, 
            detail="Google authentication is not available in this environment"
        )
        
    try:
        # Verify the token with Google
        idinfo = id_token.verify_oauth2_token(token, requests.Request(), GOOGLE_CLIENT_ID)
        
        # Check issuer
        if idinfo["iss"] not in ["accounts.google.com", "https://accounts.google.com"]:
            raise ValueError("Invalid issuer")
        
        # Get user info
        return {
            "google_id": idinfo["sub"],
            "email": idinfo["email"],
            "name": idinfo.get("name", ""),
            "picture": idinfo.get("picture", ""),
            "locale": idinfo.get("locale", "en")
        }
    except Exception as e:
        logger.error(f"Error verifying Google token: {str(e)}")
        raise HTTPException(status_code=401, detail=f"Invalid Google token: {str(e)}")