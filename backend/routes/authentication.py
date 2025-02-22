from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.future import select

import database, models
from .auth_token import create_access_token, verify_token
import token  # Ensure this is your token utility module
from .hashing import Hash
from schemas import Token

router = APIRouter(tags=["Authentication"])

@router.post("/login")
async def login(
    request: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(database.get_db)
):
    # Use async select to query the user by email (username field in OAuth2PasswordRequestForm)
    result = await db.execute(select(models.User).filter(models.User.email == request.username))
    user = result.scalars().first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    if not Hash.verify(user.password, request.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid Credentials"
        )
    
    # Generate JWT Token
    access_token = create_access_token(data={"sub": user.email})
    return Token(access_token=access_token, token_type="bearer")
