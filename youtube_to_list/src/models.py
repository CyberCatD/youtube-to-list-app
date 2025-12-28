from sqlalchemy import Column, Integer, String, DateTime, JSON
from .database import Base  # Import the central Base
from datetime import datetime

# Base = declarative_base() # REMOVE this line

class Card(Base):
    __tablename__ = "cards"

    id = Column(Integer, primary_key=True, index=True)
    video_url = Column(String, index=True)
    video_title = Column(String, index=True)
    thumbnail_url = Column(String)
    channel_name = Column(String)
    published_date = Column(DateTime)
    extracted_content_type = Column(String)
    extracted_content_details = Column(JSON)
    tags_macro = Column(JSON)
    tags_topic = Column(JSON)
    tags_content = Column(JSON)
    action_steps = Column(JSON, nullable=True)
    card_color = Column(String, nullable=True) # To store the pastel color for the card
    created_at = Column(DateTime, default=datetime.utcnow)
