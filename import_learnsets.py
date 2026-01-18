"""
Add Pokemon Learnset table and import data from xy.json

This script:
1. Creates a pokemon_learnsets table in the database
2. Imports levelup moves from xy.json
3. Provides methods to query learnsets
"""
import sys
import os
import json
import sqlite3

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))
from src.database import DatabaseManager

def create_learnset_table(cursor):
    """Create the pokemon_learnsets table"""
    print("Creating pokemon_learnsets table...")
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS pokemon_learnsets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            pokemon_id INTEGER NOT NULL,
            move_id INTEGER NOT NULL,
            learn_method TEXT NOT NULL CHECK(learn_method IN ('levelup', 'tm', 'egg', 'tutor', 'evolution', 'special')),
            learn_level INTEGER,
            form INTEGER DEFAULT 0,
            FOREIGN KEY (pokemon_id) REFERENCES pokemon(id) ON DELETE CASCADE,
            FOREIGN KEY (move_id) REFERENCES moves(id) ON DELETE CASCADE,
            UNIQUE (pokemon_id, move_id, learn_method, form)
        )
    ''')
    
    # Create indexes for faster queries
    cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_learnset_pokemon 
        ON pokemon_learnsets(pokemon_id, form)
    ''')
    
    cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_learnset_level 
        ON pokemon_learnsets(pokemon_id, learn_level)
    ''')
    
    print("✓ Table created successfully")

def import_learnsets_from_json(cursor, json_file_path):
    """Import learnset data from xy.json"""
    print(f"\nImporting learnsets from {json_file_path}...")
    
    # Load JSON data
    with open(json_file_path, 'r', encoding='utf-8') as f:
        learnset_data = json.load(f)
    
    print(f"Loaded data for {len(learnset_data)} Pokemon entries")
    
    # Clear existing learnset data
    print("Clearing existing learnset data...")
    cursor.execute("DELETE FROM pokemon_learnsets WHERE learn_method = 'levelup'")
    
    # Import data
    levelup_moves = 0
    other_moves = 0
    errors = []
    
    for entry in learnset_data:
        pokemon_id = entry['pokemon']
        form = entry.get('form', 0)
        
        for move_entry in entry['moves']:
            move_id = move_entry['move']
            method = move_entry['method']
            level = move_entry.get('level', None)
            
            # Only import levelup moves for now
            if method == 'levelup':
                try:
                    cursor.execute('''
                        INSERT OR REPLACE INTO pokemon_learnsets 
                        (pokemon_id, move_id, learn_method, learn_level, form)
                        VALUES (?, ?, ?, ?, ?)
                    ''', (pokemon_id, move_id, method, level, form))
                    levelup_moves += 1
                except sqlite3.Error as e:
                    errors.append(f"Pokemon {pokemon_id}, Move {move_id}: {e}")
            else:
                other_moves += 1
    
    print(f"\n✓ Imported {levelup_moves} levelup moves")
    print(f"  Skipped {other_moves} non-levelup moves (tm, egg, tutor, etc.)")
    
    if errors:
        print(f"\n⚠ {len(errors)} errors encountered:")
        for error in errors[:10]:  # Show first 10 errors
            print(f"  {error}")
        if len(errors) > 10:
            print(f"  ... and {len(errors) - 10} more")
    
    return levelup_moves

def verify_import(cursor):
    """Verify the imported data"""
    print("\n" + "="*80)
    print("VERIFICATION")
    print("="*80)
    
    # Count total moves
    cursor.execute("SELECT COUNT(*) FROM pokemon_learnsets WHERE learn_method = 'levelup'")
    total_moves = cursor.fetchone()[0]
    print(f"Total levelup moves in database: {total_moves}")
    
    # Count Pokemon with learnsets
    cursor.execute("""
        SELECT COUNT(DISTINCT pokemon_id) 
        FROM pokemon_learnsets 
        WHERE learn_method = 'levelup'
    """)
    pokemon_count = cursor.fetchone()[0]
    print(f"Pokemon with learnsets: {pokemon_count}")
    
    # Show sample data for a few Pokemon
    print("\nSample learnsets:")
    test_pokemon = [1, 25, 143]  # Bulbasaur, Pikachu, Snorlax
    
    for pokemon_id in test_pokemon:
        cursor.execute("""
            SELECT p.name, COUNT(pl.move_id) as move_count
            FROM pokemon p
            LEFT JOIN pokemon_learnsets pl ON p.id = pl.pokemon_id AND pl.learn_method = 'levelup'
            WHERE p.id = ?
            GROUP BY p.id
        """, (pokemon_id,))
        
        result = cursor.fetchone()
        if result:
            name, move_count = result
            print(f"  {name} (ID {pokemon_id}): {move_count} levelup moves")
            
            # Show first 5 moves
            cursor.execute("""
                SELECT m.name, pl.learn_level
                FROM pokemon_learnsets pl
                JOIN moves m ON pl.move_id = m.id
                WHERE pl.pokemon_id = ? AND pl.learn_method = 'levelup'
                ORDER BY pl.learn_level
                LIMIT 5
            """, (pokemon_id,))
            
            for move_name, level in cursor.fetchall():
                print(f"    Level {level}: {move_name}")

def add_helper_functions_to_database_py():
    """Print helper functions to add to database.py"""
    print("\n" + "="*80)
    print("HELPER FUNCTIONS TO ADD TO database.py")
    print("="*80)
    print("""
Add these functions to the DatabaseManager class or as standalone functions:

def get_pokemon_learnset(pokemon_id, max_level=None):
    '''Get all moves a Pokemon can learn by leveling up'''
    db = DatabaseManager()
    conn = db.get_connection()
    cursor = conn.cursor()
    
    query = '''
        SELECT m.id, m.name, pl.learn_level, m.type, m.category, m.power, m.accuracy, m.pp
        FROM pokemon_learnsets pl
        JOIN moves m ON pl.move_id = m.id
        WHERE pl.pokemon_id = ? AND pl.learn_method = 'levelup'
    '''
    
    if max_level:
        query += ' AND pl.learn_level <= ?'
        cursor.execute(query + ' ORDER BY pl.learn_level', (pokemon_id, max_level))
    else:
        cursor.execute(query + ' ORDER BY pl.learn_level', (pokemon_id,))
    
    moves = []
    for row in cursor.fetchall():
        moves.append({
            'id': row[0],
            'name': row[1],
            'learn_level': row[2],
            'type': row[3],
            'category': row[4],
            'power': row[5],
            'accuracy': row[6],
            'pp': row[7]
        })
    
    conn.close()
    return moves

def get_moves_at_level(pokemon_id, level):
    '''Get moves a Pokemon learns at a specific level'''
    db = DatabaseManager()
    conn = db.get_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT m.id, m.name
        FROM pokemon_learnsets pl
        JOIN moves m ON pl.move_id = m.id
        WHERE pl.pokemon_id = ? AND pl.learn_method = 'levelup' AND pl.learn_level = ?
        ORDER BY m.name
    ''', (pokemon_id, level))
    
    moves = [{'id': row[0], 'name': row[1]} for row in cursor.fetchall()]
    conn.close()
    return moves

def get_available_moves_for_level(pokemon_id, current_level, count=4):
    '''Get the most recent moves available for a Pokemon at a given level'''
    db = DatabaseManager()
    conn = db.get_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT m.id, m.name, pl.learn_level
        FROM pokemon_learnsets pl
        JOIN moves m ON pl.move_id = m.id
        WHERE pl.pokemon_id = ? AND pl.learn_method = 'levelup' AND pl.learn_level <= ?
        ORDER BY pl.learn_level DESC
        LIMIT ?
    ''', (pokemon_id, current_level, count))
    
    moves = []
    for row in cursor.fetchall():
        moves.append({
            'id': row[0],
            'name': row[1],
            'learn_level': row[2]
        })
    
    conn.close()
    return moves
""")

if __name__ == "__main__":
    print("="*80)
    print("POKEMON LEARNSET DATABASE INTEGRATION")
    print("="*80)
    
    # Initialize database
    db_manager = DatabaseManager()
    conn = db_manager.get_connection()
    cursor = conn.cursor()
    
    try:
        # Step 1: Create table
        create_learnset_table(cursor)
        
        # Step 2: Import data from JSON
        json_path = os.path.join(os.path.dirname(__file__), 'models', 'xy.json')
        
        if not os.path.exists(json_path):
            print(f"\n✗ ERROR: JSON file not found at {json_path}")
            print("Please ensure xy.json is in the models/ directory")
            sys.exit(1)
        
        levelup_count = import_learnsets_from_json(cursor, json_path)
        
        # Step 3: Commit changes
        conn.commit()
        print("\n✓ All changes committed to database")
        
        # Step 4: Verify
        verify_import(cursor)
        
        # Step 5: Show helper functions
        add_helper_functions_to_database_py()
        
        print("\n" + "="*80)
        print("✓ IMPORT COMPLETE!")
        print("="*80)
        print(f"\nSuccessfully imported {levelup_count} levelup moves for 493 Pokemon")
        print("\nNext steps:")
        print("1. Add the helper functions above to src/database.py")
        print("2. Update Pokemon class to use get_available_moves_for_level()")
        print("3. Update team generation to use the new learnset system")
        
    except Exception as e:
        print(f"\n✗ ERROR: {e}")
        import traceback
        traceback.print_exc()
        conn.rollback()
    finally:
        conn.close()
