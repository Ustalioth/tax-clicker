import os
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

CODE = os.environ["CODE"]
INTERVALLE = float(os.environ.get("INTERVALLE", "0.1"))  # secondes entre deux clics
PROFIL = Path("/data/profil")
MARQUEUR = Path("/data/.code_charge")


def run():
    with sync_playwright() as p:
        ctx = p.chromium.launch_persistent_context(str(PROFIL), headless=True)
        page = ctx.pages[0] if ctx.pages else ctx.new_page()

        # Le code n'est chargé qu'au tout premier lancement : ensuite la partie
        # est dans le profil persistant, et recharger le code écraserait la progression.
        if MARQUEUR.exists():
            page.goto("https://taxe-au-giga.fr/")
        else:
            page.goto(f"https://taxe-au-giga.fr/#code={CODE}")
            MARQUEUR.touch()

        btn = page.locator("#taxBtn")
        btn.wait_for(timeout=60_000)

        # Masque l'astuce « zen » qui s'affiche au 40e clic et recouvre le bouton
        page.add_style_tag(content="#zenTip { display: none !important; }")
        print("C'est parti !", flush=True)

        n = 0
        while True:
            btn.click(timeout=10_000)
            n += 1
            if n % 1000 == 0:
                print(f"{n} clics", flush=True)
            time.sleep(INTERVALLE)


while True:
    try:
        run()
    except Exception as e:
        print(f"Erreur : {e} — relance dans 30 s", flush=True)
        time.sleep(30)
