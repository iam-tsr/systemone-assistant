from fastapi import APIRouter, HTTPException

from ...database import UserRepository
from ..schemas import ProfileResponse

router = APIRouter()


@router.get("/profile", response_model=ProfileResponse)
def get_profile() -> ProfileResponse:
    user = UserRepository().current_user()
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return ProfileResponse(user=user)
