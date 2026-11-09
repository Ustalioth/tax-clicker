import os
import json
import time
import random
from datetime import date, datetime, timedelta
from pathlib import Path

from playwright.sync_api import sync_playwright

CODE = os.environ["CODE"]
INTERVALLE_MIN = 0.1  # 100 ms
INTERVALLE_MAX = 0.2  # 200 ms


def log(msg):
    print(f"[{datetime.now():%H:%M:%S}] {msg}", flush=True)


PROFIL = Path("/data/profil")
MARQUEUR = Path("/data/.code_charge")
ACTIVITE = Path("/data/activite.json")  # secondes de clics par jour

# Règle : jamais 3 jours consécutifs à plus de 18 h de clics.
# Si les 2 jours précédents dépassent 18 h, le jour courant est plafonné à 17 h 55.
SEUIL = 18 * 3600
PLAFOND = 17 * 3600 + 55 * 60


def charger_activite():
    try:
        return json.loads(ACTIVITE.read_text())
    except (OSError, ValueError):
        return {}


def sauver_activite(act):
    # On ne garde que les 7 derniers jours
    recents = dict(sorted(act.items())[-7:])
    tmp = ACTIVITE.with_suffix(".tmp")
    tmp.write_text(json.dumps(recents))
    tmp.replace(ACTIVITE)


def plafond_du_jour(act, jour):
    """Retourne le plafond en secondes pour `jour`, ou None si illimité."""
    veille = act.get((jour - timedelta(days=1)).isoformat(), 0)
    avant_veille = act.get((jour - timedelta(days=2)).isoformat(), 0)
    if veille > SEUIL and avant_veille > SEUIL:
        return PLAFOND
    return None


def run():
    with sync_playwright() as p:
        ctx = p.chromium.launch_persistent_context(str(PROFIL), headless=True)
        page = ctx.pages[0] if ctx.pages else ctx.new_page()

        # Le code n'est chargé qu'au tout premier lancement.
        if MARQUEUR.exists():
            page.goto("https://taxe-au-giga.fr/")
        else:
            page.goto(f"https://taxe-au-giga.fr/#code={CODE}")
            MARQUEUR.touch()

        btn = page.locator("#taxBtn")
        btn.wait_for(timeout=60_000)

        log("C'est parti !")

        n = 0
        jour = date.today()
        act = charger_activite()
        plafond = plafond_du_jour(act, jour)
        if plafond:
            log("2 jours > 18 h de suite : plafond de 17 h 55 aujourd'hui")
        dernier = time.monotonic()
        derniere_sauvegarde = dernier

        while True:
            # Temps de clic cumulé (on ignore les trous > 5 s : pause/arrêt)
            maintenant = time.monotonic()
            delta = maintenant - dernier
            dernier = maintenant
            if delta < 5:
                act[jour.isoformat()] = act.get(jour.isoformat(), 0) + delta

            if maintenant - derniere_sauvegarde > 30:
                sauver_activite(act)
                derniere_sauvegarde = maintenant

            # Plafond atteint : pause jusqu'à minuit
            if plafond and act.get(jour.isoformat(), 0) >= plafond:
                sauver_activite(act)
                log("Plafond de 17 h 55 atteint : pause jusqu'à minuit")
                while date.today() == jour:
                    time.sleep(30)
                dernier = time.monotonic()

            # Dimensions et position du bouton
            box = btn.bounding_box()

            if box:
                # Coordonnées aléatoires dans le bouton
                x = random.uniform(box["x"] + 2, box["x"] + box["width"] - 2)
                y = random.uniform(box["y"] + 2, box["y"] + box["height"] - 2)

                page.mouse.click(x, y)

            # Remise à zéro du compteur à minuit
            if date.today() != jour:
                sauver_activite(act)
                jour = date.today()
                n = 0
                plafond = plafond_du_jour(act, jour)
                log("Minuit : compteur remis à 0"
                    + (" (plafond 17 h 55 aujourd'hui)" if plafond else ""))

            n += 1

            if n % 1000 == 0:
                log(f"{n} clics")

            # Intervalle aléatoire entre 100 et 200 ms
            time.sleep(random.uniform(INTERVALLE_MIN, INTERVALLE_MAX))


while True:
    try:
        run()
    except Exception as e:
        log(f"Erreur : {e} — relance dans 30 s")
        time.sleep(30)
