"""
Parse abilities from habilitats.txt and prepare for database insertion
"""
import re

def parse_abilities_file(filename):
    """Parse the abilities text file and extract structured data"""
    with open(filename, 'r', encoding='utf-8') as f:
        content = f.read()
    
    abilities = []
    
    # Split by ability names (lines that are not indented and followed by info)
    # We'll use a different approach - split by blank lines and process sections
    sections = content.split('\n\n')
    
    current_ability = None
    
    for section in sections:
        section = section.strip()
        if not section:
            continue
            
        lines = section.split('\n')
        first_line = lines[0].strip()
        
        # Check if this looks like an ability name (not starting with special chars)
        if first_line and not first_line.startswith(('In-Battle', 'Game\'s', 'Overworld')):
            # This is likely an ability name
            if current_ability:
                abilities.append(current_ability)
            
            current_ability = {
                'name': first_line,
                'game_text': None,
                'in_battle_effect': None,
                'overworld_effect': None,
                'pokemon': []
            }
        
        # Extract effects
        if 'Game\'s Text:' in section:
            match = re.search(r'Game\'s Text:\s*(.+?)(?:\nIn-Battle Effect:|$)', section, re.DOTALL)
            if match and current_ability:
                current_ability['game_text'] = match.group(1).strip()
        
        if 'In-Battle Effect:' in section:
            match = re.search(r'In-Battle Effect:\s*(.+?)(?:\nOverworld Effect:|$)', section, re.DOTALL)
            if match and current_ability:
                current_ability['in_battle_effect'] = match.group(1).strip()
        
        if 'Overworld Effect:' in section:
            match = re.search(r'Overworld Effect:\s*(.+?)$', section, re.DOTALL)
            if match and current_ability:
                current_ability['overworld_effect'] = match.group(1).strip()
        
        # Check if this section has Pokemon names
        # Pokemon names are usually at the end after the effects
        for line in lines:
            line = line.strip()
            # Skip lines with colons (they're labels)
            if ':' in line or not line:
                continue
            # If line doesn't start with known keywords, it might be Pokemon
            if not any(keyword in line for keyword in ['Game\'s Text', 'In-Battle Effect', 'Overworld Effect']):
                # This line might contain Pokemon names
                pokemon_names = [p.strip() for p in line.split() if p.strip()]
                if pokemon_names and current_ability:
                    current_ability['pokemon'].extend(pokemon_names)
    
    # Add the last ability
    if current_ability:
        abilities.append(current_ability)
    
    return abilities

def clean_ability_data(abilities):
    """Clean and structure the ability data"""
    cleaned = []
    
    for ability in abilities:
        # Combine game_text and in_battle_effect for description
        description = ability['in_battle_effect'] or ability['game_text'] or ''
        
        # Skip empty abilities
        if not ability['name']:
            continue
        
        cleaned.append({
            'name': ability['name'],
            'description': description,
            'overworld_effect': ability['overworld_effect'],
            'pokemon': list(set(ability['pokemon']))  # Remove duplicates
        })
    
    return cleaned

def main():
    print("Parsing abilities from habilitats.txt...")
    abilities = parse_abilities_file('habilitats.txt')
    
    print(f"\nFound {len(abilities)} abilities\n")
    
    # Clean the data
    cleaned_abilities = clean_ability_data(abilities)
    
    # Display sample
    for i, ability in enumerate(cleaned_abilities[:5], 1):
        print(f"{i}. {ability['name']}")
        print(f"   Description: {ability['description'][:80]}...")
        print(f"   Pokemon: {', '.join(ability['pokemon'][:5])}{'...' if len(ability['pokemon']) > 5 else ''}")
        print()
    
    # Export to Python file
    with open('abilities_export.py', 'w', encoding='utf-8') as f:
        f.write("# Pokemon Abilities Data\n")
        f.write("# Format: (name, description, overworld_effect)\n\n")
        f.write("ABILITIES = [\n")
        for ability in cleaned_abilities:
            name = ability['name'].replace("'", "\\'")
            desc = (ability['description'] or '').replace("'", "\\'").replace('\n', ' ')
            overworld = (ability['overworld_effect'] or '').replace("'", "\\'").replace('\n', ' ')
            overworld_str = 'NULL' if not overworld else f"'{overworld}'"
            f.write(f"    ('{name}', '{desc}', {overworld_str}),\n")
        f.write("]\n\n")
        
        f.write("# Pokemon to Abilities mapping\n")
        f.write("# Format: (pokemon_name, ability_name)\n")
        f.write("POKEMON_ABILITIES = [\n")
        for ability in cleaned_abilities:
            for pokemon_name in ability['pokemon']:
                pname = pokemon_name.replace("'", "\\'")
                aname = ability['name'].replace("'", "\\'")
                f.write(f"    ('{pname}', '{aname}'),\n")
        f.write("]\n")
    
    print(f"\n✓ Exported {len(cleaned_abilities)} abilities to abilities_export.py")
    
    # Count Pokemon-Ability mappings
    total_mappings = sum(len(a['pokemon']) for a in cleaned_abilities)
    print(f"✓ Exported {total_mappings} pokemon-ability mappings")

if __name__ == '__main__':
    main()
