"""
Fetch Gen 5-6 Pokemon data from PokeAPI and export to Python file
"""
import requests
import time
import json

def fetch_pokemon_data(pokemon_id):
    """Fetch Pokemon data from PokeAPI"""
    url = f"https://pokeapi.co/api/v2/pokemon/{pokemon_id}"
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            return response.json()
        return None
    except Exception as e:
        print(f"Error fetching Pokemon {pokemon_id}: {e}")
        return None

def get_type_id(type_name):
    """Map type names to database IDs"""
    type_mapping = {
        'normal': 1, 'fighting': 2, 'flying': 3, 'poison': 4,
        'ground': 5, 'rock': 6, 'bug': 7, 'ghost': 8,
        'steel': 9, 'fire': 10, 'water': 11, 'grass': 12,
        'electric': 13, 'psychic': 14, 'ice': 15, 'dragon': 16,
        'dark': 17, 'fairy': 18
    }
    return type_mapping.get(type_name.lower(), 1)

def get_exp_curve(species_data):
    """Get experience curve from species data"""
    curve_mapping = {
        'slow': 'slow',
        'medium': 'medium-fast',
        'fast': 'fast',
        'medium-slow': 'medium-slow',
        'slow-then-very-fast': 'erratic',
        'fast-then-very-slow': 'fluctuating'
    }
    growth_rate = species_data.get('growth_rate', {}).get('name', 'medium')
    return curve_mapping.get(growth_rate, 'medium-fast')

def get_evolution_data(species_data):
    """Extract evolution data from species"""
    evolution_level = None
    evolves_to_id = None
    
    evolution_chain_url = species_data.get('evolution_chain', {}).get('url')
    if evolution_chain_url:
        try:
            response = requests.get(evolution_chain_url, timeout=10)
            if response.status_code == 200:
                chain_data = response.json()
                # This is complex - for now we'll leave it None
                # and keep the existing evolution data
        except:
            pass
    
    return evolution_level, evolves_to_id

# Fetch Gen 5-6 Pokemon (IDs 494-721)
print("Fetching Gen 5-6 Pokemon data from PokeAPI...")
print("This will take a few minutes...")

pokemon_data = []
failed_ids = []

for pokemon_id in range(494, 722):  # 494 to 721
    print(f"Fetching Pokemon #{pokemon_id}...", end=" ")
    
    # Get Pokemon data
    poke_data = fetch_pokemon_data(pokemon_id)
    if not poke_data:
        print("FAILED")
        failed_ids.append(pokemon_id)
        continue
    
    # Get species data for evolution info
    species_url = poke_data.get('species', {}).get('url')
    species_data = {}
    if species_url:
        try:
            response = requests.get(species_url, timeout=10)
            if response.status_code == 200:
                species_data = response.json()
        except:
            pass
    
    # Extract stats
    stats = {stat['stat']['name']: stat['base_stat'] for stat in poke_data['stats']}
    
    # Extract types
    types = [t['type']['name'] for t in poke_data['types']]
    type1 = get_type_id(types[0]) if len(types) > 0 else 1
    type2 = get_type_id(types[1]) if len(types) > 1 else None
    
    # Get exp curve
    exp_curve = get_exp_curve(species_data)
    
    # Calculate total stats
    total_stats = sum([
        stats.get('hp', 0),
        stats.get('attack', 0),
        stats.get('defense', 0),
        stats.get('special-attack', 0),
        stats.get('special-defense', 0),
        stats.get('speed', 0)
    ])
    
    # Create Pokemon entry
    pokemon_entry = (
        pokemon_id,
        poke_data['name'].capitalize(),
        type1,
        type2,
        stats.get('hp', 0),
        stats.get('attack', 0),
        stats.get('defense', 0),
        stats.get('special-attack', 0),
        stats.get('special-defense', 0),
        stats.get('speed', 0),
        total_stats,
        None,  # evolution_level - keep existing
        exp_curve,
        None   # evolves_to_id - keep existing
    )
    
    pokemon_data.append(pokemon_entry)
    print(f"✓ {poke_data['name']}")
    
    # Rate limiting - be nice to the API
    time.sleep(0.5)

# Save to Python file
with open('src/gen5_6_pokemon_export.py', 'w', encoding='utf-8') as f:
    f.write('"""\n')
    f.write('Gen 5-6 Pokemon data (IDs 494-721)\n')
    f.write('Fetched from PokeAPI\n')
    f.write('"""\n\n')
    f.write('GEN5_6_POKEMON = [\n')
    for pokemon in pokemon_data:
        f.write(f'    {pokemon},\n')
    f.write(']\n')

print(f"\n✓ Successfully fetched {len(pokemon_data)} Pokemon")
if failed_ids:
    print(f"⚠ Failed to fetch: {failed_ids}")
print(f"✓ Data saved to: src/gen5_6_pokemon_export.py")
