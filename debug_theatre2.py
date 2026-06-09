import httpx, re

headers = {"User-Agent": "Mozilla/5.0 Chrome/120.0.0.0 Safari/537.36", "Accept-Language": "fr-FR"}

# Télécharger le bundle JS principal et chercher les URLs d'API
js_url = "https://theatrealouest.com/main-es2015.3da1c0df74f899f50d97.js"
print(f"Fetching {js_url} ...")
r = httpx.get(js_url, headers=headers, timeout=30)
print(f"Status: {r.status_code}, taille: {len(r.text)} bytes")

js = r.text

# Chercher des patterns d'URL d'API dans le JS
patterns = [
    r'["\`]([^"\`]*(?:spectacle|event|agenda|programme)[^"\`]*)["\`]',
    r'["\`](/[a-z0-9/_-]+(?:spectacle|event|agenda)[^"\`]*)["\`]',
    r'baseUrl[^=]*=[^"\`]*["\`]([^"\`]+)["\`]',
    r'apiUrl[^=]*=[^"\`]*["\`]([^"\`]+)["\`]',
    r'environment[.\w]*=[^{]*\{[^}]*url[^:]*:[^"\`]*["\`]([^"\`]+)["\`]',
]

found = set()
for pat in patterns:
    for m in re.finditer(pat, js, re.I):
        val = m.group(1)
        if len(val) > 3 and len(val) < 100 and ("." in val or val.startswith("/")):
            found.add(val)

print("\nURLs trouvées dans le JS:")
for f in sorted(found)[:30]:
    print(f"  {f}")
