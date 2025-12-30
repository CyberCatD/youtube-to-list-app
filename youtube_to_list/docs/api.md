# API Documentation

This document outlines the available API endpoints for the YouTube to Action List CLI backend service.

## Base URL

All API endpoints are prefixed with `/api/v1/`.

For local development, the base URL is typically `http://localhost:8000`.

---

## Endpoints

### YouTube Processing

#### `POST /api/v1/youtube/process-youtube-url`

**Description:** Processes a given YouTube URL, fetches its metadata and transcript, uses an LLM to extract structured content and tags, and saves it as a card in the database.

**Request Body:**

```json
{
  "youtube_url": "string"
}
```

**Responses:**

*   **201 Created:** Success.
    ```json
    {
      "message": "Card created successfully.",
      "card_id": 123, 
      "video_title": "Example Video Title"
    }
    ```

*   **400 Bad Request:** Invalid input (e.g., invalid URL format, transcript not available, video disabled).
    ```json
    {
      "error": "Descriptive error message."
    }
    ```

*   **500 Internal Server Error:** An unexpected error occurred during processing (e.g., LLM failure, backend service issue).
    ```json
    {
      "error": "An unexpected error occurred: ..."
    }
    ```

---

### Cards

#### `GET /api/v1/cards/{card_id}`

**Description:** Retrieves a specific action list card by its unique ID.

**Path Parameters:**

*   `card_id` (integer, required): The ID of the card to retrieve.

**Responses:**

*   **200 OK:** Success. Returns the full card details.
    ```json
    {
      "id": 123,
      "video_metadata": {
        "title": "Example Video Title",
        "url": "https://www.youtube.com/watch?v=example123",
        "thumbnail_url": "http://example.com/thumb.jpg",
        "channel_name": "Example Channel",
        "published_date": "2024-01-15T12:30:00Z"
      },
      "extracted_content_type": "Instructional Guide",
      "extracted_content_details": {
        "steps": [
          {"step_number": 1, "description": "Do this."}
        ]
      },
      "tags": {
        "macro": ["Guide"],
        "topic": ["Example Topic"],
        "content": ["Example Item"]
      },
      "created_at": "2024-01-15T13:00:00Z"
    }
    ```

*   **404 Not Found:** The specified card ID does not exist.
    ```json
    {
      "error": "Card with ID 123 not found."
    }
    ```

*   **500 Internal Server Error:** An unexpected error occurred.
    ```json
    {
      "error": "An unexpected error occurred: ..."
    }
    ```

#### `GET /api/v1/cards/`

**Description:** Retrieves a list of all action list cards created. The list is ordered by creation date (newest first).

**Query Parameters:**

*(None for MVP. Future enhancements may include filtering and pagination.)*

**Responses:**

*   **200 OK:** Success. Returns a list of card summaries.
    ```json
    {
      "cards": [
        {
          "id": 123,
          "video_title": "Example Video Title",
          "extracted_content_type": "Instructional Guide",
          "created_at": "2024-01-15T13:00:00Z"
        },
        {
          "id": 122,
          "video_title": "Another Video Title",
          "extracted_content_type": "Recipe",
          "created_at": "2024-01-14T10:00:00Z"
        }
      ]
    }
    ```

*   **500 Internal Server Error:** An unexpected error occurred.
    ```json
    {
      "error": "An unexpected error occurred: ..."
    }
    ```

---

### Health Check

#### `GET /health`

**Description:** Checks the health status of the API server.

**Responses:**

*   **200 OK:** The API is running.
    ```json
    {
      "status": "ok"
    }
    ```
