from fastapi import APIRouter, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from fastapi import Depends

from backend.auth import authenticate_user, create_access_token
from backend.schemas import LoginRequest, TokenResponse

router = APIRouter()


@router.post("/login", response_model=TokenResponse)
def login(form: OAuth2PasswordRequestForm = Depends()):
    """Kullanıcı girişi — JWT token döner."""
    user = authenticate_user(form.username, form.password)
    if not user:
        raise HTTPException(status_code=401, detail="Kullanıcı adı veya şifre hatalı")

    token = create_access_token({
        "sub":  user["username"],
        "name": user["name"],
        "role": user["role"],
    })
    return TokenResponse(
        access_token=token,
        username=user["username"],
        name=user["name"],
        role=user["role"],
    )
