# Sorties Caen 🎵

Calendrier local des salles de spectacle de Caen. Récupère automatiquement la programmation des 6 salles et affiche un calendrier avec une section "Dernières sorties programmées".

## Salles suivies

| Salle | URL |
|---|---|
| Théâtre à l'Ouest | https://theatrealouest.com/caen/spectacle/liste?sort=date-ASC |
| Zénith de Caen | https://zenith-caen.fr/ |
| Le Cargö | https://lecargo.fr/programmation/ |
| Le BBC (Big Band Café) | https://bigbandcafe.com/concerts/ |
| Palais des Sports | https://caenlamer.fr/palais-des-sports |
| Centre des Congrès | https://www.caen-evenements.com/agenda/ |

## Installation

```bash
# 1. Créer un environnement virtuel
python -m venv .venv
source .venv/bin/activate      # Linux/Mac
# .venv\Scripts\activate       # Windows

# 2. Installer les dépendances
pip install -r requirements.txt

# 3. Installer Playwright (navigateur headless pour le scraping)
playwright install chromium

# 4. Lancer l'application
python run.py
```

L'application est accessible sur **http://localhost:8000**

## Utilisation

- Le scraping est lancé **automatiquement au démarrage** et tourne ensuite **deux fois par jour** (7h et 19h).
- Cliquez sur **"↻ Mettre à jour"** dans l'interface pour forcer une mise à jour.
- Les **nouveaux événements** (ajoutés depuis la dernière visite) apparaissent en haut sous "Dernières sorties programmées".
- Filtrez par salle avec les boutons de filtre.
- Cliquez sur un jour du calendrier ou sur un événement pour voir les détails et le lien de réservation.

## Ajustement des scrapers

Si un scraper ne trouve pas d'événements, les sélecteurs CSS sont peut-être à ajuster :

```bash
# Voir le HTML brut d'une salle
python debug_scraper.py --html cargo

# Tester tous les scrapers
python debug_scraper.py

# Tester une salle spécifique
python debug_scraper.py --venue zenith
```

Les scrapers sont dans `app/scrapers/`. Chaque fichier contient en en-tête les sélecteurs à ajuster.

## Structure du projet

```
sorties-caen/
├── app/
│   ├── main.py          # FastAPI (routes API)
│   ├── database.py      # SQLite + modèles SQLAlchemy
│   ├── scheduler.py     # Scraping automatique (APScheduler)
│   ├── scrapers/
│   │   ├── base.py      # Classe de base (Playwright)
│   │   ├── theatre_ouest.py
│   │   ├── zenith.py
│   │   ├── cargo.py
│   │   ├── bbc.py
│   │   ├── palais_sports.py
│   │   └── caen_evenements.py
│   └── static/          # Frontend (HTML/CSS/JS vanilla)
├── debug_scraper.py     # Outil de debug des scrapers
├── run.py               # Point d'entrée
└── requirements.txt
```

## Options de lancement

```bash
python run.py                    # http://localhost:8000
python run.py --port 8080        # port personnalisé
python run.py --reload           # mode développement
python run.py --scrape-only      # scraping seul, sans serveur web
```
