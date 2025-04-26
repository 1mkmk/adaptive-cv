from functools import wraps
from fastapi import Depends, HTTPException, status
from typing import List, Optional
from sqlalchemy.orm import Session
from app.database import get_db
from app.auth.oauth import get_current_user
from app.models.user import User

def require_authentication(func):
    """
    Decorator to require authentication for endpoints.
    Adds current_user as a parameter to the endpoint function.
    """
    @wraps(func)
    async def wrapper(*args, **kwargs):
        # Get current_user from dependencies
        if 'current_user' not in kwargs:
            # Ensure current_user is always provided through dependencies
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Authentication decorator improperly applied - missing current_user dependency"
            )
        
        return await func(*args, **kwargs)
    
    # Add the current_user dependency to the endpoint
    if hasattr(func, '__signature__'):
        wrapper.__signature__ = func.__signature__
    if hasattr(func, '__annotations__'):
        wrapper.__annotations__ = func.__annotations__
    
    # Ensure the function has dependencies
    if not hasattr(wrapper, 'dependencies'):
        wrapper.dependencies = []
    
    # Add current_user dependency if not already present
    current_user_dependency = Depends(get_current_user)
    if current_user_dependency not in wrapper.dependencies:
        wrapper.dependencies.append(current_user_dependency)
    
    return wrapper

def require_non_guest(func):
    """
    Decorator to require non-guest authentication for endpoints.
    Prevents guest users from accessing certain endpoints.
    """
    @wraps(func)
    async def wrapper(*args, **kwargs):
        # Get current_user from kwargs
        current_user = kwargs.get('current_user')
        if not current_user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication required"
            )
        
        # Check if user is a guest
        if current_user.is_guest:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="This action is not available in guest mode. Please sign in with Google."
            )
        
        return await func(*args, **kwargs)
    
    # Apply the require_authentication decorator first
    wrapper = require_authentication(wrapper)
    return wrapper