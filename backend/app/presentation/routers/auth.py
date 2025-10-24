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
    try:
        user = use_case.execute(email=payload.email, password=payload.password)
    except UserAlreadyExistsError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered") from exc
    return UserResponse.model_validate(user, from_attributes=True)


@router.post("/login", response_model=TokenResponse)
def login(
    payload: LoginRequest,
    use_case=Depends(get_authenticate_user_use_case),
):
    try:
        user, token = use_case.execute(email=payload.email, password=payload.password)
    except InvalidCredentialsError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password") from exc

    return TokenResponse(
        access_token=token,
        user=UserResponse.model_validate(user, from_attributes=True),
    )


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: CurrentUser):
    return UserResponse.model_validate(current_user, from_attributes=True)
