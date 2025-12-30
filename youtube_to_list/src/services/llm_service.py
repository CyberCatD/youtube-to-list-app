import google.generativeai as genai
from src.config import GOOGLE_API_KEY
from src.schemas import VideoMetadataSchema, TagsSchema
from typing import Dict, Any, List


genai.configure(api_key=GOOGLE_API_KEY)

# Model configuration
MODEL_NAME = "gemini-2.5-flash"


def generate_content_and_tags(
    metadata: VideoMetadataSchema,
    transcript: str,
) -> Dict[str, Any]:
    """
    Sends the transcript and video metadata to the Gemini API for content extraction and tagging.
    Returns a dictionary containing the extracted content and tags.
    """
    prompt = f"""
    You are an AI assistant tasked with transforming video content into structured, actionable data.
    
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

    **JSON OUTPUT STRUCTURE:**
    Your entire output must be a single, valid JSON object with the following structure. Do not include any text or markdown outside of this JSON.

    ```json
    {{
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
      "card_color": "string"
    }}
    ```

    **DETAILED INSTRUCTIONS:**

    -   **`recipe_details`**: Fill this with the overall information about the recipe. Convert all times to ISO 8601 duration format.
    -   **`ingredients`**: Create a list of all ingredients. Each ingredient must be an object with `name`, `quantity`, `unit`, and optional `notes`. Be as precise as possible.
    -   **`instructions`**: Create a list of all steps. Each step must be a separate object with a `step_number`, an optional `section_name`, and a `description` of the action.
    -   **`card_color`**: Choose a color from the provided list based on the recipe's category.

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
        
        # Clean the response to ensure it's valid JSON
        # The API sometimes returns the JSON wrapped in markdown-like backticks
        cleaned_response_text = response.text.strip().replace('```json', '').replace('```', '').strip()
        
        # Parse the JSON response
        response_data = json.loads(cleaned_response_text)
        
        return response_data
        
    except (json.JSONDecodeError, AttributeError) as e:
        print(f"Error parsing LLM response: {e}")
        # Return a default structure on parsing failure to avoid breaking the calling service
        return {
            "extracted_content": {
                "type": "General Information",
                "details": {"summary": "Could not parse data from video transcript."}
            },
            "tags": {
                "macro": ["Error"],
                "topic": ["Parsing"],
                "content": []
            }
        }
    except Exception as e:
        print(f"An unexpected error occurred with the Gemini API: {e}")
        raise RuntimeError("Failed to get a valid response from Gemini API.") from e
import json