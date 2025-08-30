from sqlalchemy import select
from . import db
from .models import Email
from .rules_engine import email_matches, apply_actions
from .rules_engine import RuleSet
from typing import List
from .config import settings

def process_rules(rulesets: List[RuleSet], stop_after_first_match: bool | None = None):
    session = db.get_session()
    try:
        emails = session.scalars(select(Email)).all()
        matched = 0
        stop_flag = settings.STOP_AFTER_FIRST_MATCH if stop_after_first_match is None else stop_after_first_match

        for e in emails:
            for rs in rulesets:
                if email_matches(e, rs):
                    updates = apply_actions(e, rs.actions)
                    for k, v in updates.items():
                        setattr(e, k, v)
                    matched += 1
                    if stop_flag:
                        break
        session.commit()
        return matched
    finally:
        session.close()

