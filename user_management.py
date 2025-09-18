from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, EmailStr
from passlib.context import CryptContext
from typing import Dict, Optional
from auth_dependencies import get_current_active_user

router = APIRouter()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

users_db: Dict[str, Dict] = {
    "alice": {
        "username": "alice",
        "email": "alice@example.com",
        "hashed_password": pwd_context.hash("password123"),
        "role": "admin",
    }
}

class UserRegistration(BaseModel):
    username: str
    email: EmailStr
    password: str
    role: str

class UserProfileUpdate(BaseModel):
    email: Optional[EmailStr] = None
    password: Optional[str] = None

@router.post("/register")
def register_user(user: UserRegistration):
    if user.username in users_db:
        raise HTTPException(status_code=400, detail="Username already registered")
    if any(u["email"] == user.email for u in users_db.values()):
        raise HTTPException(status_code=400, detail="Email already registered")
    hashed_password = pwd_context.hash(user.password)
    users_db[user.username] = {
        "username": user.username,
        "email": user.email,
        "hashed_password": hashed_password,
        "role": user.role,
    }
    return {"msg": "User registered successfully"}

@router.put("/profile")
def update_profile(profile: UserProfileUpdate, current_user: dict = Depends(get_current_active_user)):
    username = current_user['username']
    user = users_db.get(username)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if profile.email:
        if any(u["email"] == profile.email and u["username"] != username for u in users_db.values()):
            raise HTTPException(status_code=400, detail="Email already in use")
        user['email'] = profile.email
    if profile.password:
        user['hashed_password'] = pwd_context.hash(profile.password)
    return {"msg": "Profile updated successfully"}
