# users.py
from fastapi import APIRouter, Depends, status, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from routes import oauth2  # if you're using oauth2 for current_user, ensure it's async as well

import schemas
import models
from repository import user  # our repository functions will now be async
from database import get_db

router = APIRouter(
    tags=['Users'],
    prefix="/users",
)

@router.post('/', response_model=schemas.ShowUser)
async def create_user(request: schemas.User, db: AsyncSession = Depends(get_db)):
    return await user.create(request, db)

@router.get('/{id}', response_model=schemas.ShowUser)
async def get_user(id: int, db: AsyncSession = Depends(get_db), current_user: schemas.User = Depends(oauth2.get_current_user)):
    return await user.get_user(id, db)

@router.get('/me', response_model=schemas.ShowUser)
async def get_current_user(
    current_user: schemas.User = Depends(oauth2.get_current_user)
):
    return current_user
