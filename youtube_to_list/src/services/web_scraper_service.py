import logging
from typing import Dict, Any, Optional
from urllib.parse import urlparse
import requests
from recipe_scrapers import scrape_html
from recipe_scrapers._exceptions import NoSchemaFoundInWildMode
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.5',
}

def is_youtube_url(url: str) -> bool:
    parsed = urlparse(url)
    return any(domain in parsed.netloc for domain in ['youtube.com', 'youtu.be'])

def is_social_media_url(url: str) -> bool:
    parsed = urlparse(url)
    social_domains = ['instagram.com', 'tiktok.com', 'facebook.com', 'fb.watch', 'fb.com', 'twitter.com', 'x.com']
    return any(domain in parsed.netloc for domain in social_domains)

def fetch_page_html(url: str) -> str:
    response = requests.get(url, headers=HEADERS, timeout=15)
    response.raise_for_status()
    return response.text

def extract_recipe_from_url(url: str) -> Dict[str, Any]:
    """
    Extract structured recipe data from any recipe website URL.
    Uses recipe-scrapers library with fallback to custom parsing.
    
    Returns:
        Dict with recipe_details, ingredients, instructions, main_image_url
    """
    logger.info(f"Extracting recipe from URL: {url}")
    
    if is_youtube_url(url):
        raise ValueError("YouTube URLs should be processed via the YouTube endpoint")
    
    if is_social_media_url(url):
        raise ValueError("Social media URLs should be processed via the social media endpoint")
    
    try:
        html = fetch_page_html(url)
        scraper = scrape_html(html, org_url=url, wild_mode=True)
        
        ingredients_list = []
        for ingredient in scraper.ingredients():
            parsed = parse_ingredient_string(ingredient)
            ingredients_list.append(parsed)
        
        instructions_list = []
        instructions_text = scraper.instructions()
        if instructions_text:
            steps = instructions_text.split('\n')
            for i, step in enumerate(steps, 1):
                step = step.strip()
                if step:
                    instructions_list.append({
                        "step_number": i,
                        "section_name": None,
                        "description": step
                    })
        
        prep_time = format_time(scraper.prep_time()) if hasattr(scraper, 'prep_time') else None
        cook_time = format_time(scraper.cook_time()) if hasattr(scraper, 'cook_time') else None
        total_time = format_time(scraper.total_time()) if hasattr(scraper, 'total_time') else None
        
        try:
            nutrients = scraper.nutrients() if hasattr(scraper, 'nutrients') else {}
        except Exception:
            nutrients = {}
        
        calories = None
        if nutrients:
            cal_value = nutrients.get('calories', '')
            if cal_value:
                import re
                cal_match = re.search(r'(\d+)', str(cal_value))
                if cal_match:
                    calories = int(cal_match.group(1))
        
        result = {
            "is_recipe": True,
            "source_type": "web",
            "recipe_details": {
                "name": scraper.title() or "Untitled Recipe",
                "prep_time": prep_time,
                "cook_time": cook_time,
                "total_time": total_time,
                "servings": scraper.yields() if hasattr(scraper, 'yields') else None,
                "category": scraper.category() if hasattr(scraper, 'category') else None,
                "cuisine": scraper.cuisine() if hasattr(scraper, 'cuisine') else None,
                "calories": calories,
            },
            "ingredients": ingredients_list,
            "instructions": instructions_list,
            "main_image_url": scraper.image() if hasattr(scraper, 'image') else None,
            "tags": {
                "macro": [],
                "topic": [],
                "content": []
            }
        }
        
        logger.info(f"Successfully extracted recipe: {result['recipe_details']['name']}")
        return result
        
    except NoSchemaFoundInWildMode:
        logger.warning(f"No structured recipe data found, attempting fallback parsing")
        return fallback_extract(url, html)
    except Exception as e:
        logger.error(f"Error extracting recipe from {url}: {e}")
        raise ValueError(f"Could not extract recipe from URL: {e}")

def parse_ingredient_string(ingredient_str: str) -> Dict[str, Any]:
    """
    Parse an ingredient string like "2 cups all-purpose flour, sifted"
    into structured data.
    """
    import re
    
    quantity = None
    unit = None
    name = ingredient_str
    notes = None
    
    if ',' in ingredient_str:
        parts = ingredient_str.split(',', 1)
        ingredient_str = parts[0].strip()
        notes = parts[1].strip()
    
    if '(' in ingredient_str and ')' in ingredient_str:
        match = re.search(r'\(([^)]+)\)', ingredient_str)
        if match:
            if notes:
                notes = f"{match.group(1)}; {notes}"
            else:
                notes = match.group(1)
            ingredient_str = re.sub(r'\([^)]+\)', '', ingredient_str).strip()
    
    fraction_map = {
        '½': 0.5, '¼': 0.25, '¾': 0.75, '⅓': 0.333, '⅔': 0.667,
        '⅛': 0.125, '⅜': 0.375, '⅝': 0.625, '⅞': 0.875,
        '1/2': 0.5, '1/4': 0.25, '3/4': 0.75, '1/3': 0.333, '2/3': 0.667,
        '1/8': 0.125, '3/8': 0.375, '5/8': 0.625, '7/8': 0.875,
    }
    
    quantity_pattern = r'^([\d\s½¼¾⅓⅔⅛⅜⅝⅞]+(?:/\d+)?)\s*'
    match = re.match(quantity_pattern, ingredient_str)
    if match:
        qty_str = match.group(1).strip()
        ingredient_str = ingredient_str[match.end():].strip()
        
        try:
            if qty_str in fraction_map:
                quantity = fraction_map[qty_str]
            elif ' ' in qty_str:
                parts = qty_str.split()
                whole = float(parts[0])
                frac = fraction_map.get(parts[1], 0)
                quantity = whole + frac
            elif '/' in qty_str:
                num, denom = qty_str.split('/')
                quantity = float(num) / float(denom)
            else:
                quantity = float(qty_str)
        except (ValueError, ZeroDivisionError):
            pass
    
    units = [
        'tablespoons', 'tablespoon', 'tbsp', 'tbs', 'tb',
        'teaspoons', 'teaspoon', 'tsp', 'ts',
        'cups', 'cup', 'c',
        'ounces', 'ounce', 'oz',
        'pounds', 'pound', 'lbs', 'lb',
        'grams', 'gram', 'g',
        'kilograms', 'kilogram', 'kg',
        'milliliters', 'milliliter', 'ml',
        'liters', 'liter', 'l',
        'pints', 'pint', 'pt',
        'quarts', 'quart', 'qt',
        'gallons', 'gallon', 'gal',
        'pinch', 'pinches', 'dash', 'dashes',
        'cloves', 'clove', 'slices', 'slice',
        'pieces', 'piece', 'stalks', 'stalk',
        'sprigs', 'sprig', 'bunches', 'bunch',
        'cans', 'can', 'packages', 'package', 'pkg',
        'sticks', 'stick', 'heads', 'head',
        'large', 'medium', 'small',
    ]
    
    for u in units:
        pattern = rf'^{u}\b\.?\s*'
        match = re.match(pattern, ingredient_str, re.IGNORECASE)
        if match:
            unit = u.lower()
            if unit.endswith('s') and unit not in ['dashes', 'pinches']:
                unit = unit[:-1] if len(unit) > 3 else unit
            ingredient_str = ingredient_str[match.end():].strip()
            break
    
    name = ingredient_str.strip()
    if name.startswith('of '):
        name = name[3:]
    
    return {
        "name": name,
        "quantity": quantity,
        "unit": unit,
        "notes": notes
    }

def format_time(minutes: Optional[int]) -> Optional[str]:
    """Convert minutes to ISO 8601 duration format"""
    if not minutes:
        return None
    try:
        minutes = int(minutes)
        if minutes < 60:
            return f"PT{minutes}M"
        hours = minutes // 60
        remaining_minutes = minutes % 60
        if remaining_minutes == 0:
            return f"PT{hours}H"
        return f"PT{hours}H{remaining_minutes}M"
    except (ValueError, TypeError):
        return None

def fallback_extract(url: str, html: str) -> Dict[str, Any]:
    """
    Fallback extraction using BeautifulSoup when recipe-scrapers fails.
    Attempts to find common recipe patterns in HTML.
    """
    soup = BeautifulSoup(html, 'lxml')
    
    title = None
    title_tag = soup.find('h1')
    if title_tag:
        title = title_tag.get_text(strip=True)
    if not title:
        title_meta = soup.find('meta', property='og:title')
        if title_meta:
            title = title_meta.get('content', '')
    
    image_url = None
    img_meta = soup.find('meta', property='og:image')
    if img_meta:
        image_url = img_meta.get('content', '')
    
    return {
        "is_recipe": True,
        "source_type": "web",
        "recipe_details": {
            "name": title or "Untitled Recipe",
            "prep_time": None,
            "cook_time": None,
            "total_time": None,
            "servings": None,
            "category": None,
            "cuisine": None,
            "calories": None,
        },
        "ingredients": [],
        "instructions": [],
        "main_image_url": image_url,
        "tags": {
            "macro": [],
            "topic": [],
            "content": []
        }
    }

def detect_url_type(url: str) -> str:
    """Detect the type of URL for routing to the correct extractor."""
    if is_youtube_url(url):
        return "youtube"
    if is_social_media_url(url):
        parsed = urlparse(url)
        if 'instagram.com' in parsed.netloc:
            return "instagram"
        if 'tiktok.com' in parsed.netloc:
            return "tiktok"
        if 'facebook.com' in parsed.netloc or 'fb.watch' in parsed.netloc or 'fb.com' in parsed.netloc:
            return "facebook"
        return "social"
    return "web"
