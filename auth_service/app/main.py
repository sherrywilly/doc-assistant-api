"""Auth microservice — register, login, and token verification."""

import os

from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordRequestForm
from jose import JWTError, jwt
from sqlalchemy.orm import Session

from .auth import ALGORITHM, create_access_token, get_password_hash, verify_password
from .database import Base, engine, get_db
from .models import User
from .schemas import Token, UserCreate, UserOut

# Initialise DB tables on startup
Base.metadata.create_all(bind=engine)

JWT_SECRET_KEY: str = os.getenv(
    "JWT_SECRET_KEY", "dev-secret-key-change-in-production"
)

app = FastAPI(
    title="Auth Service",
    description="JWT-based user authentication for the Document Assistant platform",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------------------------
# Health
# ---------------------------------------------------------------------------


@app.get("/health", tags=["Health"])
def health_check():
    return {"status": "ok", "service": "auth"}


# ---------------------------------------------------------------------------
# Register
# ---------------------------------------------------------------------------


@app.post(
    "/auth/register",
    response_model=UserOut,
    status_code=status.HTTP_201_CREATED,
    tags=["Auth"],
)
def register(user: UserCreate, db: Session = Depends(get_db)):
    """Create a new user account."""
    existing = db.query(User).filter(User.username == user.username).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered.",
        )
    db_user = User(
        username=user.username,
        hashed_password=get_password_hash(user.password),
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


# ---------------------------------------------------------------------------
# Login
# ---------------------------------------------------------------------------


@app.post("/auth/login", response_model=Token, tags=["Auth"])
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
):
    """Authenticate and return a JWT access token."""
    user = db.query(User).filter(User.username == form_data.username).first()
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    token = create_access_token({"sub": user.username}, secret_key=JWT_SECRET_KEY)
    return {"access_token": token, "token_type": "bearer"}


# ---------------------------------------------------------------------------
# Verify token (called by other services for token introspection)
# ---------------------------------------------------------------------------


@app.post("/auth/verify", tags=["Auth"])
def verify_token(token: str):
    """Verify a JWT and return the username it encodes."""
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if not username:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token payload.",
            )
        return {"username": username, "valid": True}
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token is invalid or expired.",
        )
