# YouTube to Action List CLI

This application takes a YouTube URL as input, extracts key data points using an LLM, and compiles them into structured action lists or cards.

## Features

*   Processes YouTube URLs to extract video metadata.
*   Fetches video transcripts.
*   Uses Google Gemini API for content analysis and data extraction (recipes, protocols, guides).
*   Applies hierarchical tagging (macro, topic, content).
*   Stores extracted data as 'cards' in a SQLite database.
*   Provides a Command Line Interface (CLI) for interaction.

## Getting Started

### Prerequisites

*   Python 3.8+
*   `pip` package installer
*   Google API Key for Gemini (stored in `.env` file)

### Setup

1.  **Clone the repository:**
    ```bash
    # (Assuming you have cloned the repository already)
    cd youtube_to_list
    ```

2.  **Create and activate a virtual environment:**
    ```bash
    python3 -m venv venv
    source venv/bin/activate
    ```

3.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Configure API Keys:**
    Create a `.env` file in the root of the project directory (`youtube_to_list/`) and add your API keys:

    ```env
    GOOGLE_API_KEY=YOUR_GEMINI_API_KEY
    ```

### Usage

Run commands using the CLI script.

#### Process a YouTube URL

To process a YouTube video and create a card:

```bash
python -m cli --url <youtube_video_url>
```

*Example:*
```bash
python -m cli --url https://www.youtube.com/watch?v=dQw4w9WgXcQ
```

#### View all cards

To list all cards created:

```bash
python -m cli --list
```

#### View a specific card

To view a specific card by its ID:

```bash
python -m cli --card-id <card_id>
```

