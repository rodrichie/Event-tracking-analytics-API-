from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select
from api.db.session import get_session
from .models import User, UserCreate, UserLogin, UserResponse, Token
from .security import (
    verify_password, 
    get_password_hash, 
    create_access_token,
    ACCESS_TOKEN_EXPIRE_MINUTES
)
from .dependencies import get_current_active_user, get_current_superuser

router = APIRouter()


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register_user(user_data: UserCreate, session: Session = Depends(get_session)):
    """Register a new user."""
    # Check if username exists
    query = select(User).where(User.username == user_data.username)
    existing_user = session.exec(query).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered"
        )
    
    # Check if email exists
    query = select(User).where(User.email == user_data.email)
    existing_email = session.exec(query).first()
    if existing_email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Create new user
    hashed_password = get_password_hash(user_data.password)
    db_user = User(
        email=user_data.email,
        username=user_data.username,
        hashed_password=hashed_password,
        full_name=user_data.full_name
    )
    session.add(db_user)
    session.commit()
    session.refresh(db_user)
    
    return db_user


@router.post("/login", response_model=Token)
def login(user_credentials: UserLogin, session: Session = Depends(get_session)):
    """Authenticate user and return JWT token."""
    # Get user from database
    query = select(User).where(User.username == user_credentials.username)
    user = session.exec(query).first()
    
    if not user or not verify_password(user_credentials.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user"
        )
    
    # Create access token
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, 
        expires_delta=access_token_expires
    )
    
    return {"access_token": access_token, "token_type": "bearer"}


@router.get("/me", response_model=UserResponse)
def get_current_user_info(current_user: User = Depends(get_current_active_user)):
    """Get current authenticated user information."""
    return current_user


@router.get("/users", response_model=list[UserResponse])
def list_users(
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_superuser)
):
    """List all users (superuser only)."""
    query = select(User)
    users = session.exec(query).all()
    return users
