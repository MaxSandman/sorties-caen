"""
Script de correction de l'encodage - a executer une seule fois.
Corrige les problemes d'affichage des caracteres speciaux sur Windows.
"""
import os, re

BASE = os.path.dirname(os.path.abspath(__file__))

# ---- 1. Corriger main.py ----
main_path = os.path.join(BASE, "app", "main.py")
main_src  = open(main_path, encoding="utf-8").read()
old = 'with open("app/static/index.html") as f:\n        return f.read()'
new = ('with open("app/static/index.html", encoding="utf-8") as f:\n'
       '        return HTMLResponse(content=f.read(), media_type="text/html; charset=utf-8")')
if old in main_src:
    open(main_path, "w", encoding="utf-8").write(main_src.replace(old, new))
    print("[OK] app/main.py corrige")
else:
    print("[OK] app/main.py deja a jour")

# ---- 2. Corriger index.html (remplacer emoji logo) ----
html_path = os.path.join(BASE, "app", "static", "index.html")
html_src  = open(html_path, encoding="utf-8").read()
replacements_html = [
    ("\U0001f3b5", "&#9835;"),   # 🎵
    ("↻", "&#8635;"),       # ↻
    ("\xe0", "&#224;"),          # à
    ("Derni\xe8res", "Derni&#232;res"),
    ("programm\xe9es", "programm&#233;es"),
    ("r\xe9cup\xe9ration", "r&#233;cup&#233;ration"),
    ("Chargement…", "Chargement&#8230;"),
    ("Év\xe9nements", "&#201;v&#233;nements"),
    ("d\xe9tail", "d&#233;tail"),
    ("✕", "&#10005;"),
    ("—", "&#8212;"),
]
new_html = html_src
for old_c, new_c in replacements_html:
    new_html = new_html.replace(old_c, new_c)
# Also escape any remaining non-ASCII in HTML file
result = ""
for ch in new_html:
    if ord(ch) > 127:
        result += "&#{};".format(ord(ch))
    else:
        result += ch
open(html_path, "w", encoding="ascii").write(result)
print("[OK] app/static/index.html corrige")

# ---- 3. Corriger app.js (remplacer tout non-ASCII par \uXXXX) ----
js_path = os.path.join(BASE, "app", "static", "js", "app.js")
js_src  = open(js_path, encoding="utf-8").read()
result  = ""
for ch in js_src:
    if ord(ch) > 127:
        result += "\\u{:04X}".format(ord(ch))
    else:
        result += ch
open(js_path, "w", encoding="ascii").write(result)
print("[OK] app/static/js/app.js corrige")

print("\nCorrection terminee ! Redemarrez le serveur avec: python run.py")
