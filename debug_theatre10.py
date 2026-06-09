import httpx, json, os

email = os.environ['THEATRE_OUEST_EMAIL']
password = os.environ['THEATRE_OUEST_PASSWORD']
h = {'Content-Type': 'application/json', 'Accept': 'application/json'}
token = httpx.post('https://api.theatrealouest.com/login',
    json={'username': email, 'password': password}, headers=h, timeout=10).json()['token']
h['Authorization'] = f'Bearer {token}'

base = 'https://api.theatrealouest.com'

# L'URL Angular est /caen/spectacle/liste -> "caen" est le slug de l'area
# Essayer le slug dans les filtres
print("=== Filtres avec slug 'caen' ===")
for param in ['areaSlug=caen', 'area.slug=caen', 'slug=caen',
              'areas.slug=caen', 'city.slug=caen', 'location=caen',
              'city=caen']:
    r = httpx.get(f'{base}/shows?{param}', headers=h, timeout=8)
    if r.status_code == 200:
        d = r.json()
        nb = d.get('pagination', {}).get('totalResults', len(d) if isinstance(d, list) else '?')
        print(f'OK  ?{param}  -> {nb} résultats')
    else:
        print(f'{r.status_code}  ?{param}')

# Tester /areas avec Accept JSON-LD (API Platform)
print("\n=== /areas avec JSON-LD ===")
h2 = dict(h)
h2['Accept'] = 'application/ld+json'
r = httpx.get(f'{base}/areas', headers=h2, timeout=10)
print(f'{r.status_code}')
if r.status_code == 200:
    print(r.text[:1000])

# Tester /shows avec JSON-LD pour voir les filtres disponibles (hydra:supportedProperty)
print("\n=== /shows JSON-LD (hydra:supportedProperty) ===")
r = httpx.get(f'{base}/shows', headers=h2, timeout=10)
print(f'{r.status_code}')
if r.status_code == 200:
    d = r.json()
    # Chercher les filtres hydra
    filters = d.get('hydra:search', {})
    print(json.dumps(filters, ensure_ascii=False, indent=2)[:2000])
