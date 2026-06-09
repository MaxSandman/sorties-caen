import httpx, re

headers = {"User-Agent": "Mozilla/5.0 Chrome/120.0.0.0 Safari/537.36", "Accept-Language": "fr-FR"}

r = httpx.get("https://theatrealouest.com/caen/spectacle/liste?sort=date-ASC", headers=headers, follow_redirects=True, timeout=20)
print(f"Status: {r.status_code}")

# Chercher des URLs d'API dans le HTML/JS inline
api_hints = re.findall(r'["\']([^"\']*(?:api|json|graphql|endpoint)[^"\']*)["\']', r.text, re.I)
for h in sorted(set(api_hints))[:20]:
    print(f"  API hint: {h}")

# Fichiers JS chargés
scripts = re.findall(r'src=["\']([^"\']+\.js[^"\']*)["\']', r.text)
for s in scripts[:10]:
    print(f"  JS: {s}")

# Essayer des endpoints API courants pour Angular
print("\n--- Test endpoints API ---")
for path in ["/api/spectacles", "/api/events", "/api/programmation",
             "/caen/api/spectacles", "/caen/api/events"]:
    try:
        r2 = httpx.get("https://theatrealouest.com" + path, headers=headers, timeout=10)
        print(f"  {path} → {r2.status_code} ({len(r2.text)} bytes)")
        if r2.status_code == 200 and r2.text.strip().startswith("["):
            print(f"    JSON ARRAY! Premier item: {r2.text[:200]}")
    except Exception as e:
        print(f"  {path} → ERREUR: {e}")
