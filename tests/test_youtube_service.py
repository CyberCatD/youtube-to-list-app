import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime

from src.services.youtube_service import get_video_metadata, get_video_transcript, extract_video_id
from src.schemas import VideoMetadataSchema


# --- Tests for extract_video_id --- 

def test_extract_video_id_standard_url():
    url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
    assert extract_video_id(url) == "dQw4w9WgXcQ"

def test_extract_video_id_short_url():
    url = "https://youtu.be/dQw4w9WgXcQ"
    assert extract_video_id(url) == "dQw4w9WgXcQ"

def test_extract_video_id_with_other_params():
    url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ&t=10s&feature=youtu.be"
    assert extract_video_id(url) == "dQw4w9WgXcQ"

def test_extract_video_id_invalid_format():
    url = "https://example.com/video/123"
    with pytest.raises(ValueError, match="Invalid YouTube URL format"):
        extract_video_id(url)


# --- Mocking setup for get_video_metadata and get_video_transcript --- 

@pytest.fixture
def mock_youtube_api(monkeypatch):
    # Mocking googleapiclient.discovery.build
    mock_service = MagicMock()
    mock_videos_resource = MagicMock()
    mock_request_resource = MagicMock()
    
    mock_service.videos.return_value = mock_videos_resource
    mock_videos_resource.list.return_value = mock_request_resource
    
    # Mocking response.execute() for get_video_metadata
    def mock_execute_metadata():
        return {
            "items": [
                {
                    "snippet": {
                        "title": "Mock Video Title",
                        "publishedAt": "2023-10-27T10:00:00Z",
                        "thumbnails": {"high": {"url": "http://example.com/thumbnail.jpg"}},
                        "channelTitle": "Mock Channel"
                    }
                }
            ]
        }
    mock_request_resource.execute.side_effect = mock_execute_metadata
    
    # Patching the build function globally for youtube_service module
    # Need to ensure the patching path is correct relative to where it's used
    # It's used in src/services/youtube_service.py
    
    # This is a bit tricky. The `build` is called within `youtube_service.py`.
    # We need to patch `googleapiclient.discovery.build` from the perspective of youtube_service.
    # So, the path should be 'src.services.youtube_service.build'
    
    patcher = patch('src.services.youtube_service.build', return_value=mock_service)
    mocked_build = patcher.start()
    yield mock_service
    patcher.stop()


@pytest.fixture
def mock_transcript_api():
    # Mocking youtube_transcript_api.YouTubeTranscriptApi
    mock_transcript_list = MagicMock()
    mock_transcript = MagicMock()
    
    # Mocking find_transcript and fetch
    mock_transcript_list.find_transcript.return_value = mock_transcript
    mock_transcript.fetch.return_value = [
        {'text': 'This is the first part of the transcript.', 'start': 0.0, 'duration': 3.5},
        {'text': 'This is the second part.', 'start': 3.5, 'duration': 2.0}
    ]
    
    # Patching the YouTubeTranscriptApi class
    patcher = patch('src.services.youtube_service.YouTubeTranscriptApi', autospec=True)
    mock_api = patcher.start()
    mock_api.list_transcripts.return_value = mock_transcript_list
    yield mock_api
    patcher.stop()


# --- Tests for get_video_metadata --- 

@pytest.com.patch('src.services.youtube_service.build')
def test_get_video_metadata(mock_build):
    # Configure the mock for this specific test
    mock_service_instance = mock_build.return_value
    mock_videos_resource = mock_service_instance.videos.return_value
    mock_request_resource = mock_videos_resource.list.return_value
    
    mock_request_resource.execute.return_value = {
        "items": [
            {
                "snippet": {
                    "title": "Test Video",
                    "publishedAt": "2024-01-15T12:30:00Z",
                    "thumbnails": {"high": {"url": "http://example.com/thumb.png"}},
                    "channelTitle": "Test Channel"
                }
            }
        ]
    }

    video_id = "test_video_id"
    metadata = get_video_metadata(video_id)

    assert isinstance(metadata, VideoMetadataSchema)
    assert metadata.title == "Test Video"
    assert metadata.url == "https://www.youtube.com/watch?v=test_video_id"
    assert metadata.thumbnail_url == "http://example.com/thumb.png"
    assert metadata.channel_name == "Test Channel"
    assert metadata.published_date == datetime(2024, 1, 15, 12, 30, 0)

    mock_videos_resource.list.assert_called_once_with(part="snippet", id=video_id)


@pytest.mark.parametrize("video_id, expected_error_msg", [
    ("", "Video with ID  not found."), # Empty ID
    ("invalid_id", "Video with ID invalid_id not found.") # Non-existent ID
])
@pytest.com.patch('src.services.youtube_service.build')
def test_get_video_metadata_not_found(mock_build, video_id, expected_error_msg):
    mock_service_instance = mock_build.return_value
    mock_videos_resource = mock_service_instance.videos.return_value
    mock_request_resource = mock_videos_resource.list.return_value
    
    # Simulate API returning no items
    mock_request_resource.execute.return_value = {"items": []}

    with pytest.raises(ValueError, match=expected_error_msg):
        get_video_metadata(video_id)


# --- Tests for get_video_transcript --- 

@patch('src.services.youtube_service.YouTubeTranscriptApi')
def test_get_video_transcript_success(MockYouTubeTranscriptApi):
    # Mock the list_transcripts and fetch methods
    mock_transcript_list = MagicMock()
    mock_transcript = MagicMock()
    
    MockYouTubeTranscriptApi.list_transcripts.return_value = mock_transcript_list
    mock_transcript_list.find_transcript.return_value = mock_transcript
    mock_transcript.fetch.return_value = [
        {'text': 'First line.', 'start': 0.0, 'duration': 1.0},
        {'text': 'Second line.', 'start': 1.0, 'duration': 1.0}
    ]

    video_id = "some_video_id"
    transcript = get_video_transcript(video_id)

    assert transcript == "First line. Second line."
    MockYouTubeTranscriptApi.list_transcripts.assert_called_once_with(video_id)
    mock_transcript_list.find_transcript.assert_called_once_with(["en", "en-US"])


@patch('src.services.youtube_service.YouTubeTranscriptApi')
def test_get_video_transcript_no_transcript_found(MockYouTubeTranscriptApi):
    video_id = "video_no_transcript"
    
    # Simulate NoTranscriptFound exception when finding preferred language
    mock_transcript_list = MagicMock()
    MockYouTubeTranscriptApi.list_transcripts.return_value = mock_transcript_list
    mock_transcript_list.find_transcript.side_effect = NoTranscriptFound
    
    # Simulate fetching any available transcript
    mock_transcript = MagicMock()
    mock_transcript_list.fetch.return_value = [
        {'text': 'Fallback transcript.', 'start': 0.0, 'duration': 1.0}
    ]

    transcript = get_video_transcript(video_id)
    assert transcript == "Fallback transcript."
    MockYouTubeTranscriptApi.list_transcripts.assert_called_once_with(video_id)
    mock_transcript_list.find_transcript.assert_called_once_with(["en", "en-US"])


@patch('src.services.youtube_service.YouTubeTranscriptApi')
def test_get_video_transcript_transcripts_disabled(MockYouTubeTranscriptApi):
    video_id = "video_disabled_transcript"
    MockYouTubeTranscriptApi.list_transcripts.side_effect = TranscriptsDisabled

    with pytest.raises(ValueError, match=f"Transcripts are disabled for video ID: {video_id}"):
        get_video_transcript(video_id)

@patch('src.services.youtube_service.YouTubeTranscriptApi')
def test_get_video_transcript_no_transcript_at_all(MockYouTubeTranscriptApi):
    video_id = "video_no_transcript_at_all"
    mock_transcript_list = MagicMock()
    MockYouTubeTranscriptApi.list_transcripts.return_value = mock_transcript_list
    mock_transcript_list.find_transcript.side_effect = NoTranscriptFound
    mock_transcript_list.fetch.side_effect = NoTranscriptFound # Also raise when fetching any

    with pytest.raises(ValueError, match=f"No transcript found for video ID: {video_id}"):
        get_video_transcript(video_id)

