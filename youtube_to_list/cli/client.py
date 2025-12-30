import requests
import json
import os
from urllib.parse import urlparse

# Assuming the backend is running locally on port 8000
# In a real app, this might come from config or environment variables
BACKEND_URL = "http://localhost:8000"


def process_youtube_url(youtube_url: str):
    """
    Sends a YouTube URL to the backend for processing.
    """
    if not is_valid_youtube_url(youtube_url):
        print(f"Error: Invalid YouTube URL format: {youtube_url}")
        return
        
    api_endpoint = f"{BACKEND_URL}/api/v1/youtube/process-youtube-url"
    payload = {"youtube_url": youtube_url}
    
    try:
        response = requests.post(api_endpoint, json=payload, timeout=60)
        response.raise_for_status() # Raise HTTPError for bad responses (4xx or 5xx)
        
        result = response.json()
        print(f"Successfully processed video: {result.get('video_title', 'N/A')}")
        print(f"Card ID: {result.get('card_id')}")
        print(f"Message: {result.get('message')}")
        
    except requests.exceptions.RequestException as e:
        print(f"Error communicating with backend: {e}")
        if response is not None and response.content:
            try:
                error_detail = response.json().get('detail', response.text)
                print(f"Backend error details: {error_detail}")
            except json.JSONDecodeError:
                print(f"Backend error details: {response.text}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")

def get_card_by_id(card_id: int):
    """
    Retrieves a specific card from the backend by its ID.
    """
    api_endpoint = f"{BACKEND_URL}/api/v1/cards/{card_id}"
    
    try:
        response = requests.get(api_endpoint, timeout=30)
        response.raise_for_status()
        
        card_data = response.json()
        print_card_details(card_data)
        
    except requests.exceptions.RequestException as e:
        print(f"Error communicating with backend: {e}")
        if response is not None and response.content:
            try:
                error_detail = response.json().get('detail', response.text)
                print(f"Backend error details: {error_detail}")
            except json.JSONDecodeError:
                print(f"Backend error details: {response.text}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")

def get_all_cards():
    """
    Retrieves a list of all cards from the backend.
    """
    api_endpoint = f"{BACKEND_URL}/api/v1/cards/"
    
    try:
        response = requests.get(api_endpoint, timeout=30)
        response.raise_for_status()
        
        cards_list = response.json().get("cards", [])
        if not cards_list:
            print("No cards found.")
            return
            
        print("--- All Cards ---")
        for card in cards_list:
            print_card_summary(card)
        print("-----------------")
        
    except requests.exceptions.RequestException as e:
        print(f"Error communicating with backend: {e}")
        if response is not None and response.content:
            try:
                error_detail = response.json().get('detail', response.text)
                print(f"Backend error details: {error_detail}")
            except json.JSONDecodeError:
                print(f"Backend error details: {response.text}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")

def delete_card(card_id: int):
    """
    Deletes a specific card by its ID via the backend.
    """
    api_endpoint = f"{BACKEND_URL}/api/v1/cards/{card_id}"
    
    try:
        response = requests.delete(api_endpoint, timeout=30)
        response.raise_for_status()
        
        deleted_card = response.json()
        print(f"Successfully deleted card ID: {deleted_card.get('id')}")
        print(f"Video Title: {deleted_card.get('video_title', 'N/A')}")
        
    except requests.exceptions.RequestException as e:
        print(f"Error communicating with backend: {e}")
        if response is not None and response.content:
            try:
                error_detail = response.json().get('detail', response.text)
                print(f"Backend error details: {error_detail}")
            except json.JSONDecodeError:
                print(f"Backend error details: {response.text}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")

def print_card_details(card_data):
    """
    Prints the full details of a card.
    """
    print(f"\n--- Card ID: {card_data.get('id')} ---")
    print(f"Video Title: {card_data.get('video_title', 'N/A')}")
    print(f"Video URL: {card_data.get('video_url', 'N/A')}")
    if card_data.get('thumbnail_url'):
        print(f"Thumbnail: {card_data.get('thumbnail_url')}")
    if card_data.get('channel_name'):
        print(f"Channel: {card_data.get('channel_name')}")
    if card_data.get('published_date'):
        print(f"Published: {card_data.get('published_date')}")
    
    print(f"\nContent Type: {card_data.get('extracted_content_type', 'N/A')}")
    
    print("\nExtracted Details:")
    details = card_data.get('extracted_content_details', {{}})
    if details:
        # Basic pretty print for details, could be enhanced for specific types
        print(json.dumps(details, indent=2))
    else:
        print("  No specific details extracted.")

    print("\nTags:")
    tags = card_data.get('tags', {{}})
    if tags.get('macro'): print(f"  Macro: {', '.join(tags.get('macro'))}")
    if tags.get('topic'): print(f"  Topic: {', '.join(tags.get('topic'))}")
    if tags.get('content'): print(f"  Content: {', '.join(tags.get('content'))}")
    if not tags.get('macro') and not tags.get('topic') and not tags.get('content'):
        print("  No tags found.")
        
    print(f"\nCreated At: {card_data.get('created_at', 'N/A')}")
    print("------------------")

def print_card_summary(card_data):
    """
    Prints a summary of a card.
    """
    print(f"- ID: {card_data.get('id')}, Title: {card_data.get('video_title', 'N/A')}, Type: {card_data.get('extracted_content_type', 'N/A')}, Created: {card_data.get('created_at', 'N/A')}")

def is_valid_youtube_url(url):
    """
    Basic validation for YouTube URL format.
    """
    try:
        result = urlparse(url)
        if not all([result.scheme, result.netloc]):
            return False

        if 'youtu.be' in result.netloc:
            # For youtu.be, the video ID is in the path.
            # We allow query parameters like 'si=' to be present.
            return result.path and result.path != '/'
        elif 'youtube.com' in result.netloc:
            # For youtube.com, we expect /watch path and 'v' query param.
            return result.path == '/watch' and 'v' in result.query
        else:
            return False
    except Exception:
        return False