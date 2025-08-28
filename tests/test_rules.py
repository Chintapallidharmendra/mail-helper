from datetime import datetime, timedelta
from app.rules_engine import email_matches, RuleSet, RuleCondition

class Dummy:
    pass

def make_email(subject="Hello", body="", sender="a@b.com", received=None):
    e = Dummy()
    e.from_email = sender
    e.to_email = "me@x.com"
    e.subject = subject
    e.snippet = body[:100]
    e.body = body
    e.received_at = received or (datetime.utcnow() - timedelta(days=1))
    e.is_read = False
    e.labels = {"ids": []}
    return e

def test_string_contains_all():
    rs = RuleSet(
        predicate="All",
        rules=[
            RuleCondition(field="Subject", predicate="Contains", value="Hel"),
            RuleCondition(field="From", predicate="DoesNotContain", value="spam"),
        ],
        actions=[],
    )
    e = make_email()
    assert email_matches(e, rs) is True

def test_date_less_than_days():
    rs = RuleSet(
        predicate="All",
        rules=[
            RuleCondition(field="Received", predicate="LessThanDays", value=7),
        ],
        actions=[],
    )
    e = make_email(received=datetime.utcnow() - timedelta(days=3))
    assert email_matches(e, rs) is True
