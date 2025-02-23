from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional, List

from schemas import SocialPostRequest, SocialPostResponse, ImageSearchResult
from database import get_db
from .oauth2 import get_current_user
from repository.unsplash_client import search_images, get_image_by_id
from repository.seo_langgraph import optimize_content_for_seo
from repository.social_clients import SocialMediaManager

router = APIRouter(tags=["Social Post"], prefix="/social_post")
social_manager = SocialMediaManager()

@router.post("/", response_model=SocialPostResponse)
async def create_social_post(
    request: Request,
    post: SocialPostRequest,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    # print(f"Current user: {current_user}")  # Log the current user
    try:
        print("Debug - Headers:", request.headers)
        # print("Debug - Current user:", current_user)
        print("Debug - Post content:", post.dict())
        
        # Check if user is authenticated and has Facebook token
        # if not current_user:
        #     raise HTTPException(
        #         status_code=status.HTTP_401_UNAUTHORIZED,
        #         detail="Not authenticated"
        #     )
        
        # if not current_user.facebook_token:
        #     raise HTTPException(
        #         status_code=status.HTTP_400_BAD_REQUEST,
        #         detail="Facebook not connected. Please connect Facebook first."
        #     )

        # First, optimize the content using SEO LangGraph
        optimized_content = await optimize_content_for_seo(post.content)
        print("Debug - Optimized content:", optimized_content)
        
        # Check if 'seo_content' is in the optimized content
        if 'seo_content' not in optimized_content:
            raise HTTPException(status_code=400, detail="SEO content not generated")
        
        # Create the post with optimized content
        post_data = {
            "content": optimized_content["seo_content"],
            "facebook_content": optimized_content["facebook_content"],
            "hashtags": optimized_content["hashtags"],
            "meta_description": optimized_content["meta_description"],
            "image_alt": optimized_content["image_alt"]
        }

        # If there's an Unsplash image ID, get the full image URL
        if post.unsplash_image_id:
            image_url = await get_image_by_id(post.unsplash_image_id)
            if image_url:
                post_data["image_url"] = image_url
        
        # Post to Facebook with optimized content
        fb_result = await social_manager.post_to_facebook(
            content=post_data["facebook_content"],
            image_url=post_data.get("image_url"),
            hashtags=post_data["hashtags"],
            facebook_token=current_user.facebook_token
        )

        return {
            "success": fb_result["success"],
            "fb_status": fb_result["status"],
            "post_url": fb_result.get("post_url"),
            "optimized_content": {
                "original": post.content,
                "seo_optimized": post_data["seo_content"],
                "hashtags": post_data["hashtags"],
                "meta_description": post_data["meta_description"]
            }
        }

    except HTTPException as http_ex:
        raise http_ex  # Re-raise HTTP exceptions
    except Exception as e:
        print("Debug - General error:", str(e))
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.get("/auth/facebook")
async def get_facebook_auth(current_user = Depends(get_current_user)):
    """Get Facebook authentication URL"""
    if not current_user.facebook_token:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Facebook token is required"
        )
    return {"auth_url": await social_manager.get_facebook_auth_url(current_user.facebook_token)}

@router.get("/search_images", response_model=List[ImageSearchResult])
async def search_images_endpoint(
    query: str,
    # current_user = Depends(get_current_user),
    per_page: int = 5
):
    """Search for images using Unsplash"""
    try:
        images = await search_images(query, per_page)
        if not images:
            return []
            
        return [{
            "id": img["id"],
            "url": img["url"],
            "thumb": img["thumb"],
            "description": img["description"],
            "photographer": img["photographer"]
        } for img in images]
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error searching images: {str(e)}"
        )

# @router.get("/scheduled")
# async def get_scheduled_posts(
#     db: AsyncSession = Depends(get_db),
#     current_user = Depends(get_current_user)
# ):
#     print(f"Current user: {current_user}")  # Log the current user

#     """Get all scheduled posts for the current user"""
#     try:
#         # For now, return an empty list since we haven't implemented scheduling yet
#         return {
#             "posts": [
#                 # Example structure of what we'll return later
#                 # {
#                 #     "content": "Sample post content",
#                 #     "image_url": "https://example.com/image.jpg",
#                 #     "scheduled_time": "2024-03-20T15:00:00Z",
#                 #     "facebook_status": True
#                 # }
#             ]
#         }
#     except Exception as e:
#         raise HTTPException(
#             status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
#             detail=str(e)
#         )
