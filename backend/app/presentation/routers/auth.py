"""Authentication endpoints."""

from fastapi import APIRouter, Depends, HTTPException, status

from app.application.use_cases.auth import InvalidCredentialsError, UserAlreadyExistsError
from app.config.dependencies import (
    get_authenticate_user_use_case,
    get_register_user_use_case,
)
from app.config.security import CurrentUser
from app.presentation.schemas.auth import (
    LoginRequest,
    RegisterRequest,
    TokenResponse,
    UserResponse,
)

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register_user(
    payload: RegisterRequest,
    use_case=Depends(get_register_user_use_case),
):
    """Register a new user and return its public representation."""
    try:
        user = use_case.execute(email=payload.email, password=payload.password)
    except UserAlreadyExistsError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered") from exc
    return UserResponse.from_orm(user)


@router.post("/login", response_model=TokenResponse)
def login(
    payload: LoginRequest,
    use_case=Depends(get_authenticate_user_use_case),
):
    """Authenticate a user and return the access token."""
    try:
        user, token = use_case.execute(email=payload.email, password=payload.password)
    except InvalidCredentialsError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password") from exc

    return TokenResponse(access_token=token, user=UserResponse.from_orm(user))


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: CurrentUser):
    """Return the authenticated user."""
    return UserResponse.from_orm(current_user)
