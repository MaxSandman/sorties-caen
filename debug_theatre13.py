import httpx, json, os
from datetime import date

email = os.environ['THEATRE_OUEST_EMAIL']
password = os.environ['THEATRE_OUEST_PASSWORD']
h = {'Content-Type': 'application/json', 'Accept': 'application/json'}
token = httpx.post('https://api.theatrealouest.com/login',
    json={'username': email, 'password': password}, headers=h, timeout=10).json()['token']
h['Authorization'] = f'Bearer {token}'

base = 'https://api.theatrealouest.com'
CAEN_ID = '5e4e0cb9-ac24-40a9-8a79-216ec1b0b3f4'
today = date.today().isoformat()

# 1. Explorer les endpoints de slots/sessions
print("=== Endpoints slots/sessions ===")
for path in ['/slots', '/sessions', '/show-slots', '/showSlots', '/show_slots',
             '/bookings', '/performances', '/dates']:
    r = httpx.get(base + path, headers=h, timeout=8)
    if r.status_code == 200:
        d = r.json()
        if isinstance(d, dict):
            nb = d.get('pagination', {}).get('totalResults', '?')
            keys = list(d.keys())
            members = d.get('members', [])
            print(f'200  {path}  total={nb}  clés={keys}')
            if members:
                print(f'     Clés member: {list(members[0].keys())}')
        else:
            print(f'200  {path}  liste={len(d)}')
    elif r.status_code != 404:
        print(f'{r.status_code}  {path}')

# 2. Essayer les slots d'un show spécifique
print("\n=== Slots d'un show spécifique ===")
SHOW_ID = 'c25af182-706b-4df4-b764-0607e8782320'
for path in [f'/shows/{SHOW_ID}/slots', f'/shows/{SHOW_ID}/sessions',
             f'/shows/{SHOW_ID}?include=slots', f'/shows/{SHOW_ID}']:
    r = httpx.get(base + path, headers=h, timeout=8)
    print(f'{r.status_code}  {path}')
    if r.status_code == 200:
        print(json.dumps(r.json(), ensure_ascii=False, indent=2)[:600])

# 3. Essayer /slots avec filtre area
print("\n=== /slots avec filtre area ===")
for param in [f'area={CAEN_ID}', f'area.id={CAEN_ID}', f'areaId={CAEN_ID}',
              f'selectedArea={CAEN_ID}', f'area[]={CAEN_ID}',
              f'dateFrom={today}', f'date[after]={today}']:
    r = httpx.get(f'{base}/slots?{param}', headers=h, timeout=8)
    if r.status_code == 200:
        d = r.json()
        nb = d.get('pagination', {}).get('totalResults', len(d) if isinstance(d, list) else '?')
        print(f'OK  ?{param}  -> {nb}')
    elif r.status_code != 404:
        print(f'{r.status_code}  ?{param}')
