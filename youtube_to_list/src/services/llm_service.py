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
    
    Based on the transcript and video details, identify the primary content type (e.g., "Recipe", "Health Protocol", "Instructional Guide", "General Information") and extract the relevant details. Then, generate hierarchical tags and a list of actionable steps.
    
    **CRITICAL INSTRUCTIONS:**
    1.  The **video description is the primary source of truth** for creating the `action_steps`. Use it to build the most complete and accurate instructions.
    2.  If the transcript is empty, rely *only* on the description.
    3.  If the transcript is present, use it to supplement the description, but the description still takes priority for specific details like ingredient quantities, dosages, or product names.
    
    Output the result as a JSON object with the following structure:
    ```json
    {{
      "extracted_content": {{
        "type": "string",
        "details": {{}}
      }},
      "tags": {{
        "macro": [],
        "topic": [],
        "content": []
      }},
      "action_steps": [],
      "card_color": "string"
    }}
    ```
    
    Choose a `card_color` from the following list based on the video's primary topic:
    - `#FFADAD` (Pastel Red/Pink - for meats, poultry, some desserts)
    - `#FFD6A5` (Pastel Orange - for soups, stews, autumn recipes)
    - `#FDFFB6` (Pastel Yellow - for pastries, breakfast, pasta)
    - `#CAFFBF` (Pastel Green - for salads, vegetables, healthy dishes)
    - `#9BF6FF` (Pastel Blue - for seafood, drinks)
    - `#A0C4FF` (Pastel Indigo - for general guides, DIY, tech)
    - `#BDB2FF` (Pastel Violet - for health protocols, science, learning)
    - `#FFC6FF` (Pastel Magenta - for desserts, sweets, creative projects)
    - `#EAEAEA` (Pastel Gray - for general information, miscellaneous)
    
    The "action_steps" should be a list of clear, concise, and sequential instructions suitable for a checklist. 
    - For recipes, **each step must include quantities** (e.g., "Combine 1.5 cups of flour and 2 tbsp of sugar.").
    - For protocols, **each step must include dosages** (e.g., "Administer 5mg of BPC 157 daily.").
    - If a quantity or dosage is mentioned in the transcript but the exact amount is unclear, use a placeholder like `[unspecified amount]`. If it is not mentioned at all, do not include a placeholder.
    
    Detailed structure examples (only use these when applicable to the content):
    
    **For Recipe type:**
    ```json
    {{
      "extracted_content": {{
        "type": "Recipe",
        "details": {{
          "ingredients": [
            {{"item": "Flour", "quantity": "1.5 cups"}},
            {{"item": "Sugar", "quantity": "2 tbsp"}}
          ],
          "instructions": [
            "Step 1: Whisk together flour, sugar, baking powder, and salt.",
            "Step 2: Whisk together milk and egg."
          ]
        }}
      }},
      "tags": {{
        "macro": ["Cooking"],
        "topic": ["Pancakes", "Breakfast"],
        "content": ["Flour", "Eggs"]
      }},
      "action_steps": [
        "Combine 1.5 cups of flour and 2 tbsp of sugar in a large bowl.",
        "Whisk in 1 tsp of baking powder.",
        "In a separate bowl, mix 1 cup of milk and 1 egg.",
        "Pour wet ingredients into the dry ingredients and mix until just combined.",
        "Cook pancakes on a preheated griddle for 2 minutes per side."
      ]
    }}```
    
    **For Health Protocol type:**
    ```json
    {{
      "extracted_content": {{
        "type": "Health Protocol",
        "details": {{
          "protocol_name": "BPC 157",
          "dosage": "5mg",
          "frequency": "Once daily"
        }}
      }},
      "tags": {{
        "macro": ["Health"],
        "topic": ["Peptides"],
        "content": ["BPC 157"]
      }},
      "action_steps": [
        "Take 5mg of BPC 157 in the morning.",
        "Administer Cerebrolysin [unspecified dose] weekly.",
        "Continue protocol for 4-6 weeks."
      ]
    }}```
    
    **For Instructional Guide type:**
    ```json
    {{
      "extracted_content": {{
        "type": "Instructional Guide",
        "details": {{
          "steps": [
            {{"step_number": 1, "description": "Unpack the components..."}},
            {{"step_number": 2, "description": "Assemble part A with part B..."}}
          ]
        }}
      }},
      "tags": {{
        "macro": ["Guide"],
        "topic": ["DIY", "Assembly"],
        "content": ["Screws", "Manual"]
      }},
      "action_steps": [
        "Unpack all components from the box.",
        "Attach part A to part B using the 4 provided screws.",
        "Verify all connections are secure before use."
      ]
    }}```
    
    **For General Information type:**
    ```json
    {{
      "extracted_content": {{
        "type": "General Information",
        "details": {{
          "summary": "The video discusses the key aspects of quantum computing..."
        }}
      }},
      "tags": {{
        "macro": ["Science"],
        "topic": ["Quantum Computing"],
        "content": ["Qubits", "Superposition"]
      }},
      "action_steps": []
    }}```
    
    Ensure your output is ONLY valid JSON. Do not include any introductory phrases, explanations, or markdown formatting around the JSON itself. The entire output must be a single, valid JSON object.
    
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