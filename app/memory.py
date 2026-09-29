"""All Hindsight calls live here."""
import os
from hindsight_client import Hindsight
from . import config

BANK = config.BANK_ID

client = Hindsight(
    base_url=os.getenv("HINDSIGHT_URL"),
    api_key=os.getenv("HINDSIGHT_API_KEY"),  # check exact kwarg name against the Python client docs
)


def _retain(**kw):
    """Retain, dropping optional kwargs if this client version rejects them."""
    try:
        client.retain(**kw)
    except TypeError:
        for k in ("tags", "metadata"):
            kw.pop(k, None)
        client.retain(**kw)


def retain_incident(inc: dict):
    actions = "\n".join(
        f"- Attempted: {a['action']}. Outcome: {a['outcome'].upper()}. {a['note']}"
        for a in inc["actions"]
    )
    content = (
        f"Incident {inc['id']} on {inc['service']} ({inc['severity']}).\n"
        f"Alert: {inc['alert']}\nSymptoms: {inc['symptoms']}\n"
        f"Actions:\n{actions}\n"
        f"Root cause: {inc['root_cause']}\nResolution: {inc['resolution']}\n"
        f"Time to resolve: {inc['ttr_minutes']} minutes."
    )
    _retain(
        bank_id=BANK,
        content=content,
        context="incident postmortem",
        timestamp=inc["resolved_at"],
        document_id=f"incident-{inc['id']}",
        tags=[f"service:{inc['service']}", f"severity:{inc['severity']}"],
        metadata={"incident_id": inc["id"]},
    )


def log_action(incident_id: str, n: int, action: str, outcome: str, note: str = ""):
    """Mid-incident feedback: the Worked / Failed / Harmful buttons."""
    _retain(
        bank_id=BANK,
        content=f"During incident {incident_id}, attempted: {action}. Outcome: {outcome.upper()}. {note}",
        context="live incident action",
        document_id=f"incident-{incident_id}-action-{n}",
    )


def recall_for_alert(alert: str, symptoms: str = ""):
    query = f"{alert} {symptoms}".strip()
    try:
        resp = client.recall(bank_id=BANK, query=query, budget="high", max_tokens=3000)
    except TypeError:
        resp = client.recall(bank_id=BANK, query=query)
    return resp.results


def reflect_patterns() -> str:
    r = client.reflect(
        bank_id=BANK,
        query="What recurring root causes and failed fixes have you learned? Cite incident IDs.",
    )
    return getattr(r, "text", None) or str(r)
