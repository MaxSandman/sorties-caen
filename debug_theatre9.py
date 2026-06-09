import httpx, json, os

email = os.environ['THEATRE_OUEST_EMAIL']
password = os.environ['THEATRE_OUEST_PASSWORD']
h = {'Content-Type': 'application/json', 'Accept': 'application/json'}
token = httpx.post('https://api.theatrealouest.com/login',
    json={'username': email, 'password': password}, headers=h, timeout=10).json()['token']
h['Authorization'] = f'Bearer {token}'

base = 'https://api.theatrealouest.com'
CAEN_ID = '5e4e0cb9-ac24-40a9-8a79-216ec1b0b3f4'

# 1. Structure complète d'un show
print("=== Structure d'un show ===")
r = httpx.get(f'{base}/shows?page=1&limit=1', headers=h, timeout=10)
data = r.json()
if isinstance(data, list) and data:
    show = data[0]
elif isinstance(data, dict):
    items = data.get('items') or data.get('hydra:member') or data.get('data') or []
    show = items[0] if items else {}
else:
    show = {}
print(json.dumps(show, ensure_ascii=False, indent=2)[:2000])

# 2. Chercher les endpoints disponibles
print("\n=== Endpoints à tester ===")
for path in ['/theaters', '/venues', '/cities', '/locations', '/sessions', '/events',
             '/shows?city=Caen', f'/shows?theater.area={CAEN_ID}',
             f'/shows?theaters.area={CAEN_ID}', '/shows?upcoming=true&page=1']:
    r = httpx.get(base + path if path.startswith('/') else path, headers=h, timeout=8)
    if r.status_code == 200:
        d = r.json()
        if isinstance(d, list):
            nb = len(d)
            keys = list(d[0].keys()) if d else []
        elif isinstance(d, dict):
            nb = d.get('pagination', {}).get('totalResults', '?')
            keys = list(d.keys())
        else:
            nb, keys = '?', []
        print(f'200  {path}  -> {nb} items, clés: {keys[:6]}')
    else:
        print(f'{r.status_code}  {path}')

# 3. Si /theaters existe, chercher ceux de Caen
print("\n=== Théâtres ===")
r = httpx.get(f'{base}/theaters', headers=h, timeout=10)
if r.status_code == 200:
    theaters = r.json()
    if isinstance(theaters, dict):
        theaters = theaters.get('items') or theaters.get('hydra:member') or theaters.get('data') or []
    for t in theaters:
        name = t.get('name', '')
        city = t.get('city', t.get('area', t.get('location', '')))
        if 'caen' in str(name).lower() or 'caen' in str(city).lower():
            print(json.dumps(t, ensure_ascii=False, indent=2)[:400])
    if not theaters:
        print('Aucun théâtre')
else:
    print(f'{r.status_code} /theaters')
