import httpx
from bs4 import BeautifulSoup

headers = {"User-Agent": "Mozilla/5.0 Chrome/120.0.0.0 Safari/537.36", "Accept-Language": "fr-FR"}

# CARGO
r = httpx.get("https://lecargo.fr/programmation/", headers=headers, follow_redirects=True, timeout=20)
soup = BeautifulSoup(r.text, "html.parser")
print("=== CARGO - premiere a.list__title ===")
first = soup.select_one("a.list__title")
if first:
    print(first.parent.prettify()[:1500])
else:
    print("Pas trouve")

# BBC
r2 = httpx.get("https://bigbandcafe.com/concerts/", headers=headers, follow_redirects=True, timeout=20)
soup2 = BeautifulSoup(r2.text, "html.parser")
print("\n=== BBC - premier div.post-item ===")
first2 = soup2.select_one("div.post-item")
if first2:
    print(first2.prettify()[:1500])
else:
    print("Pas trouve")

# THEATRE
r3 = httpx.get("https://theatrealouest.com/caen/spectacle/liste?sort=date-ASC", headers=headers, follow_redirects=True, timeout=20)
soup3 = BeautifulSoup(r3.text, "html.parser")
print("\n=== THEATRE - toutes classes ===")
all_cls = set()
for tag in soup3.find_all(True):
    for cls in (tag.get("class") or []):
        all_cls.add(f"{tag.name}.{cls}")
for c in sorted(all_cls)[:50]:
    print(" ", c)
