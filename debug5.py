import httpx
from bs4 import BeautifulSoup

headers = {"User-Agent": "Mozilla/5.0 Chrome/120.0.0.0 Safari/537.36", "Accept-Language": "fr-FR"}

sites = [
    ("https://zenith-caen.fr/", "zenith"),
    ("https://caenlamer.fr/palais-des-sports", "palais"),
    ("https://www.caen-evenements.com/agenda/", "caen_evt"),
]

for url, name in sites:
    try:
        r = httpx.get(url, headers=headers, follow_redirects=True, timeout=20)
        soup = BeautifulSoup(r.text, "html.parser")
        print(f"=== {name} ({r.status_code}) ===")

        # Trouver toutes les classes uniques
        all_cls = {}
        for tag in soup.find_all(True):
            for cls in (tag.get("class") or []):
                key = f"{tag.name}.{cls}"
                all_cls[key] = all_cls.get(key, 0) + 1

        # Afficher les plus fréquentes et celles avec mots-clés
        keywords = ["event", "concert", "show", "date", "title", "item", "card",
                    "agenda", "spectacle", "prog", "article", "actu"]
        for c, count in sorted(all_cls.items(), key=lambda x: -x[1])[:5]:
            print(f"  [{count}x] {c}")
        print("  ---")
        for c in sorted(all_cls):
            if any(k in c.lower() for k in keywords):
                print(f"  {c}")

        # Premier article/li avec du contenu
        for tag in soup.find_all(["article", "li"], limit=200):
            cls = " ".join(tag.get("class") or [])
            txt = tag.get_text(strip=True)
            if cls and len(txt) > 30:
                print(f"\n  PREMIER {tag.name}.{cls[:50]}:")
                print(f"  {tag.prettify()[:600]}")
                break
        print()
    except Exception as e:
        print(f"=== {name} ERREUR: {e} ===\n")
