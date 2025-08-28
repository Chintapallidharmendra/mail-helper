from sqlalchemy import String, DateTime, Boolean, Text
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import JSONB
from datetime import datetime
from .db import Base

class Email(Base):
    __tablename__ = "emails"

    id: Mapped[str] = mapped_column(String, primary_key=True)           # Gmail message id
    thread_id: Mapped[str] = mapped_column(String, index=True)
    from_email: Mapped[str] = mapped_column(String, index=True)
    to_email: Mapped[str] = mapped_column(Text)
    subject: Mapped[str] = mapped_column(Text, default="")
    snippet: Mapped[str] = mapped_column(Text, default="")
    body: Mapped[str] = mapped_column(Text, default="")
    received_at: Mapped[datetime] = mapped_column(DateTime, index=True)
    is_read: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    labels: Mapped[dict] = mapped_column(JSONB, default=dict)  # {"ids": [...], "names": [...]}
