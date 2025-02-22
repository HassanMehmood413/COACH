# repository/user.py
from passlib.context import CryptContext
from fastapi import HTTPException, status
import schemas
import models
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

async def create(request: schemas.User, db: AsyncSession):
    try:
        hashed_password = pwd_context.hash(request.password)
        new_user = models.User(name=request.name, email=request.email, password=hashed_password)
        db.add(new_user)
        await db.commit()         # Await the commit
        await db.refresh(new_user)  # Await the refresh
        return new_user
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

async def get_user(id: int, db: AsyncSession):
    result = await db.execute(select(models.User).filter(models.User.id == id))
    user_obj = result.scalars().first()
    if not user_obj:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return user_obj
