from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.user import User
from app.schemas.user import UserCreate


class UserService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def create_user(self, payload: UserCreate) -> User:
        user = User(email=str(payload.email))
        self.db.add(user)
        try:
            self.db.commit()
        except IntegrityError as exc:
            self.db.rollback()
            raise ValueError("Email already exists") from exc
        self.db.refresh(user)
        return user

    def get_user_by_id(self, user_id: int) -> User | None:
        stmt = select(User).where(User.id == user_id)
        return self.db.scalar(stmt)

