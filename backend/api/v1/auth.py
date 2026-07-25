"""Auth endpoints: register, login, refresh, current user.

Routes do exactly three things: validate input (via schema),
call the service, map the result/error to an HTTP response.
No business logic lives here.
"""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from api.deps import get_auth_service, get_current_user
from core.exceptions import (
    EmailAlreadyRegisteredError,
    InvalidCredentialsError,
    InvalidTokenError,
    UserNotFoundError,
)
from models.user import User
from schemas.auth import LoginRequest, RefreshRequest, RegisterRequest, TokenResponse, UserResponse
from services.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register(
    payload: RegisterRequest,
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
) -> User:
    try:
        return auth_service.register(
            email=payload.email, password=payload.password, full_name=payload.full_name
        )
    except EmailAlreadyRegisteredError as error:
        raise HTTPException(status.HTTP_409_CONFLICT, detail=str(error)) from error


@router.post("/login", response_model=TokenResponse)
def login(
    payload: LoginRequest,
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
) -> TokenResponse:
    try:
        user = auth_service.authenticate(email=payload.email, password=payload.password)
    except InvalidCredentialsError as error:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, detail=str(error)) from error

    access_token, refresh_token = auth_service.issue_tokens(user.id)
    return TokenResponse(access_token=access_token, refresh_token=refresh_token)


@router.post("/refresh", response_model=TokenResponse)
def refresh(
    payload: RefreshRequest,
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
) -> TokenResponse:
    try:
        access_token, refresh_token = auth_service.refresh_access_token(payload.refresh_token)
    except (InvalidTokenError, UserNotFoundError) as error:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, detail=str(error)) from error

    return TokenResponse(access_token=access_token, refresh_token=refresh_token)


@router.get("/me", response_model=UserResponse)
def get_me(current_user: Annotated[User, Depends(get_current_user)]) -> User:
    return current_user
