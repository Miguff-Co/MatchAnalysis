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

# get latest season automatically
seasons = get_json(f"{BASE}/unique-tournament/{UT_ID}/seasons")["seasons"]
season_id = seasons[0]["id"]

event_ids = set()
round_no = 1
empty_rounds = 0

while empty_rounds < 3:  # stop when rounds run out
    try:
        data = get_json(
        f"{BASE}/unique-tournament/{UT_ID}/season/{season_id}/events/round/{round_no}"
        )
        events = data.get("events", [])
    except:
        break
    if not events:
        empty_rounds += 1
        round_no += 1
        continue

    empty_rounds = 0
    for e in events:
        event_ids.add(e["id"])

    round_no += 1

# output
for eid in sorted(event_ids):
    print(eid)

print(f"\nTotal matches: {len(event_ids)}")
