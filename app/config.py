from pydantic import BaseModel
from dotenv import load_dotenv
import os

load_dotenv()

class Settings(BaseModel):
    DATABASE_URL: str = os.getenv("DATABASE_URL", "postgresql+psycopg2://postgres:postgres@localhost:5432/mailhelper")
    GMAIL_CREDENTIALS_PATH: str = os.getenv("GMAIL_CREDENTIALS_PATH", "./credentials.json")
    GMAIL_TOKEN_PATH: str = os.getenv("GMAIL_TOKEN_PATH", "./token.json")
    GMAIL_USER_ID: str = os.getenv("GMAIL_USER_ID", "me")
    DEFAULT_MOVE_LABEL: str = os.getenv("DEFAULT_MOVE_LABEL", "Processed")

settings = Settings()
