from fastapi import APIRouter, Depends, HTTPException
from pymongo.database import Database

from ...database import UserRepository
from ..deps import get_db
from ..schemas import ProfileResponse

router = APIRouter()


@router.get("/profile", response_model=ProfileResponse)
def get_profile(db: Database = Depends(get_db)) -> ProfileResponse:
    user = UserRepository(db).current_user()
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return ProfileResponse(user=user)
