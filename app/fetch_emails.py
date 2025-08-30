from datetime import datetime
from .db import get_session, Base, engine
from .models import Email
from .gmail_client import list_messages, get_message, parse_headers, extract_plain_text


def init_db():
    print("Creating database tables...")
    print("Using engine:", engine)
    Base.metadata.create_all(engine)


def fetch_and_store(max_results: int = 100):
    session = get_session()
    try:
        msgs = list_messages(max_results=max_results)
        for m in msgs:
            msg = get_message(m["id"])
            headers = parse_headers(msg["payload"].get("headers", []))
            frm = headers.get("from", "")
            to = headers.get("to", "")
            subject = headers.get("subject", "")
            date_raw = headers.get("date", "")
            # Parse RFC2822 date
            from email.utils import parsedate_to_datetime

            received_at = (
                parsedate_to_datetime(date_raw) if date_raw else datetime.utcnow()
            )

            snippet = msg.get("snippet", "") or ""
            body = extract_plain_text(msg.get("payload", {})) or ""

            label_ids = msg.get("labelIds", [])
            is_read = "UNREAD" not in label_ids

            # Upsert-like behavior
            existing = session.get(Email, m["id"])
            if existing:
                existing.thread_id = msg.get("threadId", "")
                existing.from_email = frm
                existing.to_email = to
                existing.subject = subject
                existing.snippet = snippet
                existing.body = body
                existing.received_at = received_at
                existing.is_read = is_read
                existing.labels = {"ids": label_ids}
            else:
                session.add(
                    Email(
                        id=m["id"],
                        thread_id=msg.get("threadId", ""),
                        from_email=frm,
                        to_email=to,
                        subject=subject,
                        snippet=snippet,
                        body=body,
                        received_at=received_at,
                        is_read=is_read,
                        labels={"ids": label_ids},
                    )
                )
        session.commit()
        return len(msgs)
    finally:
        session.close()
