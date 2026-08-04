import requests

BASE = "https://www.sofascore.com/api/v1"
UT_ID = 187  # Hungarian NB I (Fizz Liga)

headers = {
    "User-Agent": "Mozilla/5.0",
    "Accept": "application/json",
}

def get_json(url):
    r = requests.get(url, headers=headers, timeout=30)
    r.raise_for_status()
    return r.json()

# get latest season
season_id = get_json(
    f"{BASE}/unique-tournament/{UT_ID}/seasons"
)["seasons"][0]["id"]

event_ids = set()
round_no = 1
empty_rounds = 0

while empty_rounds < 3:
    try:
        data = get_json(
        f"{BASE}/unique-tournament/{UT_ID}/season/{season_id}/events/round/{round_no}"
        )
    except:
        break
    events = data.get("events", [])

    if not events:
        empty_rounds += 1
        round_no += 1
        continue

    empty_rounds = 0

    for e in events:
        # ONLY matches that already happened
        if e.get("status", {}).get("type") == "finished":
            event_ids.add(e["id"])

    round_no += 1

# output
for eid in sorted(event_ids):
    print(eid)

print(f"\nFinished matches: {len(event_ids)}")
