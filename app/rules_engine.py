from __future__ import annotations
from dataclasses import dataclass
from typing import List, Dict, Any, Callable
from datetime import datetime
from dateutil.relativedelta import relativedelta
import json
from .models import Email
from .config import settings
from .gmail_client import ensure_label, modify_message, get_labels_map

STRING_PREDICATES = {"Contains", "DoesNotContain", "Equals", "DoesNotEqual"}
DATE_PREDICATES = {"LessThanDays", "GreaterThanDays", "LessThanMonths", "GreaterThanMonths"}

@dataclass
class RuleCondition:
    field: str
    predicate: str
    value: Any

@dataclass
class RuleSet:
    predicate: str # "All" or "Any"
    rules: List[RuleCondition]
    actions: List[Dict[str, Any]]

def load_rules(path: str) -> RuleSet:
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    rules = [RuleCondition(**r) for r in data.get("rules", [])]
    return RuleSet(predicate=data.get("predicate", "All"), rules=rules, actions=data.get("actions", []))

def _field_value(email: Email, field: str) -> Any:
    f = field.lower()
    if f == "from":
        return email.from_email or ""
    if f == "to":
        return email.to_email or ""
    if f == "subject":
        return email.subject or ""
    if f == "message":
        return email.body or email.snippet or ""
    if f == "received":
        return email.received_at
    raise ValueError(f"Unsupported field: {field}")

def _match_string(val: str, predicate: str, target: str) -> bool:
    v = (val or "").lower()
    t = (target or "").lower()
    if predicate == "Contains":
        return t in v
    if predicate == "DoesNotContain":
        return t not in v
    if predicate == "Equals":
        return v == t
    if predicate == "DoesNotEqual":
        return v != t
    raise ValueError(f"Unknown string predicate {predicate}")

def _match_date(dt: datetime, predicate: str, amount: int) -> bool:
    now = datetime.utcnow()
    if predicate == "LessThanDays":
        return (now - dt).days < int(amount)
    if predicate == "GreaterThanDays":
        return (now - dt).days > int(amount)
    if predicate == "LessThanMonths":
        # rough months via relativedelta
        return (now - relativedelta(months=int(amount))) < dt
    if predicate == "GreaterThanMonths":
        return (now - relativedelta(months=int(amount))) > dt
    raise ValueError(f"Unknown date predicate {predicate}")

def email_matches(email: Email, rs: RuleSet) -> bool:
    results = []
    for cond in rs.rules:
        val = _field_value(email, cond.field)
        if cond.predicate in STRING_PREDICATES:
            results.append(_match_string(str(val), cond.predicate, str(cond.value)))
        elif cond.predicate in DATE_PREDICATES:
            if not isinstance(val, datetime):
                results.append(False)
            else:
                results.append(_match_date(val, cond.predicate, int(cond.value)))
        else:
            results.append(False)
    return all(results) if rs.predicate == "All" else any(results)

def apply_actions(email: Email, actions: List[Dict[str, Any]]) -> Dict[str, Any]:
    labels_map = get_labels_map()
    add_ids, remove_ids = [], []
    state_updates = {}

    for act in actions:
        t = act.get("type")
        if t == "mark_as_read":
            # remove UNREAD
            if "UNREAD" in labels_map:
                remove_ids.append(labels_map["UNREAD"])
            state_updates["is_read"] = True
        elif t == "mark_as_unread":
            if "UNREAD" in labels_map:
                add_ids.append(labels_map["UNREAD"])
            state_updates["is_read"] = False
        elif t == "move_message":
            target_label = act.get("label") or settings.DEFAULT_MOVE_LABEL
            label_id = ensure_label(target_label)
            add_ids.append(label_id)
            # emulate move: remove INBOX if present
            if "INBOX" in labels_map:
                remove_ids.append(labels_map["INBOX"])
        else:
            raise ValueError(f"Unknown action type: {t}")

    if add_ids or remove_ids:
        modify_message(email.id, add_labels=list(set(add_ids)), remove_labels=list(set(remove_ids)))
        # update labels list in our local model (id-only to keep it simple)
        current_ids = set((email.labels or {}).get("ids", []))
        current_ids.update(add_ids)
        current_ids.difference_update(remove_ids)
        state_updates["labels"] = {"ids": list(current_ids)}

    return state_updates
