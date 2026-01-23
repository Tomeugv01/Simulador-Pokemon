"""
Better parser for abilities from habilitats.txt
"""
import re

def parse_abilities_manual():
    """Manually parse the abilities file with better logic"""
    with open('habilitats.txt', 'r', encoding='utf-8') as f:
        content = f.read()
    
    abilities = []
    lines = content.split('\n')
    
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        
        # Skip empty lines
        if not line:
            i += 1
            continue
        
        # Check if this is an ability name (no colon, not starting with effect keywords)
        if ':' not in line and not any(keyword in line for keyword in ['In-Battle', 'Game\'s', 'Overworld']):
            # This might be an ability name
            ability_name = line
            game_text = None
            in_battle_effect = None
            overworld_effect = None
            pokemon_list = []
            
            # Look ahead for effects and Pokemon
            i += 1
            while i < len(lines):
                next_line = lines[i].strip()
                
                # Empty line might signal end of this ability
                if not next_line:
                    i += 1
                    continue
                
                # Check for Game's Text
                if next_line.startswith("Game's Text:"):
                    game_text = next_line.replace("Game's Text:", "").strip()
                    i += 1
                    continue
                
                # Check for In-Battle Effect
                if next_line.startswith("In-Battle Effect:"):
                    in_battle_effect = next_line.replace("In-Battle Effect:", "").strip()
                    i += 1
                    continue
                
                # Check for Overworld Effect
                if next_line.startswith("Overworld Effect:"):
                    overworld_effect = next_line.replace("Overworld Effect:", "").strip()
                    # Continue reading overworld effect lines
                    i += 1
                    while i < len(lines) and lines[i].strip() and ':' not in lines[i] and not any(c.isupper() and c.isalpha() for c in lines[i][:3]):
                        overworld_effect += " " + lines[i].strip()
                        i += 1
                    continue
                
                # Check if this is a new ability (uppercase start, no colon)
                if next_line and next_line[0].isupper() and ':' not in next_line and not any(keyword in next_line for keyword in ['In-Battle', 'Game\'s', 'Overworld']):
                    # Check if line has multiple capitalized words (likely Pokemon names)
                    words = next_line.split()
                    if all(w[0].isupper() or w =='' for w in words if w):
                        # This is likely a Pokemon list
                        pokemon_list.extend(words)
                        i += 1
                    else:
                        # This is a new ability, break
                        break
                else:
                    i += 1
            
            # Save the ability
            if ability_name:
                abilities.append({
                    'name': ability_name,
                    'game_text': game_text,
                    'in_battle_effect': in_battle_effect,
                    'overworld_effect': overworld_effect,
                    'pokemon': pokemon_list
                })
        else:
            i += 1
    
    return abilities

# Run the parser
print("Parsing abilities...")
abilities = parse_abilities_manual()
print(f"Found {len(abilities)} abilities")

# Show first few
for ability in abilities[:10]:
    print(f"\n{ability['name']}")
    if ability['in_battle_effect']:
        print(f"  Effect: {ability['in_battle_effect'][:60]}...")
    if ability['pokemon']:
        print(f"  Pokemon ({len(ability['pokemon'])}): {', '.join(ability['pokemon'][:5])}...")
