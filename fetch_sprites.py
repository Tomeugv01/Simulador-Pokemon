"""
Fetch and save Pokemon sprites from the PokeAPI.

Downloads front/back sprites, Gen 7 (USUM) sprites, box icons,
Gen 5 battle animations (the only generation with animated GIFs on PokeAPI),
and shiny variants for all of the above.
Files are named by Pokemon ID (not name).

NOTE ON ANIMATIONS:
    PokeAPI only hosts animated battle sprites for Gen 5 (Black/White).
    No animated GIFs exist for Gen 6, 7 or later on PokeAPI.

Output directory structure:
    data/sprites/
        front/                  - Default front sprite         ({id}.png)
        front/shiny/            - Default front shiny          ({id}.png)
        back/                   - Default back sprite          ({id}.png)
        back/shiny/             - Default back shiny           ({id}.png)
        icons/gen7/             - Gen 7 box icons              ({id}.png)
        gen7/front/             - USUM front sprite            ({id}.png)  [all gens]
        gen7/front/shiny/       - USUM front shiny             ({id}.png)  [all gens]
        animations/front/       - Gen 5 BW animated front      ({id}.gif)  [Gen 1-5 only]
        animations/front/shiny/ - Gen 5 BW animated shiny front({id}.gif)  [Gen 1-5 only]
        animations/back/        - Gen 5 BW animated back        ({id}.gif)  [Gen 1-5 only]
        animations/back/shiny/  - Gen 5 BW animated shiny back  ({id}.gif)  [Gen 1-5 only]
"""

import os
import sys
import time
import sqlite3
import requests
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
DB_PATH = "data/pokemon_battle.db"
SPRITES_ROOT = "data/sprites"

# PokeAPI raw sprite URLs (GitHub-hosted, no rate limit)
BASE_RAW = "https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon"
BASE_G5  = f"{BASE_RAW}/versions/generation-v/black-white/animated"
BASE_G7  = f"{BASE_RAW}/versions/generation-vii/ultra-sun-ultra-moon"

SPRITE_SOURCES = {
    # category              (sub-directory,               url template,                                    extension)

    # --- Default front / back (Gen 8 art style, best coverage) ---
    "front":                ("front",                     f"{BASE_RAW}/{{id}}.png",                        "png"),
    "front_shiny":          ("front/shiny",               f"{BASE_RAW}/shiny/{{id}}.png",                  "png"),
    "back":                 ("back",                      f"{BASE_RAW}/back/{{id}}.png",                   "png"),
    "back_shiny":           ("back/shiny",                f"{BASE_RAW}/back/shiny/{{id}}.png",             "png"),

    # --- Gen 7 (Ultra Sun / Ultra Moon) static sprites ---
    "gen7_front":           ("gen7/front",                f"{BASE_G7}/{{id}}.png",                         "png"),
    "gen7_front_shiny":     ("gen7/front/shiny",          f"{BASE_G7}/shiny/{{id}}.png",                   "png"),

    # --- Gen 7 box icons ---
    "icon_gen7":            ("icons/gen7",                f"{BASE_RAW}/versions/generation-vii/icons/{{id}}.png", "png"),

    # --- Gen 5 battle animations (only generation with animated GIFs on PokeAPI) ---
    "anim_front":           ("animations/front",          f"{BASE_G5}/{{id}}.gif",                         "gif"),
    "anim_front_shiny":     ("animations/front/shiny",    f"{BASE_G5}/shiny/{{id}}.gif",                   "gif"),
    "anim_back":            ("animations/back",           f"{BASE_G5}/back/{{id}}.gif",                    "gif"),
    "anim_back_shiny":      ("animations/back/shiny",     f"{BASE_G5}/back/shiny/{{id}}.gif",              "gif"),
}

# Max parallel downloads
MAX_WORKERS = 10

# Retry settings
MAX_RETRIES = 3
RETRY_DELAY = 1  # seconds


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def get_pokemon_ids_from_db(db_path: str) -> list[int]:
    """Return a sorted list of all Pokemon IDs stored in the local database."""
    if not os.path.exists(db_path):
        print(f"ERROR: Database not found at '{db_path}'")
        sys.exit(1)

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM pokemon ORDER BY id")
    ids = [row[0] for row in cursor.fetchall()]
    conn.close()
    return ids


def ensure_directories():
    """Create the output directory tree if it doesn't already exist."""
    for _category, (sub_dir, _url, _ext) in SPRITE_SOURCES.items():
        path = Path(SPRITES_ROOT) / sub_dir
        path.mkdir(parents=True, exist_ok=True)


def download_file(url: str, dest: str, retries: int = MAX_RETRIES) -> bool:
    """Download a single file with retries. Returns True on success."""
    for attempt in range(1, retries + 1):
        try:
            resp = requests.get(url, timeout=15)
            if resp.status_code == 200:
                with open(dest, "wb") as f:
                    f.write(resp.content)
                return True
            elif resp.status_code == 404:
                # Resource genuinely missing – no point retrying
                return False
            else:
                # Transient error – retry after delay
                time.sleep(RETRY_DELAY * attempt)
        except requests.RequestException:
            time.sleep(RETRY_DELAY * attempt)
    return False


# ---------------------------------------------------------------------------
# Main download logic
# ---------------------------------------------------------------------------
def download_sprites_for_pokemon(pokemon_id: int) -> dict:
    """Download all sprite categories for a single Pokemon.

    Returns a dict  {category: True/False}  indicating success per category.
    """
    results = {}
    for category, (sub_dir, url_template, ext) in SPRITE_SOURCES.items():
        url = url_template.format(id=pokemon_id)
        dest = os.path.join(SPRITES_ROOT, sub_dir, f"{pokemon_id}.{ext}")

        # Skip if file already exists (resume-friendly)
        if os.path.exists(dest):
            results[category] = True
            continue

        results[category] = download_file(url, dest)
    return results


def main():
    print("=== Pokemon Sprite Downloader ===\n")

    # 1. Read Pokemon IDs from database
    ids = get_pokemon_ids_from_db(DB_PATH)
    if not ids:
        print("No Pokemon found in the database. Run the data import first.")
        sys.exit(1)
    print(f"Found {len(ids)} Pokemon in the database (IDs {ids[0]}-{ids[-1]}).\n")

    # 2. Prepare directories
    ensure_directories()

    # 3. Download sprites in parallel
    total_categories = len(SPRITE_SOURCES)
    success_count = 0
    missing_count = 0
    fail_count = 0
    missing_log: list[str] = []

    print(f"Downloading sprites ({total_categories} categories per Pokemon) …\n")

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as pool:
        future_to_id = {
            pool.submit(download_sprites_for_pokemon, pid): pid
            for pid in ids
        }
        done = 0
        for future in as_completed(future_to_id):
            pid = future_to_id[future]
            done += 1
            try:
                results = future.result()
                for cat, ok in results.items():
                    if ok:
                        success_count += 1
                    else:
                        missing_count += 1
                        missing_log.append(f"  ID {pid:>4d} – {cat}")
            except Exception as exc:
                fail_count += total_categories
                missing_log.append(f"  ID {pid:>4d} – ALL (error: {exc})")

            # Progress indicator every 25 Pokemon
            if done % 25 == 0 or done == len(ids):
                pct = done / len(ids) * 100
                print(f"  [{done}/{len(ids)}] {pct:5.1f}% complete")

    # 4. Summary
    total = success_count + missing_count + fail_count
    print(f"\n{'='*40}")
    print(f"  Total files attempted : {total}")
    print(f"  Successfully saved    : {success_count}")
    print(f"  Missing (404)         : {missing_count}")
    print(f"  Failed (error)        : {fail_count}")
    print(f"  Sprites directory     : {os.path.abspath(SPRITES_ROOT)}")
    print(f"{'='*40}")

    if missing_log:
        print("\nMissing / failed sprites:")
        for line in sorted(missing_log):
            print(line)
        print(
            "\nNotes:"
            "\n  • Gen 5 battle animations (anim_*) only exist for IDs 1-649 (Gen 1-5)."
            "\n  • Gen 7 (USUM) sprites cover all gens but have NO back or animated variants."
            "\n  • PokeAPI has NO animated GIFs for Gen 6, 7 or later."
        )

    print("\nDone!")


if __name__ == "__main__":
    main()
