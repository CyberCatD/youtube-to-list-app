import logging
import re
import html as html_module
from typing import Dict, Any, Optional
from urllib.parse import urlparse
import requests

logger = logging.getLogger(__name__)

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.0 Mobile/15E148 Safari/604.1',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.5',
}

def is_instagram_url(url: str) -> bool:
    parsed = urlparse(url)
    return 'instagram.com' in parsed.netloc

def is_tiktok_url(url: str) -> bool:
    parsed = urlparse(url)
    return 'tiktok.com' in parsed.netloc or 'vm.tiktok.com' in parsed.netloc

def is_facebook_url(url: str) -> bool:
    parsed = urlparse(url)
    return 'facebook.com' in parsed.netloc or 'fb.watch' in parsed.netloc or 'fb.com' in parsed.netloc

def extract_instagram_post_id(url: str) -> Optional[str]:
    patterns = [
        r'instagram\.com/p/([^/?]+)',
        r'instagram\.com/reel/([^/?]+)',
        r'instagram\.com/reels/([^/?]+)',
    ]
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    return None

def extract_tiktok_video_id(url: str) -> Optional[str]:
    patterns = [
        r'tiktok\.com/@[^/]+/video/(\d+)',
        r'tiktok\.com/v/(\d+)',
        r'vm\.tiktok\.com/(\w+)',
    ]
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    return None

def fetch_instagram_data(url: str) -> Dict[str, Any]:
    """
    Fetch Instagram post/reel data.
    Note: Instagram heavily restricts scraping. This uses basic HTML parsing.
    For production, consider Instagram Graph API with proper authentication.
    """
    post_id = extract_instagram_post_id(url)
    if not post_id:
        raise ValueError("Could not extract Instagram post ID from URL")
    
    logger.info(f"Fetching Instagram post: {post_id}")
    
    try:
        response = requests.get(url, headers=HEADERS, timeout=15)
        response.raise_for_status()
        html = response.text
        
        title_match = re.search(r'<meta property="og:title" content="([^"]+)"', html)
        desc_match = re.search(r'<meta property="og:description" content="([^"]+)"', html)
        image_match = re.search(r'<meta property="og:image" content="([^"]+)"', html)
        
        title = title_match.group(1) if title_match else "Instagram Recipe"
        description = desc_match.group(1) if desc_match else ""
        image_url = html_module.unescape(image_match.group(1)) if image_match else None
        
        caption = html_module.unescape(description)
        
        return {
            "platform": "instagram",
            "post_id": post_id,
            "caption": caption,
            "title": title,
            "image_url": image_url,
            "url": url,
        }
        
    except requests.RequestException as e:
        logger.error(f"Failed to fetch Instagram data: {e}")
        raise ValueError(f"Could not fetch Instagram post: {e}")

def fetch_tiktok_data(url: str) -> Dict[str, Any]:
    """
    Fetch TikTok video data.
    Note: TikTok also restricts scraping. This uses basic HTML parsing.
    """
    video_id = extract_tiktok_video_id(url)
    
    logger.info(f"Fetching TikTok video: {video_id or url}")
    
    try:
        response = requests.get(url, headers=HEADERS, timeout=15, allow_redirects=True)
        response.raise_for_status()
        html = response.text
        
        title_match = re.search(r'<meta property="og:title" content="([^"]+)"', html)
        desc_match = re.search(r'<meta property="og:description" content="([^"]+)"', html)
        image_match = re.search(r'<meta property="og:image" content="([^"]+)"', html)
        
        title = html_module.unescape(title_match.group(1)) if title_match else "TikTok Recipe"
        description = html_module.unescape(desc_match.group(1)) if desc_match else ""
        image_url = html_module.unescape(image_match.group(1)) if image_match else None
        
        return {
            "platform": "tiktok",
            "video_id": video_id,
            "caption": description,
            "title": title,
            "image_url": image_url,
            "url": response.url,
        }
        
    except requests.RequestException as e:
        logger.error(f"Failed to fetch TikTok data: {e}")
        raise ValueError(f"Could not fetch TikTok video: {e}")

def fetch_facebook_data(url: str) -> Dict[str, Any]:
    """
    Fetch Facebook video/post data.
    Note: Facebook restricts scraping. This uses basic HTML parsing.
    """
    logger.info(f"Fetching Facebook content: {url}")
    
    try:
        response = requests.get(url, headers=HEADERS, timeout=15, allow_redirects=True)
        response.raise_for_status()
        page_html = response.text
        
        title_match = re.search(r'<meta property="og:title" content="([^"]+)"', page_html)
        desc_match = re.search(r'<meta property="og:description" content="([^"]+)"', page_html)
        image_match = re.search(r'<meta property="og:image" content="([^"]+)"', page_html)
        
        title = html_module.unescape(title_match.group(1)) if title_match else "Facebook Recipe"
        description = html_module.unescape(desc_match.group(1)) if desc_match else ""
        image_url = html_module.unescape(image_match.group(1)) if image_match else None
        
        if not description and title:
            description = title
        
        return {
            "platform": "facebook",
            "caption": description,
            "title": title,
            "image_url": image_url,
            "url": response.url,
        }
        
    except requests.RequestException as e:
        logger.error(f"Failed to fetch Facebook data: {e}")
        raise ValueError(f"Could not fetch Facebook post: {e}")

def parse_recipe_from_caption(caption: str, metadata: Dict[str, Any]) -> Dict[str, Any]:
    """
    Parse recipe data from social media caption text.
    Uses pattern matching and LLM fallback for complex cases.
    """
    from src.services import llm_service
    from src.schemas import VideoMetadataSchema
    
    video_metadata = VideoMetadataSchema(
        title=metadata.get("title", "Social Media Recipe"),
        description=caption,
        url=metadata.get("url", ""),
        thumbnail_url=metadata.get("image_url"),
        channel_name=metadata.get("platform", "social"),
        comments=[]
    )
    
    try:
        llm_output = llm_service.generate_content_and_tags(video_metadata, caption)
        llm_output["source_type"] = metadata.get("platform", "social")
        llm_output["main_image_url"] = llm_output.get("main_image_url") or metadata.get("image_url")
        return llm_output
    except ValueError as e:
        logger.warning(f"LLM rejected social media content: {e}")
        raise
    except Exception as e:
        logger.error(f"Failed to parse recipe from caption: {e}")
        raise ValueError(f"Could not parse recipe from social media post: {e}")

def extract_recipe_from_social_url(url: str) -> Dict[str, Any]:
    """
    Main entry point: extract recipe from Instagram, TikTok, or Facebook URL.
    """
    if is_instagram_url(url):
        social_data = fetch_instagram_data(url)
    elif is_tiktok_url(url):
        social_data = fetch_tiktok_data(url)
    elif is_facebook_url(url):
        social_data = fetch_facebook_data(url)
    else:
        raise ValueError("URL is not from a supported social media platform (Instagram/TikTok/Facebook)")
    
    if not social_data.get("caption"):
        raise ValueError("Could not extract caption from social media post. The post may be private or unavailable.")
    
    recipe_data = parse_recipe_from_caption(social_data["caption"], social_data)
    return recipe_data

def detect_social_platform(url: str) -> Optional[str]:
    """Detect which social media platform a URL belongs to."""
    if is_instagram_url(url):
        return "instagram"
    if is_tiktok_url(url):
        return "tiktok"
    if is_facebook_url(url):
        return "facebook"
    return None
