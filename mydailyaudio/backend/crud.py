from .database import get_db
from .models import User, Profile
from .schemas import ProfileCreate, ProfileUpdate
from typing import List, Optional
from datetime import datetime
from .utils import get_password_hash

def get_user_by_email(db, email: str) -> Optional[User]:
    return db.query(User).filter(User.email == email).first()

def create_user(db, email: str, password: str) -> User:
    hashed = get_password_hash(password)
    user = User(email=email, hashed_password=hashed)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user

def get_user_profiles(db, user_id: int) -> List[Profile]:
    return db.query(Profile).filter(Profile.owner_id == user_id).all()

def get_profile(db, profile_id: int) -> Optional[Profile]:
    return db.query(Profile).filter(Profile.id == profile_id).first()

def create_profile(db, profile_in: ProfileCreate, owner_id: int) -> Profile:
    profile = Profile(**profile_in.dict(), owner_id=owner_id)
    db.add(profile)
    db.commit()
    db.refresh(profile)
    return profile

def update_profile(db, profile_id: int, profile_in: ProfileUpdate, owner_id: int) -> Optional[Profile]:
    profile = db.query(Profile).filter(Profile.id == profile_id, Profile.owner_id == owner_id).first()
    if not profile:
        return None
    for field, value in profile_in.dict(exclude_unset=True).items():
        setattr(profile, field, value)
    profile.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(profile)
    return profile

def delete_profile(db, profile_id: int, owner_id: int) -> bool:
    profile = db.query(Profile).filter(Profile.id == profile_id, Profile.owner_id == owner_id).first()
    if not profile:
        return False
    db.delete(profile)
    db.commit()
    return True

def get_profiles_due(db, limit: int = 10) -> List[Profile]:
    now = datetime.utcnow()
    return db.query(Profile).filter(Profile.enabled == True, Profile.next_run <= now).limit(limit).all()