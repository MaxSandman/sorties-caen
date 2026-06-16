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

## Installation locale

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

## Déploiement Docker (NAS / serveur)

```bash
# Construire et lancer
docker-compose up -d --build

# Suivre les logs
docker logs -f sorties-caen
```

La base SQLite est persistée dans `./data` (volume monté). Le conteneur
embarque Chromium ; aucun service navigateur externe n'est requis.

> **Note Synology / Docker** : le `docker-compose.yml` définit
> `security_opt: seccomp:unconfined` et `shm_size: 256mb`. Ces réglages sont
> nécessaires pour que Chromium puisse établir ses connexions réseau dans le
> conteneur (sans quoi le scraping échoue en timeout).

### Notifications ntfy (optionnel)

L'app peut envoyer une notification [ntfy](https://ntfy.sh) à chaque nouvel
événement détecté. Définissez votre topic dans un fichier `.env` à la racine :

```bash
echo "NTFY_TOPIC=mon-topic-prive" > .env
docker-compose up -d        # pas besoin de rebuild
```

Abonnez-vous ensuite au même topic dans l'app ntfy (mobile/web). Si
`NTFY_TOPIC` est vide, les notifications sont simplement ignorées.

> Le fichier `.env` n'est pas versionné (gitignore) : il faut le recréer si le
> conteneur est reconstruit sur une autre machine.

## Utilisation

- Le scraping est lancé **automatiquement au démarrage** et tourne ensuite
  **deux fois par jour** (7h et 19h, fuseau Europe/Paris). Les salles sont
  scrapées **séquentiellement** (un seul Chromium à la fois) pour éviter la
  contention de ressources dans le conteneur.
- Cliquez sur le bouton **↻** dans la barre du haut pour forcer une mise à
  jour. Le scrape tourne en arrière-plan (~1-2 min) ; le bouton reste en
  rotation jusqu'à sa complétion, puis l'horodatage "Mis à jour" se rafraîchit.
  Le déclenchement manuel est réservé au **réseau local** (localhost + IP
  privées).
- Les **nouveaux événements** apparaissent dans la cloche 🔔 et sur la page
  Nouveautés.
- Filtrez par salle, catégorie et date ; cliquez sur un événement pour voir la
  fiche détaillée et le lien de réservation.

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

### Notes sur le scraping

- **Théâtre à l'Ouest** utilise une API JSON (`use_playwright = False`) : pas de
  navigateur, c'est le plus rapide et le plus stable.
- **Le Cargö, Zénith, BBC, Caen Événements** bloquent les requêtes HTTP directes
  (403) et/ou rendent leur contenu en JavaScript : ils nécessitent Playwright.
- La navigation Playwright utilise `wait_until="commit"` puis attend le sélecteur
  de contenu réel. Ces sites chargent des trackers qui empêchent
  `domcontentloaded`/`networkidle` de se déclencher dans le délai imparti.
- Les sites de salles **changent régulièrement leur structure HTML**. Si un
  scraper retombe à 0 événement, vérifiez d'abord les sélecteurs et l'URL de la
  page de programmation (elles bougent).

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
