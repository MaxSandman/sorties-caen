import httpx
from bs4 import BeautifulSoup
headers = {"User-Agent": "Mozilla/5.0 Chrome/120.0.0.0 Safari/537.36", "Accept-Language": "fr-FR"}
r = httpx.get("https://lecargo.fr/programmation/", headers=headers, follow_redirects=True, timeout=20)
soup = BeautifulSoup(r.text, "html.parser")
prog = soup.select_one("main.page-programmation") or soup.select_one("div.programmation")
if prog:
    print(prog.prettify()[:4000])
