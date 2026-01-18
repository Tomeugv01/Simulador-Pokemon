
import sys
import os

# Add src to path
sys.path.append(os.path.join(os.getcwd(), 'src'))

from database import DatabaseManager

def test_db():
    print("Initializing Database...")
    db = DatabaseManager()
    db.initialize_database()
    
    conn = db.get_connection()
    cursor = conn.cursor()
    
    # 1. Count Moves
    cursor.execute("SELECT count(*) FROM moves")
    count = cursor.fetchone()[0]
    print(f"Total Moves: {count}")
    
    if count < 700:
        print("FAIL: Expected > 700 moves")
    else:
        print("PASS: Count looks good")

    # 2. Check Specific Move (Ember)
    cursor.execute("SELECT * FROM moves WHERE name='Ember'")
    ember = cursor.fetchone()
    print(f"Ember: {ember}")
    # Ember is ID 52 in Gen 1 list usually, or 1? 
    # In my generated list: (52, 'Ember', ...)
    
    # 3. Check Effects for Tri Attack (Move 161)
    # Tri Attack should have Par, Burn, Freeze
    cursor.execute("SELECT id FROM moves WHERE name='Tri Attack'")
    res = cursor.fetchone()
    if res:
        mid = res[0]
        print(f"Tri Attack ID: {mid}")
        
        cursor.execute("SELECT me.name, probability, triggers_on FROM move_effect_instances mei JOIN move_effects me ON mei.effect_id = me.id WHERE move_id = ?", (mid,))
        effects = cursor.fetchall()
        print("Tri Attack Effects:")
        for e in effects:
            print(f" - {e}")
            
    conn.close()

if __name__ == "__main__":
    test_db()
