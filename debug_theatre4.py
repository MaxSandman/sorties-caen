import httpx, re

headers = {"User-Agent": "Mozilla/5.0 Chrome/120.0.0.0 Safari/537.36", "Accept-Language": "fr-FR"}

js_url = "https://theatrealouest.com/main-es2015.3da1c0df74f899f50d97.js"
r = httpx.get(js_url, headers=headers, timeout=30)
js = r.text

# Chercher les strings contenant "spectacle", "caen", "programme" dans le JS
print("=== Strings avec 'spectacle'/'caen'/'programme' ===")
for pat in [r'"([^"]{0,40}spectacle[^"]{0,40})"', r'"([^"]{0,40}programme[^"]{0,40})"',
            r'"([^"]{0,30}/caen/[^"]{0,30})"']:
    for m in re.finditer(pat, js, re.I):
        val = m.group(1)
        if not any(x in val.lower() for x in ["function", "class", "=>", "import"]):
            print(f"  {val}")

# Tester des endpoints probables directement
print("\n=== Test endpoints ===")
base = "https://theatrealouest.com"
paths = [
    "/caen/spectacle",
    "/api/caen/spectacle/liste",
    "/caen/spectacle?sort=date-ASC&format=json",
    "/caen/spectacle/liste?_format=json",
    "/spectacle/liste",
    "/fr/spectacle",
    "/json/spectacles",
]
for path in paths:
    try:
        r2 = httpx.get(base + path, headers={**headers, "Accept": "application/json"},
                       timeout=10, follow_redirects=True)
        ct = r2.headers.get("content-type", "")
        is_json = "json" in ct or r2.text.strip().startswith(("[", "{"))
        print(f"  {path} → {r2.status_code} {len(r2.text)}b {'JSON!' if is_json else ct[:30]}")
    except Exception as e:
        print(f"  {path} → ERR: {e}")
