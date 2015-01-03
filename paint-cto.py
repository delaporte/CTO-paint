#!/usr/bin/env python3
import os
import subprocess
from datetime import datetime, timedelta, timezone

# 7x5 font (rows are strings of '#' and '.')
FONT = {
    "I": [
        "#####",
        "..#..",
        "..#..",
        "..#..",
        "..#..",
        "..#..",
        "#####",
    ],
    "'": [
        "..#..",
        "..#..",
        ".....",
        ".....",
        ".....",
        ".....",
        ".....",
    ],
    "M": [
        "#...#",
        "##.##",
        "#.#.#",
        "#...#",
        "#...#",
        "#...#",
        "#...#",
    ],
    " ": [
        ".....",
        ".....",
        ".....",
        ".....",
        ".....",
        ".....",
        ".....",
    ],
    "C": [
        ".###.",
        "#...#",
        "#....",
        "#....",
        "#....",
        "#...#",
        ".###.",
    ],
    "T": [
        "#####",
        "..#..",
        "..#..",
        "..#..",
        "..#..",
        "..#..",
        "..#..",
    ],
    "O": [
        ".###.",
        "#...#",
        "#...#",
        "#...#",
        "#...#",
        "#...#",
        ".###.",
    ],
    "@": [
        ".###.",
        "#...#",
        "#.###",
        "#.#.#",
        "#.###",
        "#....",
        ".###.",
    ],
    "W": [
        "#...#",
        "#...#",
        "#...#",
        "#.#.#",
        "#.#.#",
        "##.##",
        "#...#",
    ],
    "E": [
        "#####",
        "#....",
        "####.",
        "#....",
        "#....",
        "#....",
        "#####",
    ],
    "G": [
        ".###.",
        "#...#",
        "#....",
        "#.###",
        "#...#",
        "#...#",
        ".####",
    ],
    "R": [
        "####.",
        "#...#",
        "#...#",
        "####.",
        "#.#..",
        "#..#.",
        "#...#",
    ],
    "F": [
        "#####",
        "#....",
        "####.",
        "#....",
        "#....",
        "#....",
        "#....",
    ],
    "L": [
        "#....",
        "#....",
        "#....",
        "#....",
        "#....",
        "#....",
        "#####",
    ],
    "A": [
        ".###.",
        "#...#",
        "#...#",
        "#####",
        "#...#",
        "#...#",
        "#...#",
    ],
    "N": [
        "#...#",
        "##..#",
        "#.#.#",
        "#..##",
        "#...#",
        "#...#",
        "#...#",
    ],
}

# Configuration des messages par période
# Chaque entrée : (date_début, message)
# Les périodes sont triées de la plus ancienne à la plus récente
# IMPORTANT: Utiliser des DIMANCHES car GitHub commence les semaines le dimanche
TIMELINE = [
    ("2015-01-04", "I'M FREELANCE"),  # Dimanche début 2015
    ("2020-01-05", "I'M CTO @ WEGROW"),  # Dimanche début 2020
    ("2022-01-09", "I'M CTO @ WEGROW"),  # Dimanche début 2022
    ("2024-01-07", "I'M CTO"),  # Dimanche début 2024
    ("2025-03-09", "I'M CTO"),  # Dimanche début 2025
]

# Use midday to avoid timezone edge-cases
HOUR = 12

# Paris offset (winter +01:00, summer +02:00). If you want it fixed, keep +01:00:
TZ = timezone(timedelta(hours=1))

PIXELS_FILE = "pixels.txt"

def run(cmd, env=None):
    subprocess.run(cmd, check=True, env=env)

def git(*args, env=None):
    run(["git", *args], env=env)

def build_rows(message: str):
    rows = [""] * 7
    for ch in message:
        if ch not in FONT:
            raise ValueError(f"Unsupported char: {ch!r}")
        glyph = FONT[ch]
        for r in range(7):
            rows[r] += glyph[r] + "."  # 1 column spacer
    return rows

def paint_message(message, start_date, all_commits):
    """Peint un message à partir d'une date de début et ajoute les commits à la liste."""
    rows = build_rows(message)
    width = len(rows[0])

    print(f"Peinture de '{message}' à partir du {start_date.date()} sur {width} colonnes...")

    for r in range(7):
        for c in range(width):
            if rows[r][c] != "#":
                continue

            ts = start_date + timedelta(weeks=c, days=r)
            all_commits.append((ts, message))

def main():
    # Vérifier qu'on est bien dans un repo git
    if not os.path.exists(".git"):
        print("Erreur: Ce script doit être exécuté dans un dépôt git existant.")
        print("Initialisez d'abord un dépôt git avec: git init")
        return

    # Sauvegarder la liste des fichiers actuels (non trackés et trackés)
    print("Sauvegarde des fichiers existants...")
    all_files = []
    for root, dirs, files in os.walk("."):
        # Ignorer le dossier .git
        if ".git" in root:
            continue
        for file in files:
            filepath = os.path.join(root, file)
            all_files.append(filepath)

    # Créer une nouvelle branche orpheline pour la peinture
    print("Création d'une nouvelle branche orpheline 'painted-history'...")
    git("checkout", "--orphan", "painted-history")

    # Nettoyer l'index mais garder les fichiers dans le working directory
    try:
        git("rm", "-rf", "--cached", ".")
    except:
        pass  # Ignore si rien à supprimer

    # Ajouter tous les fichiers existants (sauf pixels.txt qui sera géré séparément)
    print("Ajout des fichiers existants...")
    for filepath in all_files:
        if filepath != f"./{PIXELS_FILE}" and filepath != PIXELS_FILE:
            try:
                git("add", filepath)
            except:
                pass  # Ignore les erreurs pour les fichiers problématiques

    # Créer le fichier pixels initial
    with open(PIXELS_FILE, "w", encoding="utf-8") as f:
        f.write("pixel log\n")
    git("add", PIXELS_FILE)

    # Générer tous les commits pour toutes les périodes
    all_commits = []

    for start_monday_str, message in TIMELINE:
        start = datetime.fromisoformat(start_monday_str).replace(tzinfo=TZ, hour=HOUR, minute=0, second=0)
        paint_message(message, start, all_commits)

    # Trier tous les commits par date
    all_commits.sort(key=lambda x: x[0])

    # Trouver la date du premier commit pour l'init
    if all_commits:
        first_commit_date = all_commits[0][0]
        start_init = first_commit_date - timedelta(days=1)
    else:
        start_init = datetime.now(tz=TZ)

    # Premier commit initial avec tous les fichiers
    ts_init_str = start_init.isoformat(timespec="seconds")
    env = os.environ.copy()
    env["GIT_COMMITTER_DATE"] = ts_init_str
    git("commit", "--date", ts_init_str, "-m", "init", env=env)

    # Créer tous les commits dans l'ordre chronologique
    print(f"\nCréation de {len(all_commits)} commits...")
    for idx, (ts, message) in enumerate(all_commits, 1):
        if idx % 50 == 0:
            print(f"  {idx}/{len(all_commits)} commits créés...")

        ts_str = ts.isoformat(timespec="seconds")

        with open(PIXELS_FILE, "a", encoding="utf-8") as f:
            f.write(f"{ts_str}\n")

        git("add", PIXELS_FILE)

        env = os.environ.copy()
        env["GIT_COMMITTER_DATE"] = ts_str
        git("commit", "--date", ts_str, "-m", "pixel", env=env)

    print(f"\nTerminé! {len(all_commits)} commits créés.")
    print("\nPour remplacer votre branche main par l'historique peint:")
    print("  git branch -D main")
    print("  git branch -m painted-history main")
    print("\nPour forcer le push sur GitHub (ATTENTION: écrase l'historique distant):")
    print("  git push -f origin main")

if __name__ == "__main__":
    main()
