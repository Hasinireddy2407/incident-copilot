"""Recall in code, then one LLM call to produce the plan."""
import json
import re
import time
from datetime import date

from openai import OpenAI

from . import config
from .memory import recall_for_alert

MODEL = config.MODEL
if not config.GROQ_API_KEY:
    raise RuntimeError("GROQ_API_KEY is missing. Add it to your .env file.")
llm = OpenAI(base_url=config.GROQ_BASE_URL, api_key=config.GROQ_API_KEY)

SYSTEM = """You are an on-call incident copilot. You get a NEW ALERT and MEMORIES from past incidents.
Rules:
- Put fixes that worked in past similar incidents first.
- Explicitly list actions that were HARMFUL or FAILED in similar incidents under "avoid", with the reason.
- Cite the incident id for every claim. Never invent incident ids.
- If a memory is older than 6 months (compare with TODAY), add a staleness note.
- If memories are NONE, weak or unrelated, say so and give general advice, clearly labelled as general advice with source null.
Return ONLY JSON: {"summary": str, "steps": [{"action": str, "why": str, "source": str|null}],
"avoid": [{"action": str, "reason": str, "source": str}], "staleness_note": str|null}"""


def _parse(text: str) -> dict:
    text = re.sub(r"^```(?:json)?|```$", "", text.strip(), flags=re.M).strip()
    return json.loads(text)


def _mem_dict(m) -> dict:
    d = getattr(m, "occurred_start", None)
    return {
        "type": getattr(m, "type", None) or "memory",
        "text": getattr(m, "text", str(m)),
        "date": str(d) if d else None,
    }


def _error(msg: str) -> dict:
    return {"summary": msg, "steps": [], "avoid": [], "staleness_note": None, "_memories": []}


def plan(alert: str, symptoms: str = "", use_memory: bool = True) -> dict:
    memories = []
    if use_memory:
        try:
            memories = [_mem_dict(m) for m in recall_for_alert(alert, symptoms)]
        except Exception as e:
            return _error(f"Memory unavailable (is Hindsight running?): {e}")

    mem_text = "\n".join(
        f"[{m['type']}] ({m['date'] or 'undated'}) {m['text']}" for m in memories
    ) or "NONE"
    user = (f"TODAY: {date.today().isoformat()}\nNEW ALERT: {alert}\n"
            f"SYMPTOMS: {symptoms}\n\nMEMORIES:\n{mem_text}")

    last_err = None
    for attempt in range(3):
        try:
            r = llm.chat.completions.create(
                model=MODEL, temperature=0.2,
                messages=[{"role": "system", "content": SYSTEM}, {"role": "user", "content": user}],
                response_format={"type": "json_object"},
            )
            out = _parse(r.choices[0].message.content)
            out["_memories"] = memories
            return out
        except Exception as e:
            last_err = e
            time.sleep(2)
    err = _error(f"Agent error (Groq): {last_err}")
    err["_memories"] = memories
    return err
