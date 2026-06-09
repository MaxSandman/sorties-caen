import httpx, re

headers = {"User-Agent": "Mozilla/5.0 Chrome/120.0.0.0 Safari/537.36"}
r = httpx.get("https://theatrealouest.com/main-es2015.3da1c0df74f899f50d97.js", headers=headers, timeout=30)
js = r.text

# Chercher api.theatrealouest.com dans le bundle
idx = js.find("api.theatrealouest")
if idx >= 0:
    print("TROUVE:", js[max(0, idx-50):idx+200])
else:
    print("api.theatrealouest non trouve")

# Chercher toutes les URLs theatrealouest dans le bundle
for m in re.finditer(r"https?://[a-z.]*theatrealouest[a-z.]*[^\"' >]{0,60}", js):
    print("URL:", m.group(0))

# Chercher le pattern d'env Angular: {production:true,...}
for m in re.finditer(r"\{production:!0,[^}]{0,300}\}", js):
    print("ENV:", m.group(0)[:300])
