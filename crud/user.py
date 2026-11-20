from sqlalchemy.orm import Session
from models.user import User
from schemas.user import UserCreate
from core.security import get_password_hash


def _normalize_email(email: str) -> str:
    return email.strip().lower()


def get_user_by_email(db: Session, email: str):
    """Retrieve a user by their normalized email address."""
    normalized_email = _normalize_email(email)
    return db.query(User).filter(User.email == normalized_email).first()


def create_user(db: Session, user: UserCreate):
    """Create a new user in the database with a hashed password."""
    hashed_password = get_password_hash(user.password)
    normalized_email = _normalize_email(user.email)

    db_user = User(
        email=normalized_email,
        full_name=user.full_name,
        hashed_password=hashed_password,
    )

    db.add(db_user)
    try:
        db.commit()
    except Exception:
        db.rollback()
        raise
    db.refresh(db_user)
    return db_user
