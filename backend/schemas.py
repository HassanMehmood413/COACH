# app/schemas.py
from pydantic import BaseModel
from typing import List
from typing import Optional, Any

class ConversationCreate(BaseModel):
    user_id: str
    transcript: str

class Conversation(BaseModel):
    id: int
    user_id: str
    transcript: str
    analysis: Optional[Any] = None
    created_at: str

    class Config:
        orm_mode = True

class ConversationAnalysis(BaseModel):
    aspect: str
    feedback: str
    confidence_score: float
    key_moments: list
    improvement_areas: list






class User(BaseModel):
    name:str
    email:str    
    password:str

class ShowUser(BaseModel):
    name:str
    email:str
    class Config():
        orm_mode = True

# ------------------
# Social Clients 
# ------------------


class SocialPostRequest(BaseModel):
    content: str
    unsplash_image_id: Optional[str] = None
    image_url: Optional[str] = None

class SEOData(BaseModel):
    seo_content: str
    facebook_content: str
    hashtags: List[str]
    meta_description: str
    image_alt: str
    original_content: str

class SocialPostResponse(BaseModel):
    success: bool
    fb_status: str
    post_url: Optional[str] = None
    optimized_content: Optional[dict] = None



# Authetication 
class Login(BaseModel):
    Username:str
    password:str


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    email: str | None = None

class ImageSearchResult(BaseModel):
    id: str
    url: str
    thumb: str
    description: Optional[str] = None
    photographer: str