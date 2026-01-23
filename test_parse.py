"""
Simple line-by-line parser for abilities
"""

def parse_abilities_simple():
    with open('habilitats.txt', 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    abilities = []
    current_ability = None
    reading_pokemon = False
    
    for i, line in enumerate(lines):
        line = line.rstrip()
        stripped = line.strip()
        
        # Skip completely empty lines
        if not stripped:
            reading_pokemon = False
            continue
        
        # Check for section headers
        if "Game's Text:" in stripped:
            if current_ability:
                current_ability['game_text'] = stripped.replace("Game's Text:", "").strip()
            continue
        
        if "In-Battle Effect:" in stripped:
            if current_ability:
                current_ability['in_battle_effect'] = stripped.replace("In-Battle Effect:", "").strip()
                reading_pokemon = False
            continue
        
        if "Overworld Effect:" in stripped:
            if current_ability:
                current_ability['overworld_effect'] = stripped.replace("Overworld Effect:", "").strip()
                reading_pokemon = False
            continue
        
        # Check if this line is a new ability name
        # Ability names: no colon, starts with uppercase, relatively short
        if ':' not in stripped and stripped and len(stripped) < 50:
            if stripped[0].isupper() and not reading_pokemon:
                # Check if previous ability should be saved
                if current_ability:
                    abilities.append(current_ability)
                
                # Start new ability
                current_ability = {
                    'name': stripped,
                    'game_text': '',
                    'in_battle_effect': '',
                    'overworld_effect': '',
                    'pokemon': []
                }
                reading_pokemon = False
                continue
        
        # If we have a current ability and this line has uppercase words, it's Pokemon
        if current_ability and stripped:
            # Check if line looks like Pokemon names (multiple capitalized words)
            words = stripped.split()
            if words and all(w[0].isupper() for w in words if w and len(w) > 1):
                reading_pokemon = True
                current_ability['pokemon'].extend(words)
    
    # Don't forget last ability
    if current_ability:
        abilities.append(current_ability)
    
    return abilities

# Test it
abilities = parse_abilities_simple()
print(f"Found {len(abilities)} abilities\n")

for i, ability in enumerate(abilities[:10], 1):
    print(f"{i}. {ability['name']}")
    if ability['in_battle_effect']:
        print(f"   Effect: {ability['in_battle_effect'][:60]}...")
    print(f"   Pokemon: {', '.join(ability['pokemon'][:5])}{'...' if len(ability['pokemon']) > 5 else ''}\n")
