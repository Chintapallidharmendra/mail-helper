from sqlalchemy import select
from .db import get_session
from .models import Email
from .rules_engine import load_rules, email_matches, apply_actions

def process_rules(rules_path: str):
    rs = load_rules(rules_path)
    session = get_session()
    try:
        emails = session.scalars(select(Email)).all()
        matched = 0
        for e in emails:
            if email_matches(e, rs):
                updates = apply_actions(e, rs.actions)
                for k, v in updates.items():
                    setattr(e, k, v)
                matched += 1
        session.commit()
        return matched
    finally:
        session.close()
