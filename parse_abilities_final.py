"""
Parse Pokemon Abilities from habilitats.txt
"""
import re
import sqlite3

def parse_abilities_from_file(filename='habilitats.txt'):
    """Parse abilities with proper structure understanding"""
    with open(filename, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Split by double newlines to get sections
    sections = re.split(r'\n\s*\n', content)
    
    abilities = []
    current_ability = None
    
    for section in sections:
        section = section.strip()
        if not section:
            continue
        
        lines = [l.strip() for l in section.split('\n') if l.strip()]
        
        if not lines:
            continue
        
        # First line that doesn't contain ':' is likely the ability name
        first_line = lines[0]
        
        # Check if this starts a new ability (no colon, likely capitalized)
        if ':' not in first_line and first_line and first_line[0].isupper():
            # Save previous ability
            if current_ability and current_ability['name']:
                abilities.append(current_ability)
            
            # Start new ability
            current_ability = {
                'name': first_line,
                'game_text': '',
                'in_battle_effect': '',
                'overworld_effect': '',
                'pokemon': []
            }
            
            # Process remaining lines in this section
            i = 1
            while i < len(lines):
                line = lines[i]
                
                if line.startswith("Game's Text:"):
                    current_ability['game_text'] = line.replace("Game's Text:", "").strip()
                elif line.startswith("In-Battle Effect:"):
                    current_ability['in_battle_effect'] = line.replace("In-Battle Effect:", "").strip()
                elif line.startswith("Overworld Effect:"):
                    current_ability['overworld_effect'] = line.replace("Overworld Effect:", "").strip()
                elif ':' not in line:
                    # This is likely Pokemon names
                    words = line.split()
                    # Filter out obvious non-Pokemon words
                    pokemon_names = [w for w in words if w and w[0].isupper()]
                    current_ability['pokemon'].extend(pokemon_names)
                
                i += 1
    
    # Don't forget the last ability
    if current_ability and current_ability['name']:
        abilities.append(current_ability)
    
    return abilities

def export_abilities_data():
    """Export abilities to Python file for database insertion"""
    print("Parsing abilities from habilitats.txt...")
    abilities = parse_abilities_from_file()
    
    print(f"Found {len(abilities)} abilities")
    
    # Export to Python file
    with open('abilities_data_export.py', 'w', encoding='utf-8') as f:
        f.write("# Pokemon Abilities Data\n")
        f.write("# Extracted from habilitats.txt\n\n")
        
        f.write("# Format: (name, description, overworld_effect)\n")
        f.write("ABILITIES = [\n")
        for ability in abilities:
            name = ability['name'].replace("'", "''")
            # Use in-battle effect as main description
            desc = ability['in_battle_effect'] or ability['game_text'] or ''
            desc = desc.replace("'", "''").replace('\n', ' ').replace('\r', '')
            overworld = ability['overworld_effect'].replace("'", "''").replace('\n', ' ').replace('\r', '') if ability['overworld_effect'] else None
            
            if overworld:
                f.write(f"    ('{name}', '{desc}', '{overworld}'),\n")
            else:
                f.write(f"    ('{name}', '{desc}', NULL),\n")
        f.write("]\n\n")
        
        # Create Pokemon-Ability mapping
        f.write("# Format: (pokemon_name, ability_name)\n")
        f.write("POKEMON_ABILITIES = [\n")
        for ability in abilities:
            for pokemon_name in ability['pokemon']:
                pname = pokemon_name.replace("'", "''")
                aname = ability['name'].replace("'", "''")
                f.write(f"    ('{pname}', '{aname}'),\n")
        f.write("]\n")
    
    print(f"✓ Exported {len(abilities)} abilities to abilities_data_export.py")
    
    # Show sample
    print("\nSample abilities:")
    for ability in abilities[:5]:
        print(f"\n{ability['name']}")
        print(f"  Effect: {ability['in_battle_effect'][:70]}...")
        print(f"  Pokemon: {', '.join(ability['pokemon'][:5])}{'...' if len(ability['pokemon']) > 5 else ''}")
    
    # Count mappings
    total_mappings = sum(len(a['pokemon']) for a in abilities)
    print(f"\n✓ Total Pokemon-Ability mappings: {total_mappings}")
    
    return abilities

if __name__ == '__main__':
    export_abilities_data()
