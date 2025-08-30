# Mail Helper App (Python + PostgreSQL)

A standalone Python application that:

1. Authenticates with the Gmail API (OAuth2, no IMAP).
2. Fetches emails into a PostgreSQL database.
3. Applies JSON-configured rules to perform actions (mark read/unread, move to label) using Gmail REST API.
4. Simplifies email management with easy-to-follow steps.

## Tech Stack

- **Programming Language**: Python 3.10+
- **Database**: PostgreSQL
- **Libraries**: SQLAlchemy ORM, Google Gmail API (google-api-python-client), Typer CLI, dotenv
- **Package Management**: `uv`

## Installation

### Prerequisites

- Python 3.10 or higher
- PostgreSQL installed and running
- Google Cloud project with Gmail API enabled
- `uv` package manager installed globally

### Steps

1. **Clone the Repository**:

   ```bash
   git clone <repository-url>
   cd mail-helper
   ```

2. **Install Dependencies**:

   ```bash
   uv sync
   ```

3. **Set Up Environment Variables**:

   - Copy the example `.env` file:
     ```bash
     cp .env.bak .env
     ```
   - Edit `.env` to configure `DATABASE_URL`, Gmail user ID, and other settings.

4. **Create the Database**:

   ```bash
   createdb mailhelper  # Or use psql/GUI; update .env accordingly
   ```

5. **Authenticate with Gmail**:

   - Follow [Google OAuth Documentation](https://developers.google.com/identity/protocols/oauth2#1.-obtain-oauth-2.0-credentials-from-the-dynamic_data.setvar.console_name.) to obtain OAuth credentials.
   - Save the credentials as `./credentials.json`.
   - Initialize the database and authenticate:
     ```bash
     uv run python -m app.cli init-db
     uv run python -m app.cli auth
     ```
   - A browser window will open to grant access. The token will be saved to the path specified in `.env` (default: `./token.json`).

## Usage

### Fetch Emails

Fetch emails from Gmail and store them in the database:

```bash
uv run python -m app.cli fetch --max-results 100
```

### Configure Rules

Define rules in the `rules/rules.json` file. An example is provided in the file.

### Process Rules

Apply the configured rules to emails:

```bash
uv run python -m app.cli process --rules-path rules/rules.json
```

### Run Tests

Execute the test suite:

```bash
uv run pytest -q
```

## Rules JSON Format

The `rules.json` file allows you to define multiple rules to process emails. Below is an example format:

```jsonc
[
  {
    "predicate": "All",
    "rules": [
      { "field": "From", "predicate": "Contains", "value": "noreply@" },
      {
        "field": "Subject",
        "predicate": "DoesNotContain",
        "value": "Promotion"
      }
    ],
    "actions": [{ "type": "mark_as_read" }]
  }
]
```

### Defining Multiple Rules

You can define multiple rules in the `rules.json` file. Each rule can have its own set of conditions and actions. For example:

```jsonc
[
  {
    "predicate": "All",
    "rules": [
      {
        "field": "From",
        "predicate": "Contains",
        "value": "example@domain.com"
      },
      { "field": "Subject", "predicate": "Contains", "value": "Invoice" }
    ],
    "actions": [{ "type": "mark_as_read" }]
  },
  {
    "predicate": "Any",
    "rules": [
      { "field": "From", "predicate": "Contains", "value": "newsletter@" },
      {
        "field": "Subject",
        "predicate": "Does not Contain",
        "value": "Important"
      }
    ],
    "actions": [
      { "type": "mark_as_unread" },
      { "type": "move_message", "label": "Promotions" }
    ]
  }
]
```

### Supported Fields and Predicates

- **Fields**: `From`, `To`, `Subject`, `Message`, `Received`
- **String Predicates**: `Contains`, `DoesNotContain`, `Equals`, `DoesNotEqual`
- **Date Predicates** (on `Received`): `LessThanDays`, `GreaterThanDays`, `LessThanMonths`, `GreaterThanMonths`
- **Actions**: `mark_as_read`, `mark_as_unread`, `move_message` (requires `"label"`; falls back to `DEFAULT_MOVE_LABEL` if missing)

## Notes

- "Move" in Gmail means applying a label and (optionally) removing `INBOX`. This app adds the target label and removes `INBOX` to emulate moving.
- The app updates the database `is_read` and `labels` after actions to maintain synchronization.
- This is a CLI app; no server is run.

## Support

For queries or issues, contact [Dharmendra](mailto:chintapallidharmendra@gmail.com).
