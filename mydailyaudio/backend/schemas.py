from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime

class UserBase(BaseModel):
    email: EmailStr

class UserCreate(UserBase):
    password: str

class UserOut(UserBase):
    id: int
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str

class ProfileBase(BaseModel):
    name: str
    description: Optional[str] = None
    config_dir: str
    output_dir: str
    audio_subdir: str = "audio"
    url_path: str
    telegram_bot_token: Optional[str] = None
    telegram_chat_id: Optional[str] = None
    schedule: str
    enabled: bool = True

class ProfileCreate(ProfileBase):
    pass

class ProfileUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    config_dir: Optional[str] = None
    output_dir: Optional[str] = None
    audio_subdir: Optional[str] = None
    url_path: Optional[str] = None
    telegram_bot_token: Optional[str] = None
    telegram_chat_id: Optional[str] = None
    schedule: Optional[str] = None
    enabled: Optional[bool] = None

class ProfileOut(ProfileBase):
    id: int
    owner_id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    last_run: Optional[datetime] = None
    next_run: Optional[datetime] = None

    class Config:
        from_attributes = True