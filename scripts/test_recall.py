"""Usage: python -m scripts.test_recall [INCIDENT_ID]   (default INC-113)"""
import json
import sys

from app.memory import recall_for_alert

inc_id = sys.argv[1] if len(sys.argv) > 1 else "INC-113"
inc = next(i for i in json.load(open("data/incidents.json")) if i["id"] == inc_id)
print("ALERT:", inc["alert"], "\n")
for r in recall_for_alert(inc["alert"], inc["symptoms"]):
    print(getattr(r, "type", "?"), "|", r.text[:160].replace("\n", " "))
