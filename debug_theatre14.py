import httpx, json, os

email = os.environ['THEATRE_OUEST_EMAIL']
password = os.environ['THEATRE_OUEST_PASSWORD']
h = {'Content-Type': 'application/json', 'Accept': 'application/json'}
token = httpx.post('https://api.theatrealouest.com/login',
    json={'username': email, 'password': password}, headers=h, timeout=10).json()['token']
h['Authorization'] = f'Bearer {token}'

base = 'https://api.theatrealouest.com'
CAEN_ID = '5e4e0cb9-ac24-40a9-8a79-216ec1b0b3f4'
SHOW_ID = 'c25af182-706b-4df4-b764-0607e8782320'

# 1. Méthodes autorisées sur /areas/{id}
print("=== OPTIONS /areas/{id} ===")
r = httpx.options(f'{base}/areas/{CAEN_ID}', headers=h, timeout=8)
print(f'Status: {r.status_code}, Allow: {r.headers.get("Allow", "n/a")}')
print(f'Headers: {dict(r.headers)}')

# 2. Essayer d'expand les slots
print("\n=== Expand slots ===")
for param in ['expand[]=slots', 'expand=slots', 'with=slots',
              'include=slots', f'page=1&area[id]={CAEN_ID}',
              f'area[id][]={CAEN_ID}', f'area[id]={CAEN_ID}']:
    r = httpx.get(f'{base}/shows?{param}', headers=h, timeout=8)
    if r.status_code == 200:
        d = r.json()
        members = d.get('members', [])
        if members:
            slots = members[0].get('slots', [])
            # Vérifier si les slots ont plus d'infos
            print(f'OK  ?{param}  slots[0]={slots[0] if slots else "vide"}')
        else:
            print(f'OK  ?{param}  membres vides')
    else:
        print(f'{r.status_code}  ?{param}')

# 3. Chercher les slots d'un show via expand direct
print("\n=== Show avec slots expandés ===")
r = httpx.get(f'{base}/shows/{SHOW_ID}?expand[]=slots', headers=h, timeout=8)
print(f'{r.status_code}')
if r.status_code == 200:
    d = r.json()
    print('slots:', json.dumps(d.get('slots', []), indent=2)[:500])

# 4. Essayer /show-sessions ou /public/sessions
print("\n=== Endpoints publics sessions ===")
for path in ['/show-sessions', '/public/sessions', f'/shows/{SHOW_ID}/show-sessions',
             '/upcoming', f'/shows?selectedArea={CAEN_ID}&sort=date-ASC',
             f'/shows?sort=date-ASC&area={CAEN_ID}']:
    r = httpx.get(base + path if path.startswith('/') else path, headers=h, timeout=8)
    if r.status_code not in (404, 405):
        d = r.json() if r.status_code == 200 else {}
        nb = d.get('pagination', {}).get('totalResults', '?') if d else ''
        print(f'{r.status_code}  {path}  {nb}')
        if r.status_code == 200 and nb:
            members = d.get('members', [])
            if members:
                print(f'  Clés member: {list(members[0].keys())}')
