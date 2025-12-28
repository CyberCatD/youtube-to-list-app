import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock

# Import the FastAPI app from your main application file
# Ensure this path is correct relative to your project structure
from src.main import app
from src.database import get_db, engine, Base
from src.models import Card as CardModel
from src.schemas import CardCreateSchema, VideoMetadataSchema
from datetime import datetime

client = TestClient(app)

# --- Fixtures for database and mocking --- 

@pytest.fixture(scope="module")
def test_db():
    """Provides a test database session."""
    # Create tables for testing
    Base.metadata.create_all(bind=engine)
    
    db = next(get_db())
    yield db
    
    # Clean up tables after tests
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def mock_youtube_service():
    """Mocks the youtube_service for API tests."""
    with patch("src.services.youtube_service.get_video_metadata") as mock_meta, \
         patch("src.services.youtube_service.get_video_transcript") as mock_transcript, \
         patch("src.services.youtube_service.extract_video_id") as mock_extract_id:
        # Default successful mocks
        mock_extract_id.return_value = "test_video_id"
        
        mock_meta_result = MagicMock(spec=VideoMetadataSchema)
        mock_meta_result.title = "Mock Test Video"
        mock_meta_result.url = "https://www.youtube.com/watch?v=test_video_id"
        mock_meta_result.thumbnail_url = "http://example.com/thumb.jpg"
        mock_meta_result.channel_name = "Test Channel"
        mock_meta_result.published_date = datetime(2024, 1, 1, 12, 0, 0)
        mock_meta.return_value = mock_meta_result
        
        mock_transcript.return_value = "This is a mock transcript for testing."
        
        yield mock_meta, mock_transcript, mock_extract_id


@pytest.fixture(scope="function")
def mock_llm_service():
    """Mocks the llm_service for API tests."""
    with patch("src.services.llm_service.generate_content_and_tags") as mock_generate:
        # Default successful mock response
        mock_generate.return_value = {
            "extracted_content": {
                "type": "Instructional Guide",
                "details": {"steps": [{"step_number": 1, "description": "Do this."}]}
            },
            "tags": {
                "macro": ["Guide"],
                "topic": ["Testing"],
                "content": ["Mocking"]
            }
        }
        yield mock_generate


# --- Test cases for API endpoints --- 

# Test for POST /api/v1/youtube/process-youtube-url
def test_process_youtube_url_success(
    test_db, mock_youtube_service, mock_llm_service
):
    mock_meta, mock_transcript, mock_extract_id = mock_youtube_service
    mock_generate = mock_llm_service

    youtube_url = "https://www.youtube.com/watch?v=test_video_id"
    
    response = client.post(
        "/api/v1/youtube/process-youtube-url",
        json={"youtube_url": youtube_url},
    )

    assert response.status_code == 201
    data = response.json()
    assert data["message"] == "Card created successfully."
    assert "card_id" in data
    assert data["video_title"] == "Mock Test Video"

    # Verify mocks were called
    mock_extract_id.assert_called_once_with(youtube_url)
    mock_meta.assert_called_once_with("test_video_id")
    mock_transcript.assert_called_once_with("test_video_id")
    mock_generate.assert_called_once()

    # Verify card was created in DB
    card_id = data["card_id"]
    db_card = test_db.query(CardModel).filter(CardModel.id == card_id).first()
    assert db_card is not None
    assert db_card.video_title == "Mock Test Video"
    assert db_card.extracted_content_type == "Instructional Guide"
    assert db_card.tags_macro == ["Guide"]


def test_process_youtube_url_invalid_url(
    test_db, mock_youtube_service, mock_llm_service
):
    youtube_url = "invalid-youtube-url"
    
    response = client.post(
        "/api/v1/youtube/process-youtube-url",
        json={"youtube_url": youtube_url},
    )

    assert response.status_code == 400
    data = response.json()
    assert "Invalid YouTube URL format" in data["detail"]

    # Ensure services were not called if URL is invalid early
    mock_meta, mock_transcript, mock_extract_id = mock_youtube_service
    mock_extract_id.assert_called_once_with(youtube_url)
    mock_meta.assert_not_called()
    mock_transcript.assert_not_called()
    mock_llm_service.assert_not_called()


def test_process_youtube_url_transcript_disabled(
    test_db, mock_youtube_service, mock_llm_service
):
    mock_meta, mock_transcript, mock_extract_id = mock_youtube_service
    
    # Configure mock to raise TranscriptDisabled exception
    mock_transcript.side_effect = ValueError("Transcripts are disabled for video ID: test_video_id")
    
    youtube_url = "https://www.youtube.com/watch?v=test_video_id"
    response = client.post(
        "/api/v1/youtube/process-youtube-url",
        json={"youtube_url": youtube_url},
    )

    assert response.status_code == 400
    data = response.json()
    assert "Transcript error" in data["detail"]

    # Verify correct mocks were called
    mock_extract_id.assert_called_once_with(youtube_url)
    mock_meta.assert_called_once_with("test_video_id")
    mock_transcript.assert_called_once_with("test_video_id")
    mock_llm_service.assert_not_called()


# Test for GET /api/v1/cards/{card_id}
def test_get_card_by_id_success(test_db, mock_youtube_service, mock_llm_service):
    # First, create a card to retrieve
    youtube_url = "https://www.youtube.com/watch?v=another_video"
    response_post = client.post(
        "/api/v1/youtube/process-youtube-url",
        json={"youtube_url": youtube_url},
    )
    assert response_post.status_code == 201
    card_id = response_post.json()["card_id"]

    # Now, retrieve the card
    response_get = client.get(f"/api/v1/cards/{card_id}")
    
    assert response_get.status_code == 200
    card_data = response_get.json()
    assert card_data["id"] == card_id
    assert card_data["video_title"] == "Mock Test Video" # From mock_youtube_service
    assert card_data["extracted_content_type"] == "Instructional Guide"


def test_get_card_by_id_not_found(test_db):
    non_existent_id = 9999
    response = client.get(f"/api/v1/cards/{non_existent_id}")
    
    assert response.status_code == 404
    data = response.json()
    assert f"Card with ID {non_existent_id} not found" in data["detail"]


# Test for GET /api/v1/cards
def test_list_cards_success(test_db, mock_youtube_service, mock_llm_service):
    # Create a couple of cards first
    url1 = "https://www.youtube.com/watch?v=video1"
    client.post("/api/v1/youtube/process-youtube-url", json={"youtube_url": url1})
    
    url2 = "https://www.youtube.com/watch?v=video2"
    client.post("/api/v1/youtube/process-youtube-url", json={"youtube_url": url2})

    # Retrieve the list of cards
    response = client.get("/api/v1/cards/")

    assert response.status_code == 200
    data = response.json()
    assert "cards" in data
    assert len(data["cards"]) >= 2 # Should have at least the two we created
    
    # Check if at least one card has expected structure
    if data["cards"]:
        first_card = data["cards"][0]
        assert "id" in first_card
        assert "video_title" in first_card
        assert "created_at" in first_card


def test_list_cards_empty(test_db):
    # Ensure no cards exist before this test if running in isolation
    # (test_db fixture should handle cleanup)
    response = client.get("/api/v1/cards/")
    
    assert response.status_code == 200
    data = response.json()
    assert "cards" in data
    assert data["cards"] == []


# Test for DELETE /api/v1/cards/{card_id}
def test_delete_card_by_id_success(test_db, mock_youtube_service, mock_llm_service):
    # First, create a card to delete
    youtube_url = "https://www.youtube.com/watch?v=video_to_delete"
    response_post = client.post(
        "/api/v1/youtube/process-youtube-url",
        json={"youtube_url": youtube_url},
    )
    assert response_post.status_code == 201
    card_id = response_post.json()["card_id"]

    # Now, delete the card
    response_delete = client.delete(f"/api/v1/cards/{card_id}")
    
    assert response_delete.status_code == 200
    deleted_card_data = response_delete.json()
    assert deleted_card_data["id"] == card_id
    assert deleted_card_data["video_title"] == "Mock Test Video"

    # Verify the card is no longer in the DB
    db_card = test_db.query(CardModel).filter(CardModel.id == card_id).first()
    assert db_card is None


def test_delete_card_by_id_not_found(test_db):
    non_existent_id = 9998
    response = client.delete(f"/api/v1/cards/{non_existent_id}")
    
    assert response.status_code == 404
    data = response.json()
    assert f"Card with ID {non_existent_id} not found" in data["detail"]

