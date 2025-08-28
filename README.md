# Gmail Rules App (Python + PostgreSQL)

A standalone Python application that:
1) Authenticates with the Gmail API (OAuth2, no IMAP),
2) Fetches emails into a PostgreSQL database,
3) Applies JSON-configured rules to perform actions (mark read/unread, move to label) using Gmail REST API.

## Tech
- Python 3.10+
- PostgreSQL
- SQLAlchemy ORM
- Google Gmail API (google-api-python-client)
- Typer CLI
- dotenv for config

## Setup

### 1) Create a Google Cloud OAuth Client
- Go to Google Cloud Console → APIs & Services → Credentials.
- Create OAuth client ID of type **Desktop app**.
- Download the JSON and save it as `credentials.json` in the project root (or set a custom path in `.env`).

Enable the Gmail API for your project (APIs & Services → Library → enable **Gmail API**).

### 2) Environment
```bash
cp .env.example .env
# Edit .env to set your DATABASE_URL, paths and Gmail user id.
```

### 3) Create database
```bash
createdb gmail_rules   # or use psql/GUI; update .env accordingly
```

### 4) Install dependencies
```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### 5) First auth & DB init
```bash
python -m app.cli init-db
python -m app.cli auth
```
- A browser window will ask you to grant access. Token is saved to `GMAIL_TOKEN_PATH` from `.env` (default `./token.json`).

### 6) Fetch emails
```bash
python -m app.cli fetch --max-results 100
```
- Re-run as needed; it upserts records by Gmail `message.id`.

### 7) Configure rules
Edit `rules/rules.json`. Example provided.

### 8) Process rules (apply actions via Gmail API)
```bash
python -m app.cli process --rules-path rules/rules.json
```

## Rules JSON Format

```jsonc
{
  "predicate": "All", // or "Any"
  "rules": [
    { "field": "From",    "predicate": "Contains",        "value": "noreply@" },
    { "field": "Subject", "predicate": "Does not Contain","value": "Promotion" },
    { "field": "Received","predicate": "LessThanDays",    "value": 30 }
  ],
  "actions": [
    { "type": "mark_as_read" },
    { "type": "move_message", "label": "Important" }
  ]
}
```

- **Fields**: `From`, `To`, `Subject`, `Message`, `Received`
- **String predicates**: `Contains`, `DoesNotContain`, `Equals`, `DoesNotEqual`
- **Date predicates** (on `Received`): `LessThanDays`, `GreaterThanDays`, `LessThanMonths`, `GreaterThanMonths`
- **Actions**: `mark_as_read`, `mark_as_unread`, `move_message` (requires `"label"`; falls back to `DEFAULT_MOVE_LABEL` if missing)

## Testing
```bash
pytest -q
```

## Notes
- "Move" in Gmail means applying a label and (optionally) removing `INBOX`. This app adds the target label and removes `INBOX` to emulate moving.
- The app updates the DB `is_read` and `labels` after actions to keep it in sync.
- This is a CLI app; no server is run.
```
