import httpx, json, os

email = os.environ['THEATRE_OUEST_EMAIL']
password = os.environ['THEATRE_OUEST_PASSWORD']
h = {'Content-Type': 'application/json', 'Accept': 'application/json'}
token = httpx.post('https://api.theatrealouest.com/login',
    json={'username': email, 'password': password}, headers=h, timeout=10).json()['token']
h['Authorization'] = f'Bearer {token}'

base = 'https://api.theatrealouest.com'
CAEN_ID = '5e4e0cb9-ac24-40a9-8a79-216ec1b0b3f4'

# 1. Structure complète d'un show (avec toutes les relations)
print("=== Show complet (premier résultat) ===")
r = httpx.get(f'{base}/shows', headers=h, timeout=10)
data = r.json()
items = data if isinstance(data, list) else (data.get('items') or data.get('hydra:member') or data.get('data') or [])
if items:
    print(json.dumps(items[0], ensure_ascii=False, indent=2))

# 2. Essayer le format IRI Symfony
print("\n=== Filtres IRI Symfony ===")
iri = f'/areas/{CAEN_ID}'
for param in [f'area={iri}', f'area[]={iri}', f'areas={iri}', f'theaters.area={iri}']:
    r = httpx.get(f'{base}/shows?{param}', headers=h, timeout=8)
    if r.status_code == 200:
        d = r.json()
        nb = d.get('pagination', {}).get('totalResults', len(d) if isinstance(d, list) else '?')
        print(f'OK  ?{param}  -> {nb}')
    else:
        print(f'{r.status_code}  ?{param}')

# 3. Pagination: chercher le nombre total de shows et de pages
print("\n=== Pagination info ===")
r = httpx.get(f'{base}/shows?page=1', headers=h, timeout=10)
d = r.json()
if isinstance(d, dict):
    print('Clés:', list(d.keys()))
    print('Pagination:', d.get('pagination'))
    print('Nb items page 1:', len(d.get('items') or d.get('hydra:member') or d.get('data') or []))
elif isinstance(d, list):
    print(f'Liste de {len(d)} items')
    # Essayer de trouver le total dans les headers
