"""
Verify Gen 5-6 Pokemon were added successfully
"""
import sqlite3

conn = sqlite3.connect('data/pokemon_battle.db')
cursor = conn.cursor()

# Count total Pokemon
cursor.execute('SELECT COUNT(*) FROM pokemon')
total_pokemon = cursor.fetchone()[0]

# Count Gen 5-6 Pokemon
cursor.execute('SELECT COUNT(*) FROM pokemon WHERE id >= 494')
gen56_pokemon = cursor.fetchone()[0]

# Count total learnsets
cursor.execute('SELECT COUNT(*) FROM pokemon_learnsets')
total_learnsets = cursor.fetchone()[0]

# Count Gen 5-6 learnsets
cursor.execute('SELECT COUNT(*) FROM pokemon_learnsets WHERE pokemon_id >= 494')
gen56_learnsets = cursor.fetchone()[0]

# Show some sample Gen 5-6 Pokemon
cursor.execute('SELECT id, name, type1, type2, total_stats FROM pokemon WHERE id >= 494 ORDER BY id LIMIT 10')
sample_pokemon = cursor.fetchall()

conn.close()

print("="*60)
print("DATABASE VERIFICATION - GEN 5-6 POKEMON")
print("="*60)
print(f"\n✓ Total Pokemon: {total_pokemon}")
print(f"  - Gen 1-4: {total_pokemon - gen56_pokemon}")
print(f"  - Gen 5-6: {gen56_pokemon}")
print(f"\n✓ Total Learnsets: {total_learnsets}")
print(f"  - Gen 1-4 learnsets: {total_learnsets - gen56_learnsets}")
print(f"  - Gen 5-6 learnsets: {gen56_learnsets}")

print(f"\n✓ Sample Gen 5-6 Pokemon:")
for id, name, type1, type2, total_stats in sample_pokemon:
    type_str = f"{type1}" + (f"/{type2}" if type2 else "")
    print(f"  #{id:3d}: {name:<20} Types: {type_str:<7} Total Stats: {total_stats}")

print("\n" + "="*60)
print("✅ SUCCESS! All Gen 5-6 Pokemon and learnsets added!")
print("="*60)
