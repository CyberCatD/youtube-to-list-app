from dotenv import load_dotenv
import os

load_dotenv()

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")

DEFAULT_RECIPE_LANGUAGE = os.getenv("DEFAULT_RECIPE_LANGUAGE", "English")

if not GOOGLE_API_KEY:
    raise ValueError("GOOGLE_API_KEY not found in environment variables. Please set it in your .env file.")

if not YOUTUBE_API_KEY:
    raise ValueError("YOUTUBE_API_KEY not found in environment variables. Please set it in your .env file.")