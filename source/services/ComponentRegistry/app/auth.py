"""OAuth2 authentication module for Resource Inventory Management API."""

import os
from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
import bcrypt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel


# Configuration from environment variables
SECRET_KEY = os.getenv("OAUTH2_SECRET_KEY", "your-secret-key-change-in-production")
ALGORITHM = os.getenv("OAUTH2_ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("OAUTH2_ACCESS_TOKEN_EXPIRE_MINUTES", "30"))
OAUTH2_ENABLED = os.getenv("OAUTH2_ENABLED", "false").lower() == "true"

# OAuth2 scheme
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token", auto_error=False)


class Token(BaseModel):
    """Token response model."""
    access_token: str
    token_type: str


class TokenData(BaseModel):
    """Token data model."""
    username: Optional[str] = None


class User(BaseModel):
    """User model."""
    username: str
    email: Optional[str] = None
    full_name: Optional[str] = None
    disabled: Optional[bool] = None
    user_roles: Optional[list[str]] = []


ROLE_TO_PERMISSIONS = {
    "admin": ["dashboard.view", 
              "resource.list", "resource.get", "resource.post", "resource.delete", "resource.patch",
              "hub.list",      "hub.get",      "hub.post",      "hub.delete",
              "sync.post"],
    "compreg_viewer3": ["dashboard.view", "resource.get"],
    "compreg_admin3": ["dashboard.view", "resource.get", "resource.delete", "hub.post", "hub.delete", "hub.post"],
    "compreg_query3": ["resource.list"],
    "compreg_sync3": ["sync"],
}

class UserWithPermissions(User):
    """User model with permissions."""
    def has_permission(self, permission: str) -> bool:
        for role in self.user_roles:
            if permission in ROLE_TO_PERMISSIONS.get(role, []):
                return True
        return False

    def requires_permission(self, permission: str):
        if not self.has_permission(permission):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"User does not have permission: {permission}"
            )
    

class UserInDB(UserWithPermissions):
    """User in database model."""
    hashed_password: str


# Fake users database - in production, use a real database
fake_users_db = {
    "admin": {
        "username": "admin",
        "full_name": "Administrator",
        "email": "admin@example.com",
        "hashed_password": "$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW",  # "secret"
        "disabled": False,
        "user_roles": ["admin"],
    }
}


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against a hash using bcrypt."""
    return bcrypt.checkpw(
        plain_password.encode('utf-8'),
        hashed_password.encode('utf-8')
    )


def get_password_hash(password: str) -> str:
    """Hash a password using bcrypt."""
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed.decode('utf-8')


def get_user(username: str) -> Optional[UserInDB]:
    """Get user from database."""
    if username in fake_users_db:
        user_dict = fake_users_db[username]
        return UserInDB(**user_dict)
    return None


def authenticate_user(username: str, password: str) -> Optional[UserInDB]:
    """Authenticate a user."""
    user = get_user(username)
    if not user:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    return user


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create a JWT access token."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


async def get_current_user(token: str = Depends(oauth2_scheme)) -> Optional[UserWithPermissions]:
    """Get current user from token."""
    if not OAUTH2_ENABLED:
        # If OAuth2 is disabled, return a default user
        return UserWithPermissions(username="anonymous", full_name="Anonymous User", user_roles=["admin"])
    
    if token is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = TokenData(username=username)
    except JWTError:
        raise credentials_exception
    
    user = get_user(username=token_data.username)
    if user is None:
        raise credentials_exception
    return user


async def get_current_active_user(current_user: User = Depends(get_current_user)) -> User:
    """Get current active user."""
    if current_user.disabled:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user


# Optional dependency - only enforces auth if enabled
async def optional_auth(token: str = Depends(oauth2_scheme)) -> Optional[User]:
    """Optional authentication - returns user if authenticated, None otherwise."""
    if not OAUTH2_ENABLED or token is None:
        return None
    try:
        return await get_current_user(token)
    except HTTPException:
        return None
