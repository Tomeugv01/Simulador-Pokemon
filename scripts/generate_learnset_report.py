"""
Generate detailed report of Gen 5-6 Pokemon learnsets
"""
import sqlite3
import sys

sys.path.insert(0, 'src')
from pokemon_learnsets_export import POKEMON_LEARNSETS

# Known Gen 5-6 Pokemon (you can verify these)
GEN5_6_POKEMON = {
    494: "Victini",
    495: "Snivy", 496: "Servine", 497: "Serperior",
    498: "Tepig", 499: "Pignite", 500: "Emboar",
    501: "Oshawott", 502: "Dewott", 503: "Samurott",
    504: "Patrat", 505: "Watchog",
    506: "Lillipup", 507: "Herdier", 508: "Stoutland",
    509: "Purrloin", 510: "Liepard",
    511: "Pansage", 512: "Simisage",
    513: "Pansear", 514: "Simisear",
    515: "Panpour", 516: "Simipour",
    # ... more would go here
}

# Get move names from database
conn = sqlite3.connect('data/pokemon_battle.db')
cursor = conn.cursor()
cursor.execute("SELECT id, name FROM moves")
move_names = {row[0]: row[1] for row in cursor.fetchall()}
conn.close()

# Group learnsets by Pokemon
from collections import defaultdict
learnsets_by_pokemon = defaultdict(list)

for pokemon_id, move_id, learn_method, learn_level, form in POKEMON_LEARNSETS:
    if pokemon_id > 493:
        move_name = move_names.get(move_id, f"UNKNOWN_MOVE_{move_id}")
        learnsets_by_pokemon[pokemon_id].append({
            'level': learn_level,
            'move': move_name,
            'move_id': move_id,
            'method': learn_method,
            'form': form
        })

# Sort by level
for pokemon_id in learnsets_by_pokemon:
    learnsets_by_pokemon[pokemon_id].sort(key=lambda x: x['level'])

# Write to file
with open('gen5_6_learnsets_sample.txt', 'w', encoding='utf-8') as f:
    f.write("="*80 + "\n")
    f.write("GEN 5-6 POKEMON LEARNSETS SAMPLE\n")
    f.write("Source: pokemon_learnsets_export.py (from your original database)\n")
    f.write("="*80 + "\n\n")
    
    # Show first 15 Pokemon in detail
    for pokemon_id in sorted(learnsets_by_pokemon.keys())[:15]:
        pokemon_name = GEN5_6_POKEMON.get(pokemon_id, f"Unknown Pokemon ID {pokemon_id}")
        moves = learnsets_by_pokemon[pokemon_id]
        
        f.write("\n" + "="*80 + "\n")
        f.write(f"Pokemon #{pokemon_id}: {pokemon_name}\n")
        f.write(f"Total Moves: {len(moves)}\n")
        f.write("="*80 + "\n")
        
        for move_data in moves:
            level = move_data['level']
            move = move_data['move']
            move_id = move_data['move_id']
            form = move_data['form']
            
            form_str = f" [Form {form}]" if form != 0 else ""
            f.write(f"  Lv {level:2d}: {move:<20} (Move ID: {move_id}){form_str}\n")
    
    # Summary statistics
    f.write("\n\n" + "="*80 + "\n")
    f.write("SUMMARY STATISTICS\n")
    f.write("="*80 + "\n")
    f.write(f"Total Gen 5-6 Pokemon with learnsets: {len(learnsets_by_pokemon)}\n")
    f.write(f"Total learnset entries: {sum(len(v) for v in learnsets_by_pokemon.values())}\n")
    f.write(f"Pokemon ID range: {min(learnsets_by_pokemon.keys())} to {max(learnsets_by_pokemon.keys())}\n")
    f.write(f"\nAverage moves per Pokemon: {sum(len(v) for v in learnsets_by_pokemon.values()) / len(learnsets_by_pokemon):.1f}\n")
    
    # List all Gen 5-6 Pokemon IDs
    f.write("\n\nComplete list of Gen 5-6 Pokemon IDs in learnsets:\n")
    all_ids = sorted(learnsets_by_pokemon.keys())
    for i in range(0, len(all_ids), 10):
        chunk = all_ids[i:i+10]
        f.write("  " + ", ".join(str(x) for x in chunk) + "\n")

print("✓ Generated detailed report: gen5_6_learnsets_sample.txt")
print(f"  - Shows first 15 Pokemon in detail")
print(f"  - Total of {len(learnsets_by_pokemon)} Gen 5-6 Pokemon")
print(f"  - {sum(len(v) for v in learnsets_by_pokemon.values())} total move entries")
