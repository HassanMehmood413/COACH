from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from database import get_db
from . import auth_token
from sqlalchemy.future import select
import models
import jwt
from .auth_token import SECRET_KEY, ALGORITHM

# Set auto_error to False so we can customize the error message
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login", auto_error=False)

async def get_current_user(
       token: str = Depends(oauth2_scheme),
       db: AsyncSession = Depends(get_db)
   ):
       print(f"Received token: {token}")  # Log the received token
       credentials_exception = HTTPException(
           status_code=status.HTTP_401_UNAUTHORIZED,
           detail="Could not validate credentials",
           headers={"WWW-Authenticate": "Bearer"},
       )
       
       try:
           payload = auth_token.verify_token(token, credentials_exception)
           email: str = payload.get("sub")
           result = await db.execute(
               select(models.User).filter(models.User.email == email)
           )
           user = result.scalars().first()
           
           if user is None:
               raise credentials_exception
               
           return user
       except Exception as e:
           print(f"Authentication error: {str(e)}")
           raise credentials_exception
       
       
async def get_current_token(
    token: str = Depends(oauth2_scheme)
) -> str:
    try:
        jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return token
    except:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token"
        )
