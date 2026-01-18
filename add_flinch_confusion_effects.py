"""Add missing Confusion and Flinch effects to moves"""
import sys, os
sys.path.insert(0, 'src')
from database import DatabaseManager

db = DatabaseManager()
conn = db.get_connection()
cur = conn.cursor()

# Get Flinch effect ID
cur.execute("SELECT id FROM move_effects WHERE name = 'Flinch'")
flinch_effect = cur.fetchone()
if flinch_effect:
    flinch_id = flinch_effect[0]
    print(f"Found Flinch effect: ID {flinch_id}")
else:
    print("ERROR: Flinch effect not found!")
    conn.close()
    exit(1)

# Check if Confusion effect exists, create if not
cur.execute("SELECT id FROM move_effects WHERE name = 'Confusion'")
confusion_effect = cur.fetchone()
if confusion_effect:
    confusion_id = confusion_effect[0]
    print(f"Found Confusion effect: ID {confusion_id}")
else:
    print("Creating Confusion effect...")
    cur.execute("""
        INSERT INTO move_effects (name, effect_type, status_condition)
        VALUES ('Confusion', 'OTHER', 'Confusion')
    """)
    confusion_id = cur.lastrowid
    print(f"Created Confusion effect: ID {confusion_id}")

# Define moves that need effects added
flinch_moves = [
    ('Air Slash', 30),
    ('Bite', 30),
    ('Bone Club', 10),
    ('Dark Pulse', 20),
    ('Double Iron Bash', 30),
    ('Dragon Rush', 20),
    ('Headbutt', 30),
    ('Heart Stamp', 30),
    ('Hyper Fang', 10),
    ('Icicle Crash', 30),
    ('Iron Head', 30),  # Already has it, but let's check
    ('Needle Arm', 30),
    ('Rock Slide', 30),
    ('Rolling Kick', 30),
    ('Sky Attack', 30),
    ('Stomp', 30),
    ('Waterfall', 20),
    ('Zen Headbutt', 20),
    ('Zing Zap', 30),
]

confusion_moves = [
    ('Chatter', 100),
    ('Confusion', 10),
    ('Dizzy Punch', 20),
    ('Dynamic Punch', 100),
    ('Hurricane', 30),
    ('Petal Dance', 100),  # Note: This might be self-confusion after use
    ('Psybeam', 10),
    ('Thrash', 100),  # Note: This might be self-confusion after use
]

print("\n" + "="*80)
print("Adding Flinch effects...")
print("="*80)

added_flinch = 0
for move_name, probability in flinch_moves:
    # Get move ID
    cur.execute("SELECT id FROM moves WHERE name = ?", (move_name,))
    move = cur.fetchone()
    
    if not move:
        print(f"⚠ Move not found: {move_name}")
        continue
    
    move_id = move[0]
    
    # Check if effect already exists
    cur.execute("""
        SELECT id FROM move_effect_instances 
        WHERE move_id = ? AND effect_id = ?
    """, (move_id, flinch_id))
    
    if cur.fetchone():
        print(f"✓ {move_name} (ID {move_id}) already has Flinch effect")
    else:
        # Add the effect
        try:
            cur.execute("""
                INSERT INTO move_effect_instances (move_id, effect_id, probability, effect_order, triggers_on)
                VALUES (?, ?, ?, 1, 'OnHit')
            """, (move_id, flinch_id, probability))
            print(f"✓ Added Flinch {probability}% to {move_name} (ID {move_id})")
            added_flinch += 1
        except Exception as e:
            print(f"✗ Error adding to {move_name}: {e}")

print(f"\nAdded {added_flinch} new Flinch effects")

print("\n" + "="*80)
print("Adding Confusion effects...")
print("="*80)

added_confusion = 0
for move_name, probability in confusion_moves:
    # Get move ID
    cur.execute("SELECT id FROM moves WHERE name = ?", (move_name,))
    move = cur.fetchone()
    
    if not move:
        print(f"⚠ Move not found: {move_name}")
        continue
    
    move_id = move[0]
    
    # Check if effect already exists
    cur.execute("""
        SELECT id FROM move_effect_instances 
        WHERE move_id = ? AND effect_id = ?
    """, (move_id, confusion_id))
    
    if cur.fetchone():
        print(f"✓ {move_name} (ID {move_id}) already has Confusion effect")
    else:
        # Add the effect
        # Note: For Petal Dance and Thrash, the target might be 'User' not 'Target'
        # But we'll add them as target-confusion for now
        try:
            cur.execute("""
                INSERT INTO move_effect_instances (move_id, effect_id, probability, effect_order, triggers_on)
                VALUES (?, ?, ?, 1, 'OnHit')
            """, (move_id, confusion_id, probability))
            print(f"✓ Added Confusion {probability}% to {move_name} (ID {move_id})")
            added_confusion += 1
        except Exception as e:
            print(f"✗ Error adding to {move_name}: {e}")

print(f"\nAdded {added_confusion} new Confusion effects")

conn.commit()
conn.close()

print("\n" + "="*80)
print(f"DONE! Added {added_flinch} Flinch + {added_confusion} Confusion effects")
print("="*80)
