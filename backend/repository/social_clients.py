import facebook
from typing import Dict, Optional
import aiohttp
import httpx
import random
import string
from fastapi import HTTPException
import urllib.parse

class SocialMediaManager:
    def __init__(self):
        self.facebook_app_id = "609870711852529"
        self.facebook_app_secret = "c00422746163b887358b3c83a2435c0e"
        self.redirect_uri = "http://localhost:8000/auth/facebook/callback"
        self.fb_api_version = "v18.0"  # For URL endpoints
        self.graph_api_version = "2.12"  # For Graph API initialization

    async def get_facebook_auth_url(self, access_token: str) -> str:
        """Get Facebook OAuth URL for user authorization"""
        try:
            # Ensure the redirect URI is properly encoded
            encoded_redirect = urllib.parse.quote(self.redirect_uri, safe='')
            encoded_token = urllib.parse.quote(access_token, safe='')
            
            auth_url = (
                f"https://www.facebook.com/{self.fb_api_version}/dialog/oauth"
                f"?client_id={self.facebook_app_id}"
                f"&redirect_uri={encoded_redirect}"
                f"&state={encoded_token}"
                f"&scope=pages_show_list,pages_manage_posts,pages_read_engagement,public_profile"
            )
            
            print(f"Debug - Generated Facebook auth URL: {auth_url}")
            return auth_url
            
        except Exception as e:
            print(f"Error generating Facebook auth URL: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail=f"Failed to generate Facebook auth URL: {str(e)}"
            )

    async def get_facebook_token(self, code: str) -> dict:
        """Exchange code for access token"""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"https://graph.facebook.com/{self.fb_api_version}/oauth/access_token",
                params={
                    "client_id": self.facebook_app_id,
                    "client_secret": self.facebook_app_secret,
                    "code": code,
                    "redirect_uri": self.redirect_uri
                }
            )
            if response.status_code != 200:
                raise HTTPException(
                    status_code=400,
                    detail="Failed to get Facebook access token"
                )
            
            # Get the long-lived token
            token_data = response.json()
            long_lived_token = await self.get_long_lived_token(token_data["access_token"])
            
            # Get user info to verify the account
            user_info = await self.get_facebook_user_info(long_lived_token)
            
            return {
                "access_token": long_lived_token,
                "user_id": user_info.get("id"),
                "name": user_info.get("name")
            }

    async def get_long_lived_token(self, short_lived_token: str) -> str:
        """Convert short-lived token to long-lived token"""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"https://graph.facebook.com/{self.fb_api_version}/oauth/access_token",
                params={
                    "grant_type": "fb_exchange_token",
                    "client_id": self.facebook_app_id,
                    "client_secret": self.facebook_app_secret,
                    "fb_exchange_token": short_lived_token
                }
            )
            if response.status_code != 200:
                raise HTTPException(
                    status_code=400,
                    detail="Failed to get long-lived token"
                )
            return response.json()["access_token"]

    async def get_facebook_user_info(self, token: str) -> Dict:
        """Get Facebook user information"""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"https://graph.facebook.com/{self.fb_api_version}/me",
                params={
                    "access_token": token,
                    "fields": "id,name"
                }
            )
            if response.status_code != 200:
                raise HTTPException(
                    status_code=400,
                    detail="Failed to get user information"
                )
            return response.json()

    async def post_to_facebook(self, content: str, image_url: str = None, hashtags: list = None, facebook_token: str = None):
        """
        Post content to Facebook
        """
        try:
            if not facebook_token:
                return {
                    "success": False,
                    "status": "No Facebook token provided",
                    "error": "Authentication required"
                }

            # Combine content with hashtags
            full_content = content
            if hashtags and len(hashtags) > 0:
                full_content += "\n\n" + " ".join(hashtags)

            # Prepare the post data
            post_data = {
                "message": full_content
            }

            if image_url:
                post_data["url"] = image_url

            # Make the API request to Facebook
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"https://graph.facebook.com/v18.0/me/feed",
                    params={"access_token": facebook_token},
                    json=post_data
                )

                if response.status_code == 200:
                    data = response.json()
                    post_id = data.get("id")
                    # Get the post URL
                    post_url = f"https://facebook.com/{post_id}"
                    return {
                        "success": True,
                        "status": "Posted successfully to Facebook",
                        "post_url": post_url
                    }
                else:
                    error_msg = response.json().get("error", {}).get("message", "Unknown error")
                    return {
                        "success": False,
                        "status": f"Failed to post to Facebook: {error_msg}",
                        "error": error_msg
                    }

        except Exception as e:
            print("Debug - Facebook posting error:", str(e))
            return {
                "success": False,
                "status": f"Failed to post to Facebook: {str(e)}",
                "error": str(e)
            }