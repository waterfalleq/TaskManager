from pydantic import EmailStr
from sqlalchemy.orm import Session
from fastapi import HTTPException

from app.models.models import User
from app.auth.hash import get_password_hash, verify_password


def get_user_by_email(db: Session, email: str) -> User:
    """Fetch a user by email."""
    return db.query(User).filter(User.email == email).first()


def get_user_by_id(db: Session, id: int) -> User | None:
    """Fetch a user by ID."""
    return db.query(User).filter(User.id == id).first()


def create_user(db: Session, email: str, plain_password: str) -> User:
    """Create a new user with a hashed password."""
    if get_user_by_email(db, email) is not None:
        raise HTTPException(
            status_code=409, detail="Account with this email already exists"
        )
    new_user = User(email=email, hashed_password=get_password_hash(plain_password))
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user


def update_user_email(db: Session, user: User, new_email: EmailStr) -> User:
    """Update an existing user's email address."""
    if get_user_by_email(db, new_email) is not None:
        raise HTTPException(status_code=400, detail="Email already registered")
    user.email = new_email
    db.commit()
    db.refresh(user)
    return user


def update_user_password(
    db: Session, user: User, old_password: str, new_password: str
) -> User:
    """Update an existing user's password."""
    if not verify_password(old_password, user.hashed_password):
        raise HTTPException(status_code=400, detail="Incorrect password")
    user.hashed_password = get_password_hash(new_password)
    db.commit()
    db.refresh(user)
    return user
