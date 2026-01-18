import sqlite3

def check_coverage():
    conn = sqlite3.connect('data/pokemon_battle.db')
    c = conn.cursor()
    
    # Get all moves and their descriptions
    c.execute("SELECT id, name, description, category FROM moves")
    moves = c.fetchall()
    
    # Get all moves that have effect instances
    c.execute("SELECT DISTINCT move_id FROM move_effect_instances")
    moves_with_effects = set(row[0] for row in c.fetchall())
    
    keywords = ['paralyze', 'burn', 'freeze', 'poison', 'sleep', 'confusion', 'flinch',
                'raise', 'lower', 'recover', 'heal', 'absorb', 'recoil', 'switch', 'trap', 'crit', 'priority']
                
    missing_moves = []
    
    for mid, name, desc, category in moves:
        if mid not in moves_with_effects:
            # Check if description implies an effect
            desc_lower = desc.lower() if desc else ""
            if any(k in desc_lower for k in keywords):
                missing_moves.append((name, desc))
            elif category == 'Status':
                 # Status moves almost always have effects (unless they just fail?)
                 missing_moves.append((name, desc))

    print(f"Total moves: {len(moves)}")
    print(f"Moves with effects linked: {len(moves_with_effects)}")
    print(f"Moves appearing to miss effects (by description/category analysis): {len(missing_moves)}")
    
    print("\nSample of potential missing effects:")
    for name, desc in missing_moves[:50]:
        print(f" - {name}: {desc}")

check_coverage()
