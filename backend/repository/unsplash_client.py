import os
import httpx
from typing import List, Dict, Optional

# Get Unsplash credentials from environment
UNSPLASH_ACCESS_KEY = os.getenv("UNSPLASH_ACCESS_KEY", "gA7919Wd6jK_5u6XaWR9vEgSeRVSfY8Jr8NaVFh6uCQ")
UNSPLASH_SECRET_KEY = os.getenv("UNSPLASH_SECRET_KEY", "zgOsFzZaJTmbxAp9XNqIQWCf0A4inb6GNUG04Vh2oH0")
UNSPLASH_APPLICATION_ID = os.getenv("UNSPLASH_APPLICATION_ID", "713101")

async def search_images(query: str, per_page: int = 5) -> List[Dict[str, str]]:
    """
    Search for images on Unsplash and return multiple options.
    """
    url = "https://api.unsplash.com/search/photos"
    params = {
        "query": query,
        "client_id": UNSPLASH_ACCESS_KEY,
        "per_page": per_page,
        "orientation": "landscape"
    }
    headers = {
        "X-Application-Id": UNSPLASH_APPLICATION_ID
    }
    
    async with httpx.AsyncClient() as client:
        response = await client.get(url, params=params, headers=headers)
        if response.status_code == 200:
            data = response.json()
            return [
                {
                    "id": photo["id"],
                    "url": photo["urls"]["regular"],
                    "thumb": photo["urls"]["thumb"],
                    "description": photo["description"] or photo["alt_description"] or "No description",
                    "photographer": photo["user"]["name"]
                }
                for photo in data["results"]
            ]
        else:
            print(f"Error fetching images: {response.status_code} - {response.text}")
            return []

async def get_image_by_id(image_id: str) -> Optional[str]:
    """
    Get a specific image by its ID.
    """
    url = f"https://api.unsplash.com/photos/{image_id}"
    params = {
        "client_id": UNSPLASH_ACCESS_KEY
    }
    headers = {
        "X-Application-Id": UNSPLASH_APPLICATION_ID
    }
    
    async with httpx.AsyncClient() as client:
        response = await client.get(url, params=params, headers=headers)
        if response.status_code == 200:
            data = response.json()
            return data["urls"]["regular"]
        return None
