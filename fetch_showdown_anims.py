"""
Download animated battle sprites from Pokemon Showdown.

Source URLs:
    https://play.pokemonshowdown.com/sprites/xyani/{name}.gif          (front)
    https://play.pokemonshowdown.com/sprites/xyani-back/{name}.gif     (back)
    https://play.pokemonshowdown.com/sprites/xyani-shiny/{name}.gif    (front shiny)
    https://play.pokemonshowdown.com/sprites/xyani-back-shiny/{name}.gif (back shiny)

Pokemon are looked up by name from the local DB and saved as {id}.gif.
Files already present are skipped (resume-safe).

Output:
    data/sprites/showdown/front/       {id}.gif
    data/sprites/showdown/back/        {id}.gif
    data/sprites/showdown/front-shiny/ {id}.gif
    data/sprites/showdown/back-shiny/  {id}.gif
"""

import os
import re
import sys
import time
import sqlite3
import requests
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------
DB_PATH     = "data/pokemon_battle.db"
OUT_ROOT    = "data/sprites/showdown"
MAX_WORKERS = 12
MAX_RETRIES = 3
RETRY_DELAY = 1  # seconds

SD_BASE     = "https://play.pokemonshowdown.com/sprites"
CATEGORIES  = {
    "front":       f"{SD_BASE}/xyani",
    "back":        f"{SD_BASE}/xyani-back",
    "front-shiny": f"{SD_BASE}/xyani-shiny",
    "back-shiny":  f"{SD_BASE}/xyani-back-shiny",
}

# ---------------------------------------------------------------------------
# Name → Showdown ID conversion  (mirrors Showdown's toID() function)
# Rule: lowercase + remove everything that is not [a-z0-9]
#       gender symbols are mapped to 'f' / 'm' before stripping
# ---------------------------------------------------------------------------
def to_showdown_id(name: str) -> str:
    name = name.replace("\u2640", "f").replace("\u2642", "m")   # ♀ → f, ♂ → m
    return re.sub(r"[^a-z0-9]", "", name.lower())


# Form-suffix words that Showdown omits in the default sprite filename.
# If the direct URL returns 404 we strip these suffixes and try the base name.
_FORM_SUFFIXES = re.compile(
    r"(incarnate|standard|ordinary|aria|male|average|"
    r"redstriped|50|land|normal|altered|overcast|plant|"
    r"shield|blade|therian|black|white|resolute|pirouette|"
    r"burn|chill|douse|shock|pau|baile|sensu|pomme|"
    r"east|west|spring|summer|autumn|winter|"
    r"heat|wash|frost|fan|mow|sandy|trash|active|neutral)$"
)

def fallback_showdown_id(sid: str) -> str | None:
    """Return a simpler ID to try if the primary lookup 404s."""
    stripped = _FORM_SUFFIXES.sub("", sid)
    return stripped if stripped != sid else None


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def ensure_dirs() -> None:
    for cat in CATEGORIES:
        Path(OUT_ROOT, cat).mkdir(parents=True, exist_ok=True)


def get_pokemon(db_path: str) -> list[tuple[int, str]]:
    if not os.path.exists(db_path):
        print(f"ERROR: database not found at '{db_path}'")
        sys.exit(1)
    conn = sqlite3.connect(db_path)
    rows = conn.execute("SELECT id, name FROM pokemon ORDER BY id").fetchall()
    conn.close()
    return rows


def download(url: str, dest: str, retries: int = MAX_RETRIES) -> bool:
    for attempt in range(1, retries + 1):
        try:
            resp = requests.get(url, timeout=15)
            if resp.status_code == 200:
                Path(dest).write_bytes(resp.content)
                return True
            if resp.status_code == 404:
                return False
            time.sleep(RETRY_DELAY * attempt)
        except requests.RequestException:
            time.sleep(RETRY_DELAY * attempt)
    return False


# ---------------------------------------------------------------------------
# Per-Pokemon download logic
# ---------------------------------------------------------------------------
def process_pokemon(pokemon_id: int, name: str) -> dict:
    """Download all categories for one Pokemon. Returns {category: True/False}."""
    sid      = to_showdown_id(name)
    fallback = fallback_showdown_id(sid)
    results  = {}

    for cat, base_url in CATEGORIES.items():
        dest = os.path.join(OUT_ROOT, cat, f"{pokemon_id}.gif")
        if os.path.exists(dest):
            results[cat] = True
            continue

        # Primary attempt
        ok = download(f"{base_url}/{sid}.gif", dest)

        # Fallback: try base name (e.g. "darmanitan" instead of "darmanitanstandard")
        if not ok and fallback:
            ok = download(f"{base_url}/{fallback}.gif", dest)

        results[cat] = ok

    return results


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main() -> None:
    print("=== Pokemon Showdown Animated Sprite Downloader ===\n")

    pokemon = get_pokemon(DB_PATH)
    if not pokemon:
        print("No Pokemon in the database.")
        sys.exit(1)

    print(f"Found {len(pokemon)} Pokemon (IDs {pokemon[0][0]}-{pokemon[-1][0]}).\n")
    ensure_dirs()

    total_cats = len(CATEGORIES)
    ok_count   = 0
    miss_count = 0
    miss_log   = []

    print(f"Downloading {total_cats} sprite variants per Pokemon …\n")

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as pool:
        futures = {pool.submit(process_pokemon, pid, name): (pid, name)
                   for pid, name in pokemon}
        done = 0
        for future in as_completed(futures):
            pid, name = futures[future]
            done += 1
            try:
                results = future.result()
                for cat, ok in results.items():
                    if ok:
                        ok_count += 1
                    else:
                        miss_count += 1
                        sid = to_showdown_id(name)
                        miss_log.append(f"  ID {pid:>4d} ({sid:<25}) – {cat}")
            except Exception as exc:
                miss_count += total_cats
                miss_log.append(f"  ID {pid:>4d} ({name}) – ALL (error: {exc})")

            if done % 50 == 0 or done == len(pokemon):
                pct = done / len(pokemon) * 100
                print(f"  [{done}/{len(pokemon)}] {pct:5.1f}% complete")

    total = ok_count + miss_count
    print(f"\n{'='*45}")
    print(f"  Total attempted  : {total}")
    print(f"  Saved            : {ok_count}")
    print(f"  Missing (no GIF) : {miss_count}")
    print(f"  Output directory : {os.path.abspath(OUT_ROOT)}")
    print(f"{'='*45}")

    if miss_log:
        print("\nMissing sprites:")
        for line in sorted(miss_log):
            print(line)
        print(
            "\nNote: Showdown only hosts XY-era (Gen 6) animated GIFs."
            "\nSome Gen 6+ Pokemon or rare forms may have no sprite."
        )

    print("\nDone!")


if __name__ == "__main__":
    main()
