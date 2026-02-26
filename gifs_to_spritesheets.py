"""
Convert Pokemon Showdown animated GIFs to spritesheets for use in Java Swing.

For each GIF in data/sprites/showdown/<category>/
  → produces data/sprites/showdown-sheets/<category>/{id}.png  (horizontal spritesheet)
  → produces data/sprites/showdown-sheets/<category>/{id}.json (metadata)

Original GIFs are never touched.

JSON format:
{
    "id":           25,
    "frame_count":  8,
    "frame_width":  96,
    "frame_height": 96,
    "sheet_width":  768,     // frame_width * frame_count
    "sheet_height": 96,
    "delays":       [100, 100, 100, ...]   // ms per frame
}

Java usage sketch:
    BufferedImage sheet = ImageIO.read(new File("25.png"));
    // frame N  →  sheet.getSubimage(N * frameWidth, 0, frameWidth, frameHeight)
"""

import os
import sys
import json
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from PIL import Image

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------
GIF_ROOT   = "data/sprites/showdown"
SHEET_ROOT = "data/sprites/showdown-sheets"
CATEGORIES = ["front", "back", "front-shiny", "back-shiny"]
MAX_WORKERS = 8


# ---------------------------------------------------------------------------
# GIF → composited RGBA frames
# ---------------------------------------------------------------------------
def extract_frames(gif_path: str) -> tuple[list[Image.Image], list[int]]:
    """
    Return (frames, delays_ms).
    Pillow composites sub-frames automatically when you seek+convert, so
    calling .convert('RGBA') at each position gives correctly rendered frames.
    """
    gif = Image.open(gif_path)
    frames: list[Image.Image] = []
    delays: list[int] = []

    frame_idx = 0
    while True:
        try:
            gif.seek(frame_idx)
        except EOFError:
            break

        delay = gif.info.get("duration", 100)
        delays.append(max(10, int(delay)))
        frames.append(gif.convert("RGBA").copy())
        frame_idx += 1

    return frames, delays


# ---------------------------------------------------------------------------
# Build horizontal spritesheet
# ---------------------------------------------------------------------------
def build_spritesheet(frames: list[Image.Image]) -> tuple[Image.Image, int, int]:
    w = max(f.width  for f in frames)
    h = max(f.height for f in frames)
    sheet = Image.new("RGBA", (w * len(frames), h), (0, 0, 0, 0))
    for i, frame in enumerate(frames):
        x_off = (w - frame.width)  // 2
        y_off = (h - frame.height) // 2
        sheet.paste(frame, (i * w + x_off, y_off), frame)
    return sheet, w, h


# ---------------------------------------------------------------------------
# Convert a single GIF file
# ---------------------------------------------------------------------------
def convert_gif(gif_path: Path, out_png: Path, out_json: Path, pokemon_id: int) -> bool:
    try:
        frames, delays = extract_frames(str(gif_path))
        if not frames:
            return False

        sheet, fw, fh = build_spritesheet(frames)
        sheet.save(str(out_png), "PNG", optimize=False)

        meta = {
            "id":           pokemon_id,
            "frame_count":  len(frames),
            "frame_width":  fw,
            "frame_height": fh,
            "sheet_width":  fw * len(frames),
            "sheet_height": fh,
            "delays":       delays,
        }
        out_json.write_text(json.dumps(meta, indent=2))
        return True

    except Exception as exc:
        print(f"  ERROR {gif_path.name}: {exc}", file=sys.stderr)
        return False


# ---------------------------------------------------------------------------
# Process one category with a thread pool
# ---------------------------------------------------------------------------
def process_category(category: str) -> tuple[int, int, int]:
    gif_dir   = Path(GIF_ROOT)   / category
    sheet_dir = Path(SHEET_ROOT) / category
    sheet_dir.mkdir(parents=True, exist_ok=True)

    gifs = sorted(gif_dir.glob("*.gif"), key=lambda p: int(p.stem))
    if not gifs:
        return 0, 0, 0

    todo = []
    skip = 0
    for gif_path in gifs:
        pid      = int(gif_path.stem)
        out_png  = sheet_dir / f"{pid}.png"
        out_json = sheet_dir / f"{pid}.json"
        if out_png.exists() and out_json.exists():
            skip += 1
        else:
            todo.append((gif_path, out_png, out_json, pid))

    ok = fail = 0
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as pool:
        futures = {
            pool.submit(convert_gif, gif, png, jso, pid): pid
            for gif, png, jso, pid in todo
        }
        for future in as_completed(futures):
            if future.result():
                ok += 1
            else:
                fail += 1

    return ok, skip, fail


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main() -> None:
    print("=== GIF → Spritesheet Converter ===\n")

    total_ok = total_skip = total_fail = 0

    for category in CATEGORIES:
        ok, skip, fail = process_category(category)
        print(f"[{category:12s}]  converted: {ok:4d}  |  skipped: {skip:4d}  |  failed: {fail:4d}")
        total_ok   += ok
        total_skip += skip
        total_fail += fail

    print(f"\n{'='*45}")
    print(f"  Converted : {total_ok}")
    print(f"  Skipped   : {total_skip}  (already existed)")
    print(f"  Failed    : {total_fail}")
    print(f"  Output    : {os.path.abspath(SHEET_ROOT)}")
    print(f"{'='*45}")
    print("\nOriginal GIFs were not modified.")
    print("Done!")


if __name__ == "__main__":
    main()

if __name__ == "__main__":
    main()
