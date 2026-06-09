import httpx
from bs4 import BeautifulSoup

headers = {"User-Agent": "Mozilla/5.0 Chrome/120.0.0.0 Safari/537.36", "Accept-Language": "fr-FR"}

# CARGO - chercher une API JSON ou le vrai contenu events
r = httpx.get("https://lecargo.fr/programmation/", headers=headers, follow_redirects=True, timeout=20)
soup = BeautifulSoup(r.text, "html.parser")

# Chercher scripts avec des données JSON inline
print("=== CARGO scripts avec data ===")
for script in soup.find_all("script"):
    src = script.get("src", "")
    txt = script.string or ""
    if any(k in txt for k in ["concert", "event", "spectacle", "date", "programmation"]):
        print(txt[:400])
        print("---")

# Chercher balises avec data-* contenant des events
print("\n=== CARGO data-attributes ===")
for tag in soup.find_all(True):
    for attr, val in tag.attrs.items():
        if attr.startswith("data-") and isinstance(val, str) and len(val) > 20:
            print(f"{tag.name}[{attr}]: {str(val)[:100]}")

# Montrer le contenu brut de div.programmation
print("\n=== CARGO div.programmation innerHTML ===")
prog = soup.select_one("div.programmation")
if prog:
    print(prog.prettify()[:2000])
