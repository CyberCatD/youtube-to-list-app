import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# Build an absolute path for the database file to ensure it's always
# created in the 'youtube_to_list' project directory, regardless of
# where the application is run from.
# __file__ -> .../youtube_to_list/src/database.py
# os.path.dirname(__file__) -> .../youtube_to_list/src
# os.path.dirname(...) -> .../youtube_to_list
DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "youtube_cards.db")
SQLALCHEMY_DATABASE_URL = f"sqlite:///{DB_PATH}"


engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
