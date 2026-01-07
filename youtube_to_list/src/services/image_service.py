import logging
import os
import uuid
import requests
from typing import Optional
from urllib.parse import quote

logger = logging.getLogger(__name__)

MICROLINK_API = "https://api.microlink.io/"
UPLOAD_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "uploads")

os.makedirs(UPLOAD_DIR, exist_ok=True)

def fetch_thumbnail_from_microlink(url: str) -> Optional[str]:
    """
    Fetch thumbnail image URL using Microlink API.
    This is used as a fallback when OG meta image is not available or expired.
    """
    try:
        encoded_url = quote(url, safe='')
        api_url = f"{MICROLINK_API}?url={encoded_url}"
        
        response = requests.get(api_url, timeout=15)
        response.raise_for_status()
        
        data = response.json()
        
        if data.get("status") == "success":
            image_data = data.get("data", {}).get("image")
            if image_data and image_data.get("url"):
                logger.info(f"Microlink returned image for {url}")
                return image_data["url"]
        
        logger.warning(f"Microlink did not return image for {url}: {data.get('status')}")
        return None
        
    except requests.RequestException as e:
        logger.error(f"Microlink API error for {url}: {e}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error fetching thumbnail: {e}")
        return None

def validate_image_url(url: str) -> bool:
    """
    Check if an image URL is valid and accessible.
    """
    if not url:
        return False
    
    try:
        response = requests.head(url, timeout=5, allow_redirects=True)
        content_type = response.headers.get("content-type", "")
        return response.status_code == 200 and "image" in content_type
    except Exception:
        return False

def get_best_image_url(source_url: str, current_image_url: Optional[str] = None) -> Optional[str]:
    """
    Get the best available image URL for a recipe.
    
    Priority:
    1. Current image URL if valid
    2. Microlink thumbnail
    3. None (user can upload)
    """
    if current_image_url and validate_image_url(current_image_url):
        logger.info(f"Current image URL is valid: {current_image_url[:50]}...")
        return current_image_url
    
    logger.info(f"Current image invalid or missing, trying Microlink for {source_url}")
    microlink_url = fetch_thumbnail_from_microlink(source_url)
    
    if microlink_url:
        return microlink_url
    
    logger.info(f"No image available for {source_url}")
    return None

def save_uploaded_image(file_content: bytes, filename: str) -> str:
    """
    Save an uploaded image file and return the relative path.
    """
    ext = os.path.splitext(filename)[1].lower()
    if ext not in ['.jpg', '.jpeg', '.png', '.gif', '.webp']:
        ext = '.jpg'
    
    unique_filename = f"{uuid.uuid4().hex}{ext}"
    file_path = os.path.join(UPLOAD_DIR, unique_filename)
    
    with open(file_path, 'wb') as f:
        f.write(file_content)
    
    logger.info(f"Saved uploaded image: {unique_filename}")
    return f"/uploads/{unique_filename}"

def get_upload_path(filename: str) -> str:
    """Get full path for an uploaded file."""
    return os.path.join(UPLOAD_DIR, filename)
