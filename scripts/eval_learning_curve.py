import os, json, time
os.environ["BANK_ID"] = f"eval-{int(time.time())}"   # must be set BEFORE importing app.memory

from dotenv import load_dotenv
load_dotenv()
from openai import OpenAI
from app import agent
from app.memory import retain_incident
from scripts.families import FAMILIES

judge = OpenAI(base_url="https://api.groq.com/openai/v1", api_key=os.environ["GROQ_API_KEY"])

def grade(plan: dict, inc: dict) -> dict:
    f = FAMILIES[inc["family"]]
    bad = [w[0] for w in f["wrong_actions"]]
    prompt = f"""Grade this incident plan against ground truth.
Correct fix: {f['good_fix']}
Known-bad actions: {bad}
Plan JSON: {json.dumps({k: plan.get(k) for k in ('steps', 'avoid')})}
Return ONLY JSON: {{"step1_correct": bool, "recommends_bad_action": bool}}
step1_correct is true only if the FIRST step is essentially the correct fix.
recommends_bad_action is true if any known-bad action appears in "steps" as something to do (listing it under "avoid" does not count)."""
    r = judge.chat.completions.create(
        model=agent.MODEL, temperature=0,
        messages=[{"role": "user", "content": prompt}],
        response_format={"type": "json_object"})
    return json.loads(r.choices[0].message.content)

incidents = sorted(json.load(open("data/incidents.json")), key=lambda i: i["resolved_at"])
results = []
for n, inc in enumerate(incidents):
    row = {"id": inc["id"], "n_memories_before": n}
    for mode in ("off", "on"):
        p = agent.plan(inc["alert"], inc["symptoms"], use_memory=(mode == "on"))
        row[mode] = grade(p, inc)
    results.append(row)
    print(row)
    retain_incident(inc)          # only AFTER planning, so it never sees itself
    time.sleep(5)                 # give consolidation a moment

json.dump(results, open("data/eval_results.json", "w"), indent=2)

import matplotlib.pyplot as plt
xs = [r["n_memories_before"] for r in results]
for mode, label in (("off", "Memory OFF"), ("on", "Memory ON")):
    wrong = [0 if r[mode]["step1_correct"] else 1 for r in results]
    cum = [sum(wrong[:i + 1]) / (i + 1) for i in range(len(wrong))]
    plt.plot(xs, cum, marker="o", label=label)
plt.xlabel("Past incidents in memory")
plt.ylabel("Cumulative wrong-first-suggestion rate")
plt.legend(); plt.savefig("data/learning_curve.png", dpi=150)