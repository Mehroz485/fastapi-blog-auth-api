import os
from fastapi import APIRouter, Depends, Header, HTTPException
from sqlalchemy.orm import Session
from jose import jwt, JWTError
from datetime import datetime, timedelta, timezone

from passlib.context import CryptContext
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm

# This tells Swagger UI: "tokens come from the /login endpoint,
# and show an Authorize button that sends them as a Bearer header"
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

from database import SessionLocal  # FIX: get_db wasn't defined here; reuse the same session factory as main.py
from model import User  # FIX: "User" was used but never imported/defined; added the model in model.py and import it here
import schemas

# FIX: this file had "@app.post(...)" / "@app.get(...)" but no FastAPI
# "app" was ever created or imported in this file - app lives in main.py.
# Using an APIRouter here lets main.py mount these routes onto its own
# app via app.include_router(auth.router), which is the normal FastAPI
# pattern for splitting routes across files.
router = APIRouter()

# FIX: SECRET_KEY and ALGORITHM were used in create_token/verify_token but
# never defined anywhere, which would raise a NameError at runtime.
# In real projects this should come from an environment variable, not be
# hardcoded - falls back to a default only for local development.
SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-change-me")
ALGORITHM = "HS256"

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


# FIX: get_db was referenced (Depends(get_db)) but never defined in this
# file. Added a local copy identical to the one in main.py.
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def create_token(data: dict):
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(minutes=30)
    to_encode.update({"exp": expire})
    token = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return token


# FIX: changed decorator from @app.post to @router.post since "app"
# doesn't exist in this file (see router definition above).
@router.post("/register", response_model=schemas.UserResponse)
def register(user: schemas.UserCreate, db: Session = Depends(get_db)):
    # FIX: original took username/password as raw query params with no
    # validation; now takes a validated UserCreate body via schemas.py.
    existing_user = db.query(User).filter(User.username == user.username).first()

    if existing_user:
        raise HTTPException(
            status_code=400,
            detail="Username already taken"
        )

    hashed_password = pwd_context.hash(user.password)

    new_user = User(username=user.username, hashed_password=hashed_password)

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return new_user  # FIX: was returning a plain dict; now returns the user so response_model can validate/shape it


@router.post("/login", response_model=schemas.Token)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.username == form_data.username).first()

    if not db_user or not pwd_context.verify(form_data.password, db_user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid username or password")

    token = create_token({"sub": db_user.username})
    return {"access_token": token, "token_type": "bearer"}

def verify_token(token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid or expired token")



@router.get("/secure")  # FIX: changed @app.get to @router.get (same reason as /register)
def secure(user=Depends(verify_token)):
    return {
        "message": "secure data accessed",
        "user": user
    }
