import httpx, re

headers = {"User-Agent": "Mozilla/5.0 Chrome/120.0.0.0 Safari/537.36", "Accept-Language": "fr-FR"}

js_url = "https://theatrealouest.com/main-es2015.3da1c0df74f899f50d97.js"
r = httpx.get(js_url, headers=headers, timeout=30)
js = r.text

# Chercher toutes les URLs https:// dans le JS
urls = re.findall(r'https?://[^\s"\'`\\]{5,80}', js)
found = set()
for u in urls:
    # Exclure les CDNs connus et garder ce qui ressemble à une API
    if not any(x in u for x in ["google", "facebook", "twitter", "youtube", "jsdelivr",
                                  "cloudflare", "jquery", "bootstrap", "font"]):
        found.add(u.rstrip(".,);\"'`"))

print("URLs non-CDN dans le JS:")
for u in sorted(found):
    print(f"  {u}")

# Chercher aussi les chemins relatifs qui ressemblent à des appels API
api_paths = re.findall(r'"(/[a-z]{2}/[a-z/_-]{3,50})"', js)
print("\nChemins relatifs type /xx/xxx:")
for p in sorted(set(api_paths))[:20]:
    print(f"  {p}")
