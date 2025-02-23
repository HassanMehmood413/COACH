from fastapi import APIRouter, Depends, HTTPException, status, Request, Response
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.future import select
from repository.social_clients import SocialMediaManager
from database import get_db
from routes.oauth2 import get_current_user
from fastapi.responses import HTMLResponse
from typing import Dict

import database, models
from .auth_token import create_access_token, verify_token, SECRET_KEY, ALGORITHM
from .hashing import Hash
from schemas import Token
from . import oauth2
import jwt

router = APIRouter(tags=["Authentication"])
social_manager = SocialMediaManager()

@router.post("/login")
async def login(
    request: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(database.get_db)
):
    try:
        result = await db.execute(
            select(models.User).filter(models.User.email == request.username)
        )
        user = result.scalars().first()
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Invalid Credentials"
            )
            
        if not Hash.verify(user.password, request.password):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Incorrect password"
            )
            
        # Generate access token
        access_token = create_access_token(data={"sub": user.email})
            
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "user": {
                "id": user.id,
                "name": user.name,
                "email": user.email
            }
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.post("/auth/refresh")
async def refresh_token(
    current_user = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Refresh the access token"""
    try:
        # Create new access token
        access_token = create_access_token(data={"sub": current_user.email})
        
        return {
            "access_token": access_token,
            "token_type": "bearer"
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not refresh token"
        )

@router.get("/auth/facebook")
async def facebook_auth(
    request: Request,
    db: AsyncSession = Depends(get_db)
) -> Dict[str, str]:
    """Get Facebook authentication URL"""
    try:
        # Get Authorization header
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            raise HTTPException(
                status_code=401,
                detail="No valid authorization header found"
            )
        
        # Extract and verify token
        token = auth_header.replace('Bearer ', '')
        print(token)
        try:
            # Verify token and get user email
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            email = payload.get("sub")
            if not email:
                raise HTTPException(status_code=401, detail="Invalid token")
            
            # Get user from database
            result = await db.execute(
                select(models.User).filter(models.User.email == email)
            )
            user = result.scalars().first()
            if not user:
                raise HTTPException(status_code=401, detail="User not found")
            
            # Generate Facebook auth URL
            auth_url = await social_manager.get_facebook_auth_url(token)
            print(f"Debug - Generated auth URL for user {email}")
            
            return {
                "auth_url": auth_url,
                "message": "Successfully generated Facebook authentication URL"
            }
            
        except jwt.PyJWTError as e:
            print(f"Debug - Token verification error: {str(e)}")
            raise HTTPException(
                status_code=401,
                detail="Invalid or expired token"
            )
            
    except HTTPException as he:
        raise he
    except Exception as e:
        print(f"Debug - Facebook auth error: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to initialize Facebook authentication: {str(e)}"
        )

@router.get("/auth/facebook/callback")
async def facebook_callback(
    request: Request,
    code: str,
    state: str,
    db: AsyncSession = Depends(get_db)
):
    """Handle Facebook OAuth callback"""
    try:
        # Remove 'Bearer ' prefix from state
        token = state.replace('Bearer ', '') if state.startswith('Bearer ') else state
        
        try:
            # Verify the token
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            email = payload.get("sub")
            if not email:
                raise HTTPException(status_code=401, detail="Invalid token")
                
            # Get user from database
            result = await db.execute(select(models.User).filter(models.User.email == email))
            user = result.scalars().first()
            if not user:
                raise HTTPException(status_code=401, detail="User not found")

            # Exchange code for access token
            token_data = await social_manager.get_facebook_token(code)
            
            # Update user's Facebook token
            user.facebook_token = token_data["access_token"]
            await db.commit()
            
            return HTMLResponse(content=f"""
                <script>
                    window.opener.postMessage({{
                        type: 'facebook_auth',
                        success: true,
                        token: '{token}',
                        message: 'Facebook connected successfully'
                    }}, window.location.origin);
                    window.close();
                </script>
            """)
        except jwt.PyJWTError as e:
            print(f"Token verification error: {str(e)}")
            raise HTTPException(status_code=401, detail="Invalid token")
            
    except Exception as e:
        print(f"Facebook callback error: {str(e)}")
        return HTMLResponse(content=f"""
            <script>
                window.opener.postMessage({{ 
                    type: 'facebook_auth',
                    success: false,
                    error: 'Authentication failed'
                }}, window.location.origin);
                window.close();
            </script>
        """)

async def get_user_from_token(token: str, db: AsyncSession):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email = payload.get("sub")
        if not email:
            return None
        result = await db.execute(select(models.User).filter(models.User.email == email))
        return result.scalars().first()
    except:
        return None

@router.get("/auth/facebook/status")
async def facebook_status(
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Check if user has connected Facebook"""
    try:
        if not current_user:
            return {"connected": False, "message": "Not authenticated"}
            
        # Check if user has a valid Facebook token
        if current_user.facebook_token:
            try:
                # Verify the token is still valid
                user_info = await social_manager.get_facebook_user_info(current_user.facebook_token)
                return {
                    "connected": True,
                    "user_name": user_info.get("name"),
                    "message": "Facebook connected"
                }
            except:
                # Token is invalid, clear it
                current_user.facebook_token = None
                await db.commit()
                return {
                    "connected": False,
                    "message": "Facebook token expired. Please reconnect."
                }
        
        return {"connected": False, "message": "Facebook not connected"}
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to check Facebook status: {str(e)}"
        )
