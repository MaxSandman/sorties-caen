import httpx, re, json, os

email = os.environ['THEATRE_OUEST_EMAIL']
password = os.environ['THEATRE_OUEST_PASSWORD']
h_api = {'Content-Type': 'application/json', 'Accept': 'application/json'}
token = httpx.post('https://api.theatrealouest.com/login',
    json={'username': email, 'password': password}, headers=h_api, timeout=10).json()['token']
h_api['Authorization'] = f'Bearer {token}'

# 1. Fetch la page HTML du site pour trouver le bundle JS actuel
print("=== Bundle JS actuel ===")
h_web = {"User-Agent": "Mozilla/5.0 Chrome/120.0.0.0 Safari/537.36"}
r = httpx.get("https://theatrealouest.com/caen/spectacle/liste", headers=h_web, timeout=30)
# Trouver les scripts
scripts = re.findall(r'src="([^"]*main[^"]*\.js)"', r.text)
print("Scripts trouvés:", scripts[:5])
# Aussi chercher les fichiers chunk
chunks = re.findall(r'"([^"]*\d+\.[a-f0-9]+\.js)"', r.text)
print("Chunks:", chunks[:10])

# 2. Fetch le bundle principal
bundle_url = None
if scripts:
    bundle_url = scripts[0]
    if not bundle_url.startswith('http'):
        bundle_url = 'https://theatrealouest.com' + bundle_url
    print(f"\nFetch bundle: {bundle_url}")
    r2 = httpx.get(bundle_url, headers=h_web, timeout=60)
    js = r2.text

    # Chercher le pattern d'appel API pour les shows avec area/selectedArea
    print("\n=== Patterns API shows ===")
    for pattern in [r'shows[^"]{0,100}area[^"]{0,100}', r'selectedArea[^"]{0,200}',
                    r'spectacle[^"]{0,100}', r'/shows\?[^"]{0,100}',
                    r'areaId[^"]{0,100}', r'\.slug[^"]{0,200}']:
        matches = re.findall(pattern, js)
        for m in matches[:3]:
            print(f"  [{pattern[:20]}]: {m[:200]}")

# 3. GET /areas/{id} avec le bon token
print("\n=== GET /areas/{id} ===")
CAEN_ID = '5e4e0cb9-ac24-40a9-8a79-216ec1b0b3f4'
r = httpx.get(f'https://api.theatrealouest.com/areas/{CAEN_ID}', headers=h_api, timeout=8)
print(f'Status: {r.status_code}')
if r.status_code == 200:
    print(json.dumps(r.json(), ensure_ascii=False, indent=2)[:800])
else:
    print(r.text[:200])

# 4. Essayer sort=date-ASC sur shows
print("\n=== /shows?sort=date-ASC ===")
r = httpx.get('https://api.theatrealouest.com/shows?sort=date-ASC', headers=h_api, timeout=10)
print(f'Status: {r.status_code}')
if r.status_code == 200:
    d = r.json()
    members = d.get('members', [])
    print(f'Total: {d.get("pagination", {}).get("totalResults")}')
    if members:
        # Voir si les slots sont différents avec ce tri
        print('slots[0]:', members[0].get('slots'))
