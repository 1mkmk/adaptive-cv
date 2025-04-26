from fastapi import APIRouter, Depends, HTTPException, status, Request, Response
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.user import User
from app.auth.oauth import (
    create_access_token, 
    verify_google_token,
    get_current_user,
    GOOGLE_CLIENT_ID,
    GOOGLE_CLIENT_SECRET
)
import os
import httpx
from urllib.parse import quote
import logging

# Setup logging
logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/auth",
    tags=["authentication"],
)

# Frontend URL for redirecting after authentication
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:3000")

@router.get("/google/authorize")
async def authorize_google():
    """Redirect to Google OAuth consent screen"""
    
    # Define OAuth parameters
    redirect_uri = f"{os.getenv('API_BASE_URL', 'http://localhost:8000')}/auth/google/callback"
    scope = "email profile"
    
    # Construct URL
    auth_url = (
        "https://accounts.google.com/o/oauth2/auth"
        f"?response_type=code"
        f"&client_id={GOOGLE_CLIENT_ID}"
        f"&redirect_uri={quote(redirect_uri)}"
        f"&scope={quote(scope)}"
        f"&access_type=offline"
    )
    
    return RedirectResponse(auth_url)

@router.get("/google/callback")
async def google_callback(code: str, request: Request, db: Session = Depends(get_db)):
    """Handle callback from Google OAuth"""
    try:
        # Exchange code for token
        redirect_uri = f"{os.getenv('API_BASE_URL', 'http://localhost:8000')}/auth/google/callback"
        token_url = "https://oauth2.googleapis.com/token"
        
        # Prepare token request
        data = {
            "code": code,
            "client_id": GOOGLE_CLIENT_ID,
            "client_secret": GOOGLE_CLIENT_SECRET,
            "redirect_uri": redirect_uri,
            "grant_type": "authorization_code"
        }
        
        # Make token request
        async with httpx.AsyncClient() as client:
            response = await client.post(token_url, data=data)
            token_data = response.json()
        
        if "error" in token_data:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"OAuth error: {token_data['error']}"
            )
        
        # Verify ID token to get user info
        id_token = token_data["id_token"]
        user_info = verify_google_token(id_token)
        
        # Check if user exists
        user = db.query(User).filter(User.email == user_info["email"]).first()
        
        if not user:
            # Create new user
            logger.info(f"Creating new user with email: {user_info['email']}")
            user = User(
                email=user_info["email"],
                name=user_info["name"],
                picture=user_info["picture"],
                google_id=user_info["google_id"],
                locale=user_info["locale"]
            )
            db.add(user)
            db.commit()
            db.refresh(user)
        else:
            # Update existing user with latest Google info
            user.name = user_info["name"]
            user.picture = user_info["picture"]
            user.google_id = user_info["google_id"]
            db.commit()
            db.refresh(user)
        
        # Create access token
        access_token = create_access_token(data={"sub": user.email})
        
        # Set cookie and redirect to frontend
        response = RedirectResponse(url=f"{FRONTEND_URL}", status_code=303)  # Use 303 See Other
        # Usuń "Bearer " prefix dla spójności
        response.set_cookie(
            key="access_token",
            value=f"{access_token}",
            httponly=True,
            max_age=60*60*24*7,  # 7 days
            samesite="none",  # Pozwala na cross-site cookies
            secure=True  # Zawsze używaj secure dla samesite=none
        )
        # Dodaj logowanie
        logger.info(f"Setting cookie access_token with value length {len(access_token)}")
        
        return response
        
    except Exception as e:
        logger.error(f"Error in Google callback: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Authentication error: {str(e)}"
        )

@router.get("/logout")
async def logout_get(response: Response):
    """Handle user logout by clearing the authentication cookie"""
    response = RedirectResponse(url=f"{FRONTEND_URL}")
    response.delete_cookie(
        key="access_token",
        path="/",
        secure=False,  # Set to True in production with HTTPS
        httponly=True,
        samesite="lax"
    )
    logger.info("User logged out (GET method)")
    return response

@router.post("/logout")
async def logout_post(response: Response):
    """
    Endpoint for logging out the current user
    Clears the access_token cookie
    """
    # Clear the cookie by setting it to empty with immediate expiration
    response.delete_cookie(
        key="access_token",
        path="/",
        secure=False,  # Set to True in production with HTTPS
        httponly=True,
        samesite="lax"
    )
    logger.info("User logged out (POST method)")
    return {"message": "Successfully logged out"}

@router.get("/guest")
async def login_as_guest(db: Session = Depends(get_db)):
    """Create a guest user session"""
    # Check if guest user exists
    guest_email = "guest@example.com"
    user = db.query(User).filter(User.email == guest_email).first()
    
    if not user:
        # Create new guest user
        user = User(
            email=guest_email,
            name="Guest User",
            locale="en",
            is_guest=True
        )
        db.add(user)
        db.commit()
        db.refresh(user)
    
    # Create access token
    access_token = create_access_token(data={"sub": user.email})
    
    # Set cookie and redirect to frontend
    response = RedirectResponse(url=f"{FRONTEND_URL}", status_code=303)
    response.set_cookie(
        key="access_token",
        value=f"{access_token}",  # Bez "Bearer " - to zostanie dodane przy odczycie
        httponly=True,
        max_age=60*60*24*7,  # 7 days
        samesite="none",  # Pozwala na cross-site cookies
        secure=True  # Zawsze używaj secure dla samesite=none
    )
    # Dodaj logowanie
    logger.info(f"Setting cookie access_token with value length {len(access_token)}")
    
    return response

@router.get("/environment")
async def get_environment():
    """Return the current environment (local or production)"""
    env = os.getenv("ENV", "local")
    # Dla uproszczenia, uznajemy że wszystko co nie jest "local" to "production"
    if env != "local":
        env = "production"
    return {
        "environment": env
    }

@router.get("/me")
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    """Return information about the currently authenticated user"""
    return {
        "id": current_user.id,
        "email": current_user.email,
        "name": current_user.name,
        "picture": current_user.picture,
        "locale": current_user.locale,
        "is_guest": current_user.is_guest
    }