"""
Fetch complete ability data from PokeAPI and generate export files.
Generates:
  - abilities_data_export.py  (ABILITIES list)
  - pokemon_abilities_export.py  (POKEMON_ABILITIES list)
"""
import json
import time
import sqlite3
import os
import sys

try:
    import urllib.request
    HAS_URLLIB = True
except ImportError:
    HAS_URLLIB = False

DB_PATH = os.path.join(os.path.dirname(__file__), 'data', 'pokemon_battle.db')
MAX_POKEMON_ID = 721  # Gen 1-6

def fetch_json(url, retries=3):
    """Fetch JSON from URL with retries."""
    for attempt in range(retries):
        try:
            req = urllib.request.Request(url, headers={'User-Agent': 'Pokemon-Simulator/1.0'})
            with urllib.request.urlopen(req, timeout=30) as resp:
                return json.loads(resp.read().decode('utf-8'))
        except Exception as e:
            if attempt < retries - 1:
                print(f"  Retry {attempt+1} for {url}: {e}")
                time.sleep(1)
            else:
                print(f"  FAILED to fetch {url}: {e}")
                return None

def get_db_pokemon_names():
    """Get pokemon_id -> name mapping from DB."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT id, name FROM pokemon WHERE id <= ?", (MAX_POKEMON_ID,))
    result = {row[0]: row[1] for row in cursor.fetchall()}
    conn.close()
    return result

def fetch_all_abilities():
    """Fetch all abilities from PokeAPI."""
    print("Fetching ability list...")
    # Get total count first
    data = fetch_json("https://pokeapi.co/api/v2/ability?limit=1")
    if not data:
        return None
    total = data['count']
    print(f"Total abilities in API: {total}")
    
    # Fetch all ability names/URLs
    data = fetch_json(f"https://pokeapi.co/api/v2/ability?limit={total}")
    if not data:
        return None
    
    abilities = []
    for i, item in enumerate(data['results']):
        ability_url = item['url']
        ability_id = int(ability_url.rstrip('/').split('/')[-1])
        
        # Only fetch abilities up to a reasonable ID (Gen 1-6 abilities are IDs 1-191ish)
        # But also include any that have Gen 1-6 pokemon
        if ability_id > 300:
            continue
            
        print(f"  Fetching ability {i+1}/{len(data['results'])}: {item['name']} (ID {ability_id})...")
        detail = fetch_json(ability_url)
        if not detail:
            continue
        
        # Get English effect text
        effect = None
        for entry in detail.get('effect_entries', []):
            if entry['language']['name'] == 'en':
                effect = entry.get('short_effect') or entry.get('effect', '')
                break
        
        # Get English flavor text (fallback)
        flavor = None
        for entry in detail.get('flavor_text_entries', []):
            if entry['language']['name'] == 'en':
                flavor = entry['flavor_text'].replace('\n', ' ').strip()
                break
        
        # Get pokemon with this ability
        pokemon_list = []
        for pokemon_entry in detail.get('pokemon', []):
            pokemon_url = pokemon_entry['pokemon']['url']
            pokemon_id = int(pokemon_url.rstrip('/').split('/')[-1])
            if pokemon_id <= MAX_POKEMON_ID:
                is_hidden = pokemon_entry.get('is_hidden', False)
                slot = pokemon_entry.get('slot', 1)
                pokemon_list.append({
                    'id': pokemon_id,
                    'name': pokemon_entry['pokemon']['name'],
                    'is_hidden': is_hidden,
                    'slot': slot
                })
        
        # Only include if it has Gen 1-6 pokemon OR is a Gen 1-6 ability (ID <= 191)
        if pokemon_list or ability_id <= 191:
            # Clean up the name
            name = detail['name']  # slug form like "speed-boost"
            # Convert to display name
            display_name = ' '.join(word.capitalize() for word in name.split('-'))
            
            abilities.append({
                'id': ability_id,
                'slug': name,
                'name': display_name,
                'effect': effect or flavor or '',
                'pokemon': pokemon_list
            })
        
        # Be polite to the API
        time.sleep(0.15)
    
    return abilities

def generate_abilities_export(abilities):
    """Generate abilities_data_export.py."""
    lines = [
        '# Pokemon Abilities Data',
        '# Auto-generated from PokeAPI',
        '# Format: (id, name, description, overworld_effect)',
        '',
        'ABILITIES = ['
    ]
    
    for ability in sorted(abilities, key=lambda a: a['id']):
        desc = ability['effect'].replace("'", "\\'").replace('"', '\\"')
        name = ability['name'].replace("'", "\\'")
        lines.append(f"    ({ability['id']}, '{name}', '{desc}', None),")
    
    lines.append(']')
    lines.append('')
    
    filepath = os.path.join(os.path.dirname(__file__), 'abilities_data_export.py')
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))
    print(f"Wrote {filepath} with {len(abilities)} abilities")

def generate_pokemon_abilities_export(abilities):
    """Generate pokemon_abilities_export.py."""
    lines = [
        '# Pokemon-Ability Relations Data',
        '# Auto-generated from PokeAPI',
        '# Format: (pokemon_id, ability_id, is_hidden, slot)',
        '',
        'POKEMON_ABILITIES = ['
    ]
    
    relations = []
    for ability in abilities:
        for pokemon in ability['pokemon']:
            relations.append((pokemon['id'], ability['id'], pokemon['is_hidden'], pokemon['slot']))
    
    # Sort by pokemon_id, then slot
    relations.sort(key=lambda r: (r[0], r[3]))
    
    for pid, aid, hidden, slot in relations:
        lines.append(f"    ({pid}, {aid}, {hidden}, {slot}),")
    
    lines.append(']')
    lines.append('')
    
    filepath = os.path.join(os.path.dirname(__file__), 'pokemon_abilities_export.py')
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))
    print(f"Wrote {filepath} with {len(relations)} pokemon-ability relations")

def main():
    if not HAS_URLLIB:
        print("ERROR: urllib not available")
        sys.exit(1)
    
    # Check DB exists
    if not os.path.exists(DB_PATH):
        print(f"ERROR: Database not found at {DB_PATH}")
        sys.exit(1)
    
    pokemon_names = get_db_pokemon_names()
    print(f"Found {len(pokemon_names)} Pokemon in DB (IDs 1-{MAX_POKEMON_ID})")
    
    # Fetch from PokeAPI
    abilities = fetch_all_abilities()
    if not abilities:
        print("ERROR: Failed to fetch abilities from PokeAPI")
        sys.exit(1)
    
    print(f"\nFetched {len(abilities)} abilities with Gen 1-6 Pokemon")
    
    # Generate export files
    generate_abilities_export(abilities)
    generate_pokemon_abilities_export(abilities)
    
    # Also save raw JSON for reference
    json_path = os.path.join(os.path.dirname(__file__), 'abilities_raw.json')
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(abilities, f, indent=2)
    print(f"Saved raw JSON to {json_path}")
    
    print("\nDone! Now run 'python src/run.py' to rebuild the database.")

if __name__ == '__main__':
    main()
