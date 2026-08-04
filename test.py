import requests

api = "638f12719f9f25b4a5db7b67e29dc499"

#url = "https://v3.football.api-sports.io/leagues?season=2023&id=271"

url = "https://v3.football.api-sports.io/players?id=178882&season=2023"

payload={}
headers = {
  'x-apisports-key': api,
}

response = requests.request("GET", url, headers=headers, data=payload)

print(response.json()["response"][0]["statistics"][0])
