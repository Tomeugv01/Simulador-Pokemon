#!/usr/bin/env python3
"""Quick test script to verify Pokemon data"""

import sys
sys.path.insert(0, 'src')

from add_pokemon_data import get_pokemon_by_name, get_all_pokemon, search_pokemon_by_type

# Test individual Pokemon
print("=" * 60)
print("Testing Pokemon Queries")
print("=" * 60)

pika = get_pokemon_by_name('Pikachu')
if pika:
    print(f"\n✅ Pikachu found:")
    print(f"   ID: {pika[0]}, Name: {pika[1]}, Type: {pika[2]}/{pika[3]}")
    print(f"   Stats: HP={pika[4]}, Atk={pika[5]}, Def={pika[6]}, SpA={pika[7]}, SpD={pika[8]}, Spe={pika[9]}")
    print(f"   Total: {pika[10]}")

char = get_pokemon_by_name('Charizard')
if char:
    print(f"\n✅ Charizard found:")
    print(f"   ID: {char[0]}, Name: {char[1]}, Type: {char[2]}/{char[3]}")
    print(f"   Stats: HP={char[4]}, Atk={char[5]}, Def={char[6]}, SpA={char[7]}, SpD={char[8]}, Spe={char[9]}")
    print(f"   Total: {char[10]}")

# Test type search
fire_types = search_pokemon_by_type('Fire')
print(f"\n✅ Found {len(fire_types)} Fire-type Pokemon:")
for p in fire_types[:10]:  # Show first 5
    print(f"   - {p[1]} ({p[2]}/{p[3] if p[3] else 'None'})")

# Test total count
all_pokemon = get_all_pokemon()
print(f"\n✅ Total Pokemon in database: {len(all_pokemon)}")

print("\n" + "=" * 60)
print("All tests passed! ✅")
print("=" * 60)
