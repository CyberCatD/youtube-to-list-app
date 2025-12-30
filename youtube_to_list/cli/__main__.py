import argparse
import sys

from cli.client import process_youtube_url, get_card_by_id, get_all_cards, delete_card

def main():
    parser = argparse.ArgumentParser(description="YouTube to Action List CLI")
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Process URL command
    process_parser = subparsers.add_parser("process", help="Process a YouTube URL to create an action list card.")
    process_parser.add_argument("--url", required=True, help="The YouTube video URL to process.")

    # List cards command
    list_parser = subparsers.add_parser("list", help="List all created action list cards.")

    # Get card by ID command
    card_parser = subparsers.add_parser("card", help="Get details of a specific card by its ID.")
    card_parser.add_argument("--card-id", type=int, required=True, help="The ID of the card to retrieve.")

    # Delete card by ID command
    delete_parser = subparsers.add_parser("delete", help="Delete a specific card by its ID.")
    delete_parser.add_argument("--card-id", type=int, required=True, help="The ID of the card to delete.")

    args = parser.parse_args()

    if args.command == "process":
        process_youtube_url(args.url)
    elif args.command == "list":
        get_all_cards()
    elif args.command == "card":
        get_card_by_id(args.card_id)
    elif args.command == "delete":
        delete_card(args.card_id)
    else:
        # If no command is provided, show help
        parser.print_help()

if __name__ == "__main__":
    main()
