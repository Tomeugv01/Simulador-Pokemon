"""
Update Pokemon database with correct evolution data from evolution data JSON
"""
import sqlite3
import json
import os

def update_evolution_data():
    """Update pokemon table with evolution data"""
    
    # Paths
    db_path = 'data/pokemon_battle.db'
    json_path = 'src/evolution data'
    
    if not os.path.exists(db_path):
        print(f"❌ Database not found: {db_path}")
        return
    
    if not os.path.exists(json_path):
        print(f"❌ Evolution data file not found: {json_path}")
        return
    
    # Load evolution data
    print("Loading evolution data...")
    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            content = f.read()
            # Remove BOM if present
            if content.startswith('\ufeff'):
                content = content[1:]
            data = json.loads(content)
    except json.JSONDecodeError as e:
        print(f"❌ Error parsing JSON: {e}")
        print(f"   Trying to read first few bytes...")
        with open(json_path, 'rb') as f:
            first_bytes = f.read(100)
            print(f"   First bytes: {first_bytes}")
        return
    except Exception as e:
        print(f"❌ Error loading file: {e}")
        return
    
    evolutions = data['evolutions']
    print(f"✓ Loaded {len(evolutions)} evolution entries")
    
    # Connect to database
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Create pokemon_evolutions table if it doesn't exist
    print("\n📝 Creating/Checking pokemon_evolutions table...")
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS pokemon_evolutions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            pokemon_id INTEGER,
            evolves_to_id INTEGER,
            evolution_level INTEGER,
            FOREIGN KEY (pokemon_id) REFERENCES pokemon(id),
            FOREIGN KEY (evolves_to_id) REFERENCES pokemon(id)
        )
    ''')
    conn.commit()
    print("✓ Table checked/created")
    
    # Check if evolves_to_id column exists (keep for backward compatibility)
    cursor.execute("PRAGMA table_info(pokemon)")
    columns = [row[1] for row in cursor.fetchall()]
    
    if 'evolves_to_id' not in columns:
        print("\n📝 Adding evolves_to_id column to pokemon table...")
        cursor.execute('''
            ALTER TABLE pokemon 
            ADD COLUMN evolves_to_id INTEGER
        ''')
        conn.commit()
        print("✓ Column added")
    else:
        print("\n✓ evolves_to_id column already exists")
    
    # First, clear existing evolution data
    print("\n🧹 Clearing existing evolution data...")
    cursor.execute("UPDATE pokemon SET evolves_to_id = NULL, evolution_level = NULL")
    cursor.execute("DELETE FROM pokemon_evolutions")
    conn.commit()
    print("✓ Cleared")
    
    # Update evolution data
    print("\n📊 Updating evolution data...")
    updated_count = 0
    skipped_count = 0
    error_count = 0
    
    for evo in evolutions:
        pokemon_id = evo['pokemon_id']
        evolves_to_id = evo['evolves_to_id']
        evolution_level = evo['evolution_level']
        pokemon_name = evo['pokemon_name']
        
        # Check if Pokemon exists in database
        cursor.execute("SELECT id, name FROM pokemon WHERE id = ?", (pokemon_id,))
        result = cursor.fetchone()
        
        if not result:
            print(f"  ⚠️  Pokemon ID {pokemon_id} ({pokemon_name}) not found in database - skipping")
            skipped_count += 1
            continue
        
        # Update the evolution data
        try:
            # Insert into pokemon_evolutions table (supports multiple evolutions)
            cursor.execute('''
                INSERT INTO pokemon_evolutions (pokemon_id, evolves_to_id, evolution_level)
                VALUES (?, ?, ?)
            ''', (pokemon_id, evolves_to_id, evolution_level))

            # Also update legacy columns (will be overwritten if multiple, but keeps compatibility)
            # Only update if it's the first one or just overwrite (last one wins for legacy col)
            cursor.execute('''
                UPDATE pokemon 
                SET evolves_to_id = ?, evolution_level = ?
                WHERE id = ?
            ''', (evolves_to_id, evolution_level, pokemon_id))
            
            updated_count += 1
            
            # Show some progress
            if updated_count % 50 == 0:
                print(f"  ... {updated_count} Pokemon updated")
                
        except Exception as e:
            print(f"  ❌ Error updating {pokemon_name} (ID {pokemon_id}): {e}")
            error_count += 1
    
    # Commit changes
    conn.commit()
    
    # Show summary
    print("\n" + "="*70)
    print("EVOLUTION DATA UPDATE SUMMARY")
    print("="*70)
    print(f"✓ Successfully updated: {updated_count} Pokemon")
    if skipped_count > 0:
        print(f"⚠️  Skipped (not in DB): {skipped_count} Pokemon")
    if error_count > 0:
        print(f"❌ Errors: {error_count}")
    
    # Verification: Show some examples
    print("\n" + "="*70)
    print("VERIFICATION - Sample Evolution Chains:")
    print("="*70)
    
    # Check starter evolutions
    starters = [
        (1, "Bulbasaur"), (4, "Charmander"), (7, "Squirtle"),
        (25, "Pikachu"), (133, "Eevee")
    ]
    
    for starter_id, starter_name in starters:
        cursor.execute("""
            SELECT p1.id, p1.name, p1.evolution_level, p1.evolves_to_id, p2.name as evolves_to_name
            FROM pokemon p1
            LEFT JOIN pokemon p2 ON p1.evolves_to_id = p2.id
            WHERE p1.id = ?
        """, (starter_id,))
        
        result = cursor.fetchone()
        if result:
            pid, name, evo_level, evo_id, evo_name = result
            if evo_id:
                print(f"  {name} (#{pid}) → {evo_name} (#{evo_id}) at level {evo_level}")
            else:
                print(f"  {name} (#{pid}) → Does not evolve")
    
    # Show evolution chains
    print("\n📊 Full Evolution Chains:")
    print("-"*70)
    
    # Example: Bulbasaur line
    cursor.execute("""
        WITH RECURSIVE evolution_chain AS (
            -- Start with Bulbasaur
            SELECT id, name, evolution_level, evolves_to_id, 0 as stage
            FROM pokemon 
            WHERE id = 1
            
            UNION ALL
            
            -- Recursively get evolutions
            SELECT p.id, p.name, p.evolution_level, p.evolves_to_id, ec.stage + 1
            FROM pokemon p
            INNER JOIN evolution_chain ec ON p.id = ec.evolves_to_id
            WHERE ec.stage < 10
        )
        SELECT * FROM evolution_chain
    """)
    
    chain = cursor.fetchall()
    if chain:
        chain_str = " → ".join([f"{row[1]} (Lv.{row[2] if row[2] else 'N/A'})" for row in chain])
        print(f"  Bulbasaur line: {chain_str}")
    
    # Example: Charmander line
    cursor.execute("""
        WITH RECURSIVE evolution_chain AS (
            SELECT id, name, evolution_level, evolves_to_id, 0 as stage
            FROM pokemon 
            WHERE id = 4
            
            UNION ALL
            
            SELECT p.id, p.name, p.evolution_level, p.evolves_to_id, ec.stage + 1
            FROM pokemon p
            INNER JOIN evolution_chain ec ON p.id = ec.evolves_to_id
            WHERE ec.stage < 10
        )
        SELECT * FROM evolution_chain
    """)
    
    chain = cursor.fetchall()
    if chain:
        chain_str = " → ".join([f"{row[1]} (Lv.{row[2] if row[2] else 'N/A'})" for row in chain])
        print(f"  Charmander line: {chain_str}")
    
    # Statistics
    print("\n" + "="*70)
    print("DATABASE STATISTICS:")
    print("="*70)
    
    cursor.execute("SELECT COUNT(*) FROM pokemon")
    total_pokemon = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM pokemon WHERE evolves_to_id IS NOT NULL")
    can_evolve = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM pokemon WHERE evolves_to_id IS NULL")
    cannot_evolve = cursor.fetchone()[0]
    
    print(f"Total Pokemon in database: {total_pokemon}")
    print(f"Pokemon that can evolve: {can_evolve}")
    print(f"Pokemon that don't evolve: {cannot_evolve}")
    
    conn.close()
    print("\n✅ Evolution data update complete!")

if __name__ == "__main__":
    update_evolution_data()
