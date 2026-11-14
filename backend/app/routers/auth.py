from fastapi import APIRouter, Depends, HTTPException, Request, status

from app.auth import require_admin, verify_password
from app.config import settings
from app.schemas import AdminMe, LoginRequest

router = APIRouter(prefix="/admin", tags=["auth"])


@router.post("/login", response_model=AdminMe)
def login(payload: LoginRequest, request: Request) -> AdminMe:
    valid_username = payload.username == settings.admin_username
    valid_password = verify_password(payload.password, settings.admin_password_hash)
    if not (valid_username and valid_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Невірний логін або пароль"
        )

    request.session["is_admin"] = True
    return AdminMe(username=settings.admin_username)


@router.post("/logout")
def logout(request: Request) -> dict:
    request.session.clear()
    return {"ok": True}


@router.get("/me", response_model=AdminMe, dependencies=[Depends(require_admin)])
def me() -> AdminMe:
    return AdminMe(username=settings.admin_username)
