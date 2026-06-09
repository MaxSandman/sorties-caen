import httpx, json, os
from datetime import date

email = os.environ['THEATRE_OUEST_EMAIL']
password = os.environ['THEATRE_OUEST_PASSWORD']
h = {'Content-Type': 'application/json', 'Accept': 'application/json'}
token = httpx.post('https://api.theatrealouest.com/login',
    json={'username': email, 'password': password}, headers=h, timeout=10).json()['token']
h['Authorization'] = f'Bearer {token}'

CAEN_ID = '5e4e0cb9-ac24-40a9-8a79-216ec1b0b3f4'
today = date.today().isoformat() + 'T00:00:00'
params = {'slots:to[min]': today, 'sort': 'slots:from|ASC', 'enabled': 'true', 'page': '1'}

r = httpx.get(f'https://api.theatrealouest.com/shows/areas/{CAEN_ID}',
              headers=h, params=params, timeout=15)
print(f'Status: {r.status_code}')
d = r.json()
print(f'Total: {d.get("pagination", {}).get("totalResults")} spectacles, {d.get("pagination", {}).get("totalPages")} pages')

members = d.get('members', [])
print(f'Page 1: {len(members)} shows')
if members:
    show = members[0]
    print(f'\nPremier show complet:')
    print(json.dumps(show, ensure_ascii=False, indent=2))
