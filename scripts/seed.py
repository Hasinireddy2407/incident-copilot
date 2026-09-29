import json
from app.memory import retain_incident

incidents = json.load(open("data/incidents.json"))
seed = [i for i in incidents if i["split"] == "seed"]
for inc in sorted(seed, key=lambda i: i["resolved_at"]):
    retain_incident(inc)
    print("retained", inc["id"])
print(f"Seeded {len(seed)} incidents. Wait 1-2 minutes for consolidation.")