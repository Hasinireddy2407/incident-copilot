import json, os, random, re, sys
from openai import OpenAI
from dotenv import load_dotenv
sys.path.insert(0, os.path.dirname(__file__))
from families import FAMILIES, SPECS

load_dotenv()
llm = OpenAI(base_url="https://api.groq.com/openai/v1", api_key=os.environ["GROQ_API_KEY"])
MODEL = "openai/gpt-oss-120b"
OUTCOMES = {"worked", "failed", "harmful", "partial"}

PROMPT = """Write a realistic production incident record as JSON for an SRE team.

Service: {service}   Severity: {severity}   Date: {date}
Root cause (fixed, do not change): {root_cause}
Realistic log/error fragments you may use and adapt: {log_hints}
Wrong first instincts the on-call engineer may have tried (use 1 or 2 of them, in any order,
using the given outcome and rewording the note): {wrong}
The action that finally worked: {good_fix}

Requirements:
- Use realistic details: specific deploy numbers, metric values, pod/host names, an on-call
  engineer's first name, and error lines that mention {service}.
- The alert must be worded differently from these existing alerts, sharing no distinctive phrases: {existing}
- Do not simply restate the root cause in the alert. Describe symptoms as a monitoring system would.
- Return ONLY JSON with keys:
  "alert" (one line as a monitoring system would send it),
  "symptoms" (2-3 sentences including one realistic log line),
  "actions" (list of {{"action","outcome","note"}}, in the order tried; the LAST one is the fix with outcome "worked"),
  "root_cause" (1 sentence, specific to this service), "resolution" (1 sentence),
  "ttr_minutes" (integer between 12 and 95)."""

def valid(d):
    try:
        acts = d["actions"]
        return (isinstance(d["alert"], str) and isinstance(d["ttr_minutes"], int)
                and all(a["outcome"] in OUTCOMES for a in acts)
                and acts[-1]["outcome"] == "worked" and len(acts) >= 2)
    except Exception:
        return False

def generate(spec, existing):
    inc_id, fam, service, date, sev, split = spec
    f = FAMILIES[fam]
    wrong = "; ".join(f"{a} -> {o} ({n})" for a, o, n in f["wrong_actions"])
    prompt = PROMPT.format(service=service, severity=sev, date=date, root_cause=f["root_cause"],
                           log_hints=f["log_hints"], wrong=wrong, good_fix=f["good_fix"],
                           existing=existing or "none yet")
    for _ in range(4):
        try:
            r = llm.chat.completions.create(model=MODEL, temperature=0.9,
                messages=[{"role": "user", "content": prompt}],
                response_format={"type": "json_object"})
            d = json.loads(re.sub(r"^```(?:json)?|```$", "", r.choices[0].message.content.strip(), flags=re.M))
            if valid(d):
                d.update(id=inc_id, family=fam, service=service, severity=sev, split=split,
                         resolved_at=f"{date}T{random.randint(0,23):02d}:{random.randint(0,59):02d}:00Z")
                return d
        except Exception as e:
            print("retry:", e)
    raise RuntimeError(f"failed to generate {inc_id}")

if __name__ == "__main__":
    out, alerts = [], []
    for spec in sorted(SPECS, key=lambda s: s[3]):      # chronological
        inc = generate(spec, alerts)
        alerts.append(inc["alert"])
        out.append(inc)
        print(inc["id"], "|", inc["alert"])
    os.makedirs("data", exist_ok=True)
    json.dump(out, open("data/incidents.json", "w"), indent=2)
    print(f"Wrote {len(out)} incidents")