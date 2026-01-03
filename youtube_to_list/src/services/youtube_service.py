import os
from datetime import datetime
import logging

from googleapiclient.discovery import build
from youtube_transcript_api import YouTubeTranscriptApi, NoTranscriptFound, TranscriptsDisabled
from dateutil import parser

from src.config import GOOGLE_API_KEY, YOUTUBE_API_KEY
from typing import List
from src.schemas import VideoMetadataSchema

logger = logging.getLogger(__name__)

youtube_api_service = build(
    "youtube", "v3", developerKey=YOUTUBE_API_KEY
)

def get_video_comments(video_id: str, max_results: int = 5) -> List[str]:
    """
    Fetches the top-level comments for a given video ID.
    """
    comments = []
    try:
        request = youtube_api_service.commentThreads().list(
            part="snippet",
            videoId=video_id,
            maxResults=max_results,
            order="relevance",
            textFormat="plainText"
        )
        response = request.execute()

        for item in response.get("items", []):
            comment = item["snippet"]["topLevelComment"]["snippet"]["textDisplay"]
            comments.append(comment)
            
        return comments

    except Exception as e:
        logger.error(f"Error fetching comments for {video_id}: {e}")
        return []

def check_transcript_availability(video_id: str) -> bool:
    """
    Checks if a transcript is available for the given video ID.
    Returns True if a transcript is available, False otherwise.
    """
    try:
        captions_request = youtube_api_service.captions().list(
            part="snippet",
            videoId=video_id
        )
        captions_response = captions_request.execute()
        return bool(captions_response.get("items"))
    except Exception as e:
        logger.error(f"An unexpected error occurred while checking transcript availability for {video_id}: {e}")
        return False


def get_video_metadata(video_id: str) -> VideoMetadataSchema:
    try:
        request = youtube_api_service.videos().list(
            part="snippet",
            id=video_id,
        )
        response = request.execute()

        if not response.get("items"):
            raise ValueError(f"Video with ID {video_id} not found.")

        snippet = response["items"][0]["snippet"]
        published_at_str = snippet.get("publishedAt")
        published_date = parser.isoparse(published_at_str) if published_at_str else None

        return VideoMetadataSchema(
            title=snippet.get("title"),
            description=snippet.get("description"),
            url=f"https://www.youtube.com/watch?v={video_id}",
            thumbnail_url=snippet.get("thumbnails", {}).get("high", {}).get("url", None),
            channel_name=snippet.get("channelTitle"),
            published_date=published_date,
        )

    except Exception as e:
        logger.error(f"Error fetching YouTube metadata for {video_id}: {e}")
        raise


def get_video_transcript(video_id: str, preferred_languages: list[str] = ["en", "en-US"]) -> str:
    try:
        # Updated to use new API (v1.2.3+)
        ytt_api = YouTubeTranscriptApi()
        transcript_list = ytt_api.list(video_id)
        
        transcript = transcript_list.find_transcript(preferred_languages)
        
        fetched_transcript = transcript.fetch()
        
        # In v1.2.3+, items are objects with .text attribute instead of dictionaries
        full_transcript = " ".join([item.text for item in fetched_transcript])
        return full_transcript
        
    except TranscriptsDisabled:
        raise ValueError(f"Transcripts are disabled for video ID: {video_id}")
    except NoTranscriptFound:
        raise ValueError(f"No transcript found for video ID: {video_id} in preferred languages.")
    except Exception as e:
        logger.error(f"Error fetching transcript for {video_id}: {e}")
        raise

def extract_video_id(youtube_url: str) -> str:
    if "v=" in youtube_url:
        return youtube_url.split("v=")[-1].split("&")[0]
    elif "youtu.be/" in youtube_url:
        return youtube_url.split("youtu.be/")[-1].split("?")[0]
    elif "/shorts/" in youtube_url:
        return youtube_url.split("/shorts/")[-1].split("?")[0]
    else:
        raise ValueError(f"Invalid YouTube URL format: {youtube_url}")
