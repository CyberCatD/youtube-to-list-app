# inspect_api.py
import inspect
from youtube_transcript_api import YouTubeTranscriptApi

print("--- Inspecting the YouTubeTranscriptApi class ---")

# Get all members of the class
members = inspect.getmembers(YouTubeTranscriptApi)

print("\nMethods found:")
for name, member_type in members:
    if inspect.isfunction(member_type) or inspect.ismethod(member_type):
        print(f"- {name}")

print("\nAll attributes and methods:")
# Use dir() for a comprehensive list of attributes
for attr in dir(YouTubeTranscriptApi):
    if not attr.startswith('__'):
        print(f"- {attr}")

print("\n--- Inspection complete ---")
