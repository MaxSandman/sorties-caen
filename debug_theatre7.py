import httpx, json, os

email = os.environ['THEATRE_OUEST_EMAIL']
password = os.environ['THEATRE_OUEST_PASSWORD']
h = {'Content-Type': 'application/json', 'Accept': 'application/json'}
token = httpx.post('https://api.theatrealouest.com/login',
    json={'username': email, 'password': password}, headers=h, timeout=10).json()['token']
h['Authorization'] = f'Bearer {token}'

CAEN_ID = '5e4e0cb9-ac24-40a9-8a79-216ec1b0b3f4'

r = httpx.get(f'https://api.theatrealouest.com/shows?area={CAEN_ID}', headers=h, timeout=10)
data = r.json()
print('Clés racine:', list(data.keys()) if isinstance(data, dict) else f'Liste de {len(data)} items')
if isinstance(data, dict):
    print('Aperçu:', json.dumps(data, ensure_ascii=False)[:600])
elif isinstance(data, list):
    print(f'Premier item clés: {list(data[0].keys())}')
    print(json.dumps(data[0], ensure_ascii=False, indent=2)[:800])
