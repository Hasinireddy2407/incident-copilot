from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from . import agent, memory

app = FastAPI(title="Incident Copilot")
STATIC = Path(__file__).parent / "static"


class Alert(BaseModel):
    alert: str
    symptoms: str = ""
    use_memory: bool = True


class Action(BaseModel):
    incident_id: str
    n: int
    action: str
    outcome: str          # worked | failed | harmful | partial
    note: str = ""


@app.post("/plan")
def plan(a: Alert):
    return agent.plan(a.alert, a.symptoms, a.use_memory)


@app.post("/action")
def action(a: Action):
    try:
        memory.log_action(a.incident_id, a.n, a.action, a.outcome, a.note)
    except Exception as e:
        raise HTTPException(502, f"Hindsight error: {e}")
    return {"ok": True}


@app.post("/close")
def close(inc: dict):
    try:
        memory.retain_incident(inc)
    except Exception as e:
        raise HTTPException(502, f"Hindsight error: {e}")
    return {"ok": True}


@app.get("/patterns")
def patterns():
    try:
        return {"text": memory.reflect_patterns()}
    except Exception as e:
        raise HTTPException(502, f"Hindsight error: {e}")


# Must be last, or it shadows the API routes above.
app.mount("/", StaticFiles(directory=STATIC, html=True), name="static")
