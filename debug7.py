import httpx
from bs4 import BeautifulSoup

headers = {"User-Agent": "Mozilla/5.0 Chrome/120.0.0.0 Safari/537.36", "Accept-Language": "fr-FR"}

r = httpx.get("https://zenith-caen.fr/", headers=headers, follow_redirects=True, timeout=20)
soup = BeautifulSoup(r.text, "html.parser")

print("=== ZENITH dates + titres ===")
for card in soup.select("li.spectacle-item-wrapper")[:6]:
    h4 = card.select_one("h4")
    date_p = card.select_one("p.date")
    booking = card.select_one("a.button-white")
    detail = card.select_one("a.button-dark")
    title = h4.get_text(strip=True) if h4 else "?"
    # get_text enlève le SVG automatiquement
    date_txt = date_p.get_text(strip=True) if date_p else "?"
    print(f"  {title[:40]} | DATE: '{date_txt}' | URL: {detail['href'] if detail else '?'}")
