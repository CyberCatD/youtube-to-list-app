import google.generativeai as genai
from src.config import GOOGLE_API_KEY
from src.schemas import VideoMetadataSchema, TagsSchema
from typing import Dict, Any, List
import json
import logging

logger = logging.getLogger(__name__)

genai.configure(api_key=GOOGLE_API_KEY)

MODEL_NAME = "gemini-2.5-flash"


def generate_content_and_tags(
    metadata: VideoMetadataSchema,
    transcript: str,
) -> Dict[str, Any]:
    """
    Sends the transcript and video metadata to the Gemini API for content extraction and tagging.
    Returns a dictionary containing the extracted content and tags.
    Raises ValueError if content is not a recipe/cooking video.
    """
    prompt = f"""
    You are an AI assistant tasked with transforming video content into structured, actionable data.
    
    **FIRST STEP - CONTENT VALIDATION:**
    Analyze if this video is about COOKING, FOOD PREPARATION, or RECIPES. 
    - Videos about cooking techniques, recipes, meal prep, baking, etc. → PROCEED
    - Videos about food reviews, restaurant tours, food challenges, non-food topics → REJECT
    
    If this is NOT a cooking/recipe video, respond ONLY with:
    {{"is_recipe": false, "reason": "Brief explanation of why this is not a recipe video"}}
    
    If this IS a cooking/recipe video, proceed with full extraction.
    
    Analyze the following YouTube video transcript and its accompanying description to extract key information.
    The video details are:
    - Title: {metadata.title}
    - Channel: {metadata.channel_name}
    - URL: {metadata.url}
    
    **Video Description:**
    ---
    {metadata.description}
    ---
    
    **Top Comments:**
    ---
    {metadata.comments}
    ---
    
    **CRITICAL INSTRUCTIONS (GENERAL):**
    1.  Your primary goal is to extract structured data for a recipe or protocol.
    2.  Use the video description, comments, and transcript as your sources. The description and comments are the most reliable sources for specific details.
    3.  **CRITICAL - Missing Data Handling**: When specific information is not provided in the video:
        - For **timing** (prep_time, cook_time): Estimate based on the recipe complexity and cooking methods shown. If uncertain, use reasonable defaults (e.g., simple recipes: PT10M prep, PT15M cook).
        - For **ingredient quantities**: If not specified, extrapolate based on the number of servings (default to 2-4 servings if not mentioned). Set quantity to 0 ONLY if it's truly "to taste" (salt, pepper, herbs).
        - For **servings**: If not stated, estimate based on ingredient quantities (typically 2-4 servings for most recipe videos).
    4.  Provide complete, usable data rather than leaving fields empty.

    **JSON OUTPUT STRUCTURE:**
    Your entire output must be a single, valid JSON object with the following structure. Do not include any text or markdown outside of this JSON.

    ```json
    {{
      "is_recipe": true,
      "recipe_details": {{
        "name": "string",
        "prep_time": "string (ISO 8601 format, e.g., PT30M)",
        "cook_time": "string (ISO 8601 format, e.g., PT1H)",
        "total_time": "string (ISO 8601 format, e.g., PT1H30M)",
        "servings": "string",
        "category": "string (e.g., Dessert, Main Course)",
        "cuisine": "string (e.g., Italian, Mexican)",
        "calories": "integer"
      }},
      "ingredients": [
        {{
          "name": "string",
          "quantity": "float",
          "unit": "string (e.g., cups, tbsp, grams)",
          "notes": "string (e.g., sifted, softened)"
        }}
      ],
      "instructions": [
        {{
          "step_number": "integer",
          "section_name": "string (e.g., For the Cake, For the Frosting)",
          "description": "string"
        }}
      ],
      "tags": {{
        "macro": [],
        "topic": [],
        "content": []
      }},
      "main_image_url": "string (URL for the main dish image, fallback to thumbnail)"
    }}
    ```

    **DETAILED INSTRUCTIONS:**

    -   **`recipe_details`**: Fill this with the overall information about the recipe. Convert all times to ISO 8601 duration format (e.g., PT15M for 15 minutes, PT1H30M for 1 hour 30 minutes).
        - **`prep_time`**: Time spent on preparation (chopping, mixing, etc.) BEFORE cooking starts. Look for phrases like "prep time", "preparation", "mise en place" in the video. **If not stated, estimate based on recipe complexity** (simple: PT5M-PT10M, complex: PT20M-PT30M).
        - **`cook_time`**: Active cooking time (time on stove, in oven, etc.). Look for "cook time", "cooking", "baking time". **If not stated, estimate based on cooking methods shown** (sautéing: PT10M-PT15M, baking: PT30M-PT45M).
        - **`total_time`**: Sum of prep_time and cook_time. Calculate even if individual times are estimated.
        - **`servings`**: Number of servings. **If not stated, estimate from ingredient quantities** (default: "2-4" for typical home cooking).
    -   **`main_image_url`**: **CRITICAL**: ALWAYS use the thumbnail URL: {metadata.thumbnail_url}. Do NOT leave this field empty. Do NOT try to find other images. Use the thumbnail provided.
    -   **`ingredients`**: Create a list of all ingredients. Each ingredient must be an object with `name`, `quantity`, `unit`, and optional `notes`.
        - **For missing quantities**: Estimate reasonable amounts based on servings and typical recipe ratios. For example, if making 4 servings of salmon, estimate ~6 oz per fillet.
        - Set `quantity` to 0 ONLY for truly variable items like "salt to taste", "pepper to taste", "herbs for garnish".
        - **For main proteins/vegetables**: Always provide quantity estimates if not stated (e.g., "4 salmon fillets" → quantity: 4, unit: "fillets").
        - Be as precise as possible with measurements.
    -   **`instructions`**: Create a list of all steps. Each step must be a separate object with a `step_number`, an optional `section_name`, and a `description` of the action.

    **COLOR PALETTE:**
    -   `#FFADAD` (Red/Pink)
    -   `#FFD6A5` (Orange)
    -   `#FDFFB6` (Yellow)
    -   `#CAFFBF` (Green)
    -   `#9BF6FF` (Blue)
    -   `#A0C4FF` (Indigo)
    -   `#BDB2FF` (Violet)
    -   `#FFC6FF` (Magenta)
    -   `#EAEAEA` (Gray)

    Full Transcript:
    ---
    {transcript}
    ---
    """
    try:
        model = genai.GenerativeModel(MODEL_NAME)
        response = model.generate_content(prompt)
        
        cleaned_response_text = response.text.strip().replace('```json', '').replace('```', '').strip()
        
        response_data = json.loads(cleaned_response_text)
        
        # Check if this is a recipe video
        if not response_data.get("is_recipe", True):
            reason = response_data.get("reason", "This video is not about cooking or recipe preparation")
            logger.warning(f"Non-recipe video detected: {reason}")
            raise ValueError(f"Not a recipe video: {reason}")
        
        return response_data
        
    except (json.JSONDecodeError, AttributeError) as e:
        logger.error(f"Error parsing LLM response: {e}")
        raise ValueError("Could not parse recipe data from video. The video might not contain a clear recipe.")
    except ValueError as ve:
        # Re-raise ValueError (includes non-recipe detection)
        raise
    except Exception as e:
        logger.error(f"An unexpected error occurred with the Gemini API: {e}")
        raise RuntimeError("Failed to get a valid response from Gemini API.") from e
