from dotenv import load_dotenv
import os

load_dotenv()

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY") # New API key for YouTube

if not GOOGLE_API_KEY:
    raise ValueError("GOOGLE_API_KEY not found in environment variables. Please set it in your .env file.")

if not YOUTUBE_API_KEY:
    raise ValueError("YOUTUBE_API_KEY not found in environment variables. Please set it in your .env file.")