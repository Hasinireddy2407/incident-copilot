# Incident Copilot

An on-call assistant that remembers past incidents. Given a new alert, it recalls similar incidents from Hindsight memory, recommends what worked, and warns about fixes that made things worse.

## Architecture

```
Browser UI (app/static/index.html)
        |
   FastAPI (app/main.py)
   /plan  /action  /close  /patterns
        |                    |
   agent.py              memory.py  ---->  Hindsight (retain / recall / reflect)
   recall -> 1 LLM call
        |
   Groq: openai/gpt-oss-120b
```

## How Hindsight memory is used

- **Retain:** each resolved incident is stored as a postmortem with its resolution timestamp and a stable `document_id`, so re-retaining is idempotent. Every attempted action is written with an explicit outcome (WORKED, FAILED, HARMFUL).
- **Recall:** on a new alert, the agent recalls memories across all services. A `payments-api` alert can therefore surface a `checkout-service` incident with the same root cause. Memory dates let the agent flag stale advice.
- **Live feedback loop:** the Worked / Failed / Harmful buttons retain each outcome mid-incident, so the next alert benefits.
- **Reflect:** the Patterns panel asks Hindsight what recurring root causes and failed fixes it has learned.
- **Memory OFF mode:** the same agent runs without recall, which gives a fair before/after comparison.

## Setup

```powershell
python -m pip install -r requirements.txt
copy .env.example .env        # then fill in your keys
# data/incidents.json is included. To regenerate it with Groq (optional):
# python scripts/generate_data.py
python -m scripts.seed            # loads the seed incidents into Hindsight
python -m scripts.test_recall     # sanity check recall
python -m uvicorn app.main:app --reload
```

Open http://localhost:8000.

## Evaluation

```powershell
python -m scripts.eval_learning_curve
```

Replays incidents in date order using a fresh bank, comparing memory OFF and ON, and writes `data/eval_results.json` and `data/learning_curve.png`. The step-1 grading is done by an LLM judge, so spot-check the results.

Results: _fill in with the numbers you measured._
