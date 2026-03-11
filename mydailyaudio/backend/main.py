from fastapi import FastAPI, Depends, HTTPException, status, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
import sys
from pathlib import Path
from .database import engine, Base, get_db
from .models import User, Profile
from .schemas import UserCreate, UserOut, Token, ProfileCreate, ProfileUpdate, ProfileOut
from .crud import create_user, get_user_by_email, get_user_profiles, create_profile, update_profile, delete_profile
from .auth import verify_password, create_access_token, get_current_user

# 添加项目根目录到 sys.path，以便导入 report_engine
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from report_engine.run import run_profile

app = FastAPI(title="MyDailyAudio API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 模板配置
templates = Jinja2Templates(directory="templates")

@app.on_event("startup")
def startup_event():
    Base.metadata.create_all(bind=engine)

@app.post("/auth/register", response_model=UserOut)
def register(user_in: UserCreate, db: Session = Depends(get_db)):
    if get_user_by_email(db, user_in.email):
        raise HTTPException(status_code=400, detail="Email already registered")
    user = create_user(db, email=user_in.email, password=user_in.password)
    return user

@app.post("/auth/login", response_model=Token)
def login(user_in: UserCreate, db: Session = Depends(get_db)):
    user = get_user_by_email(db, user_in.email)
    if not user or not verify_password(user_in.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    access_token = create_access_token(data={"sub": user.email})
    return {"access_token": access_token, "token_type": "bearer"}

@app.get("/profiles", response_model=list[ProfileOut])
def list_profiles(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return get_user_profiles(db, current_user.id)

@app.post("/profiles", response_model=ProfileOut)
def create_profile(profile_in: ProfileCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    existing = db.query(Profile).filter(Profile.owner_id == current_user.id, Profile.name == profile_in.name).first()
    if existing:
        raise HTTPException(status_code=400, detail="Profile name already exists")
    return create_profile(db, profile_in, owner_id=current_user.id)

@app.get("/profiles/{profile_id}", response_model=ProfileOut)
def get_profile(profile_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    profile = db.query(Profile).filter(Profile.id == profile_id, Profile.owner_id == current_user.id).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    return profile

@app.put("/profiles/{profile_id}", response_model=ProfileOut)
def update_profile(profile_id: int, profile_in: ProfileUpdate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    profile = update_profile(db, profile_id, profile_in, owner_id=current_user.id)
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    return profile

@app.delete("/profiles/{profile_id}")
def delete_profile(profile_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    success = delete_profile(db, profile_id, current_user.id)
    if not success:
        raise HTTPException(status_code=404, detail="Profile not found")
    return {"detail": "Deleted"}

@app.post("/profiles/{profile_id}/run")
def run_profile_now(profile_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    profile = db.query(Profile).filter(Profile.id == profile_id, Profile.owner_id == current_user.id).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    
    profile_dict = {
        "name": profile.name,
        "config_dir": profile.config_dir,
        "output_dir": profile.output_dir,
        "audio_subdir": profile.audio_subdir,
        "url_path": profile.url_path,
        "telegram_bot_token": profile.telegram_bot_token,
        "telegram_chat_id": profile.telegram_chat_id,
    }

    try:
        result = run_profile(
            profile_dict,
            base_dir=ROOT_DIR,
            repo_name="mydailyaudio",
            dry_run=False
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
def health():
    return {"status": "ok"}