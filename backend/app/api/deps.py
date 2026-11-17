from fastapi import Depends, HTTPException, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session
from app.database.db import get_db
from app.models.orm import User
from app.security.hashing import decode_token
from app.security.ratelimit import check_rate_limit

bearer = HTTPBearer(auto_error=False)


def rate_limited(request: Request) -> None:
    check_rate_limit(request)


def current_user(cred: HTTPAuthorizationCredentials | None = Depends(bearer), db: Session = Depends(get_db)) -> User:
    uid = decode_token(cred.credentials) if cred else None
    user = db.get(User, uid) if uid else None
    if not user:
        raise HTTPException(401, "Not authenticated")
    return user
