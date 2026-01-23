"""
Show complete learnsets for Gen 5-6 Pokemon with move names
"""
import sqlite3
import sys

sys.path.insert(0, 'src')
from pokemon_learnsets_export import POKEMON_LEARNSETS

# Connect to database to get move names
conn = sqlite3.connect('data/pokemon_battle.db')
cursor = conn.cursor()

# Get all moves into a dict
cursor.execute("SELECT id, name FROM moves")
move_names = {row[0]: row[1] for row in cursor.fetchall()}

# Get Pokemon names (if they exist)
cursor.execute("SELECT id, name FROM pokemon")
pokemon_names = {row[0]: row[1] for row in cursor.fetchall()}

conn.close()

# Filter learnsets for Pokemon > 493
gen5_learnsets = [entry for entry in POKEMON_LEARNSETS if entry[0] > 493]

# Group by Pokemon
from collections import defaultdict
learnsets_by_pokemon = defaultdict(list)

for pokemon_id, move_id, learn_method, learn_level, form in gen5_learnsets:
    move_name = move_names.get(move_id, f"UNKNOWN_MOVE_{move_id}")
    learnsets_by_pokemon[pokemon_id].append({
        'level': learn_level,
        'move': move_name,
        'method': learn_method,
        'form': form
    })

# Sort learnsets by level
for pokemon_id in learnsets_by_pokemon:
    learnsets_by_pokemon[pokemon_id].sort(key=lambda x: x['level'])

# Show sample Pokemon (first 5 different Pokemon)
print("=" * 80)
print("SAMPLE LEARNSETS FOR GEN 5-6 POKEMON (Pokemon IDs > 493)")
print("=" * 80)

shown_count = 0
for pokemon_id in sorted(learnsets_by_pokemon.keys())[:10]:
    pokemon_name = pokemon_names.get(pokemon_id, f"UNKNOWN_POKEMON_ID_{pokemon_id}")
    moves = learnsets_by_pokemon[pokemon_id]
    
    print(f"\n{'='*80}")
    print(f"Pokemon ID: {pokemon_id} ({pokemon_name})")
    print(f"Total Moves: {len(moves)}")
    print(f"{'='*80}")
    
    for move_data in moves:
        level = move_data['level']
        move = move_data['move']
        method = move_data['method']
        form = move_data['form']
        
        form_str = f" [Form {form}]" if form != 0 else ""
        print(f"  Level {level:2d}: {move}{form_str}")
    
    shown_count += 1
    if shown_count >= 5:
        break

# Show statistics
print(f"\n{'='*80}")
print("STATISTICS")
print(f"{'='*80}")
print(f"Total Gen 5-6 learnset entries: {len(gen5_learnsets)}")
print(f"Number of Gen 5-6 Pokemon with learnsets: {len(learnsets_by_pokemon)}")
print(f"Pokemon ID range: {min(learnsets_by_pokemon.keys())} to {max(learnsets_by_pokemon.keys())}")

# Check for unknown moves
unknown_moves = set()
for entry in gen5_learnsets:
    if entry[1] not in move_names:
        unknown_moves.add(entry[1])

if unknown_moves:
    print(f"\n⚠️  WARNING: Found {len(unknown_moves)} move IDs that don't exist in your database:")
    print(f"   Move IDs: {sorted(unknown_moves)[:20]}...")
else:
    print(f"\n✓ All move IDs in learnsets exist in your moves table")

print(f"\n{'='*80}")
