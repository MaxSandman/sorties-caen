import httpx
from bs4 import BeautifulSoup

headers = {"User-Agent": "Mozilla/5.0 Chrome/120.0.0.0 Safari/537.36", "Accept-Language": "fr-FR"}

sites = [
    ("https://lecargo.fr/programmation/", "cargo"),
    ("https://bigbandcafe.com/concerts/", "bbc"),
    ("https://theatrealouest.com/caen/spectacle/liste?sort=date-ASC", "theatre"),
]

for url, name in sites:
    try:
        r = httpx.get(url, headers=headers, follow_redirects=True, timeout=20)
        soup = BeautifulSoup(r.text, "html.parser")
        all_classes = set()
        for tag in soup.find_all(True):
            for cls in (tag.get("class") or []):
                all_classes.add(f"{tag.name}.{cls}")
        print(f"=== {name} ({r.status_code}) ===")
        keywords = ["item", "card", "event", "show", "date", "title", "artist", "prog", "spectacle", "concert"]
        for c in sorted(all_classes):
            if any(k in c.lower() for k in keywords):
                print(f"  {c}")
        # Also show first event-like link
        for a in soup.select("a[href]")[:100]:
            href = a.get("href", "")
            if any(k in href for k in ["/spectacle/", "/concert", "/event", "/agenda", "/programmation/"]):
                txt = a.get_text(strip=True)[:60]
                if txt and len(txt) > 3:
                    print(f"  LINK: {href[:70]} | {txt}")
                    break
        print()
    except Exception as e:
        print(f"=== {name} ERROR: {e} ===\n")
