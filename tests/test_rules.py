from datetime import datetime, timedelta
import pytest
from app.rules_engine import email_matches, RuleSet, RuleCondition, load_rules
from app.process_rules import process_rules
from app.models import Email

# -----------------------------
# Fake session for mocking DB
# -----------------------------
class FakeSession:
    def __init__(self):
        self.storage = {}
    def add(self, obj):
        self.storage[obj.id] = obj
    def commit(self):
        # Ensure that the objects in storage reflect their updated state
        for key, obj in self.storage.items():
            self.storage[key] = obj
    def close(self):
        pass
    
    def get(self, model, pk):
        return self.storage.get(pk)
    
    def scalars(self, stmt):
        class FakeResult:
            def __init__(self, values):
                self._values = values
            def all(self):
                return self._values
        return FakeResult(list(self.storage.values()))

# -----------------------------
# Fixtures
# -----------------------------
@pytest.fixture
def fake_session(monkeypatch):
    fs = FakeSession()
    monkeypatch.setattr("app.db.get_session", lambda: fs)
    return fs

@pytest.fixture(autouse=True)
def mock_gmail(monkeypatch):
    """Mock Gmail API calls so tests don't hit network."""
    monkeypatch.setattr("app.rules_engine.modify_message", lambda *a, **kw: None)
    monkeypatch.setattr("app.rules_engine.get_labels_map", lambda: {"UNREAD": "lbl_unread", "INBOX": "lbl_inbox"})
    monkeypatch.setattr("app.rules_engine.ensure_label", lambda name: f"lbl_{name.lower()}")

# -----------------------------
# Helpers
# -----------------------------
def make_email(id="dummy", subject="Hello", body="", sender="a@b.com", received=None):
    return Email(
        id=id,
        thread_id="t1",
        from_email=sender,
        to_email="me@x.com",
        subject=subject,
        snippet=body[:100],
        body=body,
        received_at=received or (datetime.utcnow() - timedelta(days=1)),
        is_read=False,
        labels={"ids": []},
    )

# -----------------------------
# Tests
# -----------------------------
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

def test_multiple_rulesets_stop_after_first(tmp_path, fake_session):
    """Only first matching ruleset should apply when stop_after_first_match=True"""
    rules_file = tmp_path / "rules.json"
    rules_file.write_text("""
    [
      {
        "predicate": "Any",
        "rules": [{ "field": "Subject", "predicate": "Contains", "value": "Hello" }],
        "actions": [{ "type": "mark_as_read" }]
      },
      {
        "predicate": "Any",
        "rules": [{ "field": "From", "predicate": "Contains", "value": "a@" }],
        "actions": [{ "type": "mark_as_unread" }]
      }
    ]
    """)

    e = make_email(id="msg1", subject="Hello World", sender="a@b.com")
    fake_session.add(e)

    rulesets = load_rules(str(rules_file))
    matched = process_rules(rulesets, stop_after_first_match=True)
    updated = fake_session.get(Email, "msg1")

    assert matched == 1
    # Because stop_after_first_match=True, only mark_as_read should apply
    assert updated.is_read is True

def test_multiple_rulesets_allow_multiple(tmp_path, fake_session):
    """Both rulesets should apply when stop_after_first_match=False"""
    rules_file = tmp_path / "rules.json"
    rules_file.write_text("""
    [
      {
        "predicate": "Any",
        "rules": [{ "field": "Subject", "predicate": "Contains", "value": "Hello" }],
        "actions": [{ "type": "mark_as_read" }]
      },
      {
        "predicate": "Any",
        "rules": [{ "field": "From", "predicate": "Contains", "value": "a@" }],
        "actions": [{ "type": "mark_as_unread" }]
      }
    ]
    """)

    e = make_email(id="msg2", subject="Hello World", sender="a@b.com")
    fake_session.add(e)

    rulesets = load_rules(str(rules_file))
    matched = process_rules(rulesets, stop_after_first_match=False)
    updated = fake_session.get(Email, "msg2")

    assert matched == 2   # both rules matched
    # Last action mark_as_unread overrides mark_as_read
    assert updated.is_read is False

def test_move_message_action(tmp_path, fake_session):
    """Verify move_message applies label correctly using mocks."""
    rules_file = tmp_path / "rules.json"
    rules_file.write_text("""
    [
      {
        "predicate": "Any",
        "rules": [{ "field": "Subject", "predicate": "Contains", "value": "Project" }],
        "actions": [{ "type": "move_message", "label": "Important" }]
      }
    ]
    """)

    e = make_email(id="msg3", subject="Project Update", sender="boss@company.com")
    fake_session.add(e)

    rulesets = load_rules(str(rules_file))
    matched = process_rules(rulesets, stop_after_first_match=True)
    updated = fake_session.get(Email, "msg3")

    assert matched == 1
    # Labels should now include "lbl_important" (from mocked ensure_label)
    assert "lbl_important" in updated.labels["ids"]
