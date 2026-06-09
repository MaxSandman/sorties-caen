import httpx
from bs4 import BeautifulSoup

headers = {"User-Agent": "Mozilla/5.0 Chrome/120.0.0.0 Safari/537.36", "Accept-Language": "fr-FR"}

# ZENITH
r = httpx.get("https://zenith-caen.fr/", headers=headers, follow_redirects=True, timeout=20)
soup = BeautifulSoup(r.text, "html.parser")
print("=== ZENITH - premier li.spectacle-item-wrapper ===")
card = soup.select_one("li.spectacle-item-wrapper")
if card:
    print(card.prettify()[:2000])
else:
    print("Non trouve - essai div.spectacle-item:")
    card = soup.select_one("div.spectacle-item")
    if card:
        print(card.prettify()[:2000])

print()

# CAEN EVENEMENTS
r2 = httpx.get("https://www.caen-evenements.com/agenda/", headers=headers, follow_redirects=True, timeout=20)
soup2 = BeautifulSoup(r2.text, "html.parser")
print("=== CAEN EVENEMENTS - premiere a.ce_events-item ===")
card2 = soup2.select_one("a.ce_events-item")
if card2:
    print(card2.prettify()[:2000])

print()

# PALAIS - chercher des events dans la page
r3 = httpx.get("https://caenlamer.fr/palais-des-sports", headers=headers, follow_redirects=True, timeout=20)
soup3 = BeautifulSoup(r3.text, "html.parser")
print("=== PALAIS - item_content ===")
item = soup3.select_one("div.item_content")
if item:
    print(item.prettify()[:1500])
else:
    # Chercher liens vers agenda
    for a in soup3.select("a[href]"):
        href = a.get("href", "")
        if "agenda" in href or "programme" in href or "event" in href:
            print(f"LIEN AGENDA: {href}")
