"""Simple debug to check database for failed moves"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.database import DatabaseManager

# Initialize database
db_manager = DatabaseManager()

failed_moves = [
    "Thunder Fang",
    "Ice Fang",
    "Poison Fang",
    "Iron Head",
    "Fake Out",
    "Thunderbolt"
]

conn = db_manager.get_connection()
cursor = conn.cursor()

print("="*80)
print("DATABASE CHECK FOR FAILED MOVES")
print("="*80)

for move_name in failed_moves:
    print(f"\n{move_name}:")
    print("-"*80)
    
    # Check if move exists
    cursor.execute("SELECT id, name FROM moves WHERE name = ?", (move_name,))
    move = cursor.fetchone()
    
    if not move:
        # Try with different naming (Thunder-Fang vs Thunder Fang)
        cursor.execute("SELECT id, name FROM moves WHERE name LIKE ?", (f"%{move_name.replace(' ', '%')}%",))
        move = cursor.fetchone()
        
        if move:
            print(f"  Found as: {move[1]} (ID: {move[0]})")
        else:
            print(f"  NOT FOUND in database")
            continue
    else:
        print(f"  Move ID: {move[0]}")
    
    move_id = move[0]
    
    # Check effects
    cursor.execute("""
        SELECT me.name, me.effect_type, me.status_condition,
               mei.probability, mei.triggers_on
        FROM move_effect_instances mei
        JOIN move_effects me ON mei.effect_id = me.id
        WHERE mei.move_id = ?
    """, (move_id,))
    
    effects = cursor.fetchall()
    
    if not effects:
        print(f"  NO EFFECTS FOUND")
    else:
        print(f"  Effects ({len(effects)}):")
        for effect in effects:
            effect_name, effect_type, status_cond, probability, triggers_on = effect
            print(f"    - {effect_name}")
            print(f"      Type: {effect_type}")
            print(f"      Status: {status_cond}")
            print(f"      Probability: {probability}%")
            print(f"      Triggers On: {triggers_on}")

conn.close()
