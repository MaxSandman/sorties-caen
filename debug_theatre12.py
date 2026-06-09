import httpx, json, os

email = os.environ['THEATRE_OUEST_EMAIL']
password = os.environ['THEATRE_OUEST_PASSWORD']
h = {'Content-Type': 'application/json', 'Accept': 'application/json'}
token = httpx.post('https://api.theatrealouest.com/login',
    json={'username': email, 'password': password}, headers=h, timeout=10).json()['token']
h['Authorization'] = f'Bearer {token}'

base = 'https://api.theatrealouest.com'
CAEN_ID = '5e4e0cb9-ac24-40a9-8a79-216ec1b0b3f4'

# 1. Structure d'un show (clé = members)
print("=== Show complet ===")
r = httpx.get(f'{base}/shows?page=1', headers=h, timeout=10)
d = r.json()
members = d.get('members', [])
if members:
    print(json.dumps(members[0], ensure_ascii=False, indent=2))
else:
    print("Pas de membres! Clés:", list(d.keys()))

# 2. Chercher un show qui a 'caen' dans ses données
print("\n=== Cherche un show avec Caen ===")
found = False
for page in range(1, 5):
    r = httpx.get(f'{base}/shows?page={page}', headers=h, timeout=10)
    members = r.json().get('members', [])
    for show in members:
        txt = json.dumps(show).lower()
        if 'caen' in txt:
            print(f"TROUVE page {page}:")
            print(json.dumps(show, ensure_ascii=False, indent=2)[:1500])
            found = True
            break
    if found:
        break
if not found:
    print("Pas trouvé dans les 4 premières pages")
    # Afficher toutes les clés d'un show
    r = httpx.get(f'{base}/shows?page=1', headers=h, timeout=10)
    members = r.json().get('members', [])
    if members:
        print("\nClés d'un show:", list(members[0].keys()))
        # Afficher les valeurs non-nulles
        for k, v in members[0].items():
            if v is not None and v != [] and v != {}:
                print(f"  {k}: {str(v)[:100]}")
