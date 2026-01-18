import json
import sqlite3

# Load evolution data
with open('evolution_data.json', 'r') as f:
    data = json.load(f)

# Find Pokemon with multiple evolutions
from collections import defaultdict
multi_evos = defaultdict(list)

for evo in data['evolutions']:
    pokemon_id = evo['pokemon_id']
    multi_evos[pokemon_id].append(evo)

# Print Pokemon with multiple evolutions
print("Pokemon with multiple evolution paths:")
print("=" * 60)
for pokemon_id, evos in multi_evos.items():
    if len(evos) > 1:
        print(f"\n{evos[0]['pokemon_name']} (ID {pokemon_id}) - {len(evos)} evolutions:")
        for evo in evos:
            print(f"  → {evo['evolves_to_name']} (ID {evo['evolves_to_id']}) at level {evo['evolution_level']}")
