import httpx, json, os

email = os.environ['THEATRE_OUEST_EMAIL']
password = os.environ['THEATRE_OUEST_PASSWORD']
h = {'Content-Type': 'application/json', 'Accept': 'application/json'}
token = httpx.post('https://api.theatrealouest.com/login',
    json={'username': email, 'password': password}, headers=h, timeout=10).json()['token']
h['Authorization'] = f'Bearer {token}'

CAEN_ID = '5e4e0cb9-ac24-40a9-8a79-216ec1b0b3f4'
base = 'https://api.theatrealouest.com'

# Symfony API Platform filter syntaxes
params_to_try = [
    f'area[]={CAEN_ID}',
    f'area.id={CAEN_ID}',
    f'area.name=Caen',
    f'areas[]={CAEN_ID}',
    f'filter[area]={CAEN_ID}',
    'area=caen',
    'site=caen',
    'selectedArea=caen',
    f'selectedArea={CAEN_ID}',
]

for param in params_to_try:
    r = httpx.get(f'{base}/shows?{param}', headers=h, timeout=8)
    if r.status_code == 200:
        data = r.json()
        nb = data.get('pagination', {}).get('totalResults', len(data) if isinstance(data, list) else '?')
        print(f'OK  ?{param}  -> {nb} résultats')
    else:
        print(f'{r.status_code}  ?{param}')

# Aussi tester /areas/{id}/shows
print()
for path in [f'/areas/{CAEN_ID}/shows', f'/areas/{CAEN_ID}']:
    r = httpx.get(base + path, headers=h, timeout=8)
    print(f'{r.status_code}  {path}  {r.text[:100].replace(chr(10)," ")}')
