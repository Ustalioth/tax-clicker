import os
import time
import random
from pathlib import Path

from playwright.sync_api import sync_playwright

CODE = os.environ["CODE"]
INTERVALLE_MIN = 0.1  # 100 ms
INTERVALLE_MAX = 0.2  # 200 ms

PROFIL = Path("/data/profil")
MARQUEUR = Path("/data/.code_charge")


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

        print("C'est parti !", flush=True)

        n = 0

        while True:
            # Dimensions et position du bouton
            box = btn.bounding_box()

            if box:
                # Coordonnées aléatoires dans le bouton
                x = random.uniform(box["x"] + 2, box["x"] + box["width"] - 2)
                y = random.uniform(box["y"] + 2, box["y"] + box["height"] - 2)

                page.mouse.click(x, y)

            n += 1

            if n % 1000 == 0:
                print(f"{n} clics", flush=True)

            # Intervalle aléatoire entre 100 et 200 ms
            time.sleep(random.uniform(INTERVALLE_MIN, INTERVALLE_MAX))


while True:
    try:
        run()
    except Exception as e:
        print(f"Erreur : {e} — relance dans 30 s", flush=True)
        time.sleep(30)
