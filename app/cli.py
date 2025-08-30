import typer
from .fetch_emails import init_db as initialize_db, fetch_and_store
from .process_rules import process_rules
from .rules_engine import load_rules
from .gmail_client import get_credentials

app = typer.Typer(help="Mail Helper App CLI")


@app.command()
def auth():
    """Run OAuth and save token."""
    get_credentials()
    typer.echo("Authenticated and token saved.")


@app.command()
def init_db():
    """Create tables."""
    initialize_db()  # Corrected to call the function
    typer.echo("Database initialized.")


@app.command()
def fetch(
    max_results: int = typer.Option(50, help="How many emails to fetch from INBOX"),
):
    count = fetch_and_store(max_results=max_results)
    typer.echo(f"Fetched {count} message metadata.")


@app.command()
def process(
    rules_path: str = typer.Option("rules/rules.json", help="Path to rules JSON"),
    stop_after_first_match: bool = typer.Option(
        None,
        "--stop-after-first-match/--allow-multiple",
        help="Stop after first matching rule (default: from .env)",
    ),
):
    rulesets = load_rules(rules_path)
    typer.echo(f"Loaded {len(rulesets)} rulesets from {rules_path}")
    matched = process_rules(rulesets, stop_after_first_match=stop_after_first_match)
    typer.echo(f"Applied rules to {matched} matching emails.")


if __name__ == "__main__":
    app()
