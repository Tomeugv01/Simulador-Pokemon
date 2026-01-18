"""Add missing secondary effects to moves"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.database import DatabaseManager

# Initialize database
db_manager = DatabaseManager()
conn = db_manager.get_connection()
cursor = conn.cursor()

# Check what effect IDs exist
cursor.execute("SELECT id, name, effect_type, status_condition FROM move_effects")
effects = cursor.fetchall()

print("Available effects in database:")
for eff in effects[:20]:  # Show first 20
    print(f"  ID {eff[0]}: {eff[1]} ({eff[2]}, Status: {eff[3]})")

print("\n" + "="*80)
print("Adding missing effects...")
print("="*80)

# Get effect IDs we need
cursor.execute("SELECT id FROM move_effects WHERE name = 'Paralysis 10%'")
paralysis_10_effect = cursor.fetchone()

cursor.execute("SELECT id FROM move_effects WHERE name = 'Flinch' AND effect_type = 'OTHER'")
flinch_effect = cursor.fetchone()

cursor.execute("SELECT id FROM move_effects WHERE name = 'Freeze 10%'")
freeze_10_effect = cursor.fetchone()

cursor.execute("SELECT id FROM move_effects WHERE name LIKE '%Badly%Poison%' OR (name LIKE '%Poison%' AND status_condition LIKE '%Badly%')")
poison_50_effect = cursor.fetchone()

print(f"\nFound effect IDs:")
print(f"  Paralysis 10%: {paralysis_10_effect}")
print(f"  Flinch: {flinch_effect}")
print(f"  Freeze 10%: {freeze_10_effect}")
print(f"  Poison 50%: {poison_50_effect}")

# If effects don't exist, we need to create them
if not flinch_effect:
    print("\nCreating Flinch effect...")
    cursor.execute("""
        INSERT INTO move_effects (name, effect_type, status_condition)
        VALUES ('Flinch', 'OTHER', NULL)
    """)
    flinch_effect_id = cursor.lastrowid
    print(f"Created Flinch effect with ID: {flinch_effect_id}")
else:
    flinch_effect_id = flinch_effect[0]
    print(f"\nUsing existing Flinch effect ID: {flinch_effect_id}")

if not paralysis_10_effect:
    print("\nCreating Paralysis 10% effect...")
    cursor.execute("""
        INSERT INTO move_effects (name, effect_type, status_condition)
        VALUES ('Paralysis 10%', 'STATUS', 'Paralysis')
    """)
    paralysis_10_effect_id = cursor.lastrowid
    print(f"Created Paralysis 10% effect with ID: {paralysis_10_effect_id}")
else:
    paralysis_10_effect_id = paralysis_10_effect[0]
    print(f"\nUsing existing Paralysis 10% effect ID: {paralysis_10_effect_id}")

if not freeze_10_effect:
    print("\nCreating Freeze 10% effect...")
    cursor.execute("""
        INSERT INTO move_effects (name, effect_type, status_condition)
        VALUES ('Freeze 10%', 'STATUS', 'Freeze')
    """)
    freeze_10_effect_id = cursor.lastrowid
    print(f"Created Freeze 10% effect with ID: {freeze_10_effect_id}")
else:
    freeze_10_effect_id = freeze_10_effect[0]
    print(f"\nUsing existing Freeze 10% effect ID: {freeze_10_effect_id}")

if not poison_50_effect:
    print("\nCreating Badly Poison effect...")
    cursor.execute("""
        INSERT INTO move_effects (name, effect_type, status_condition)
        VALUES ('Badly Poison', 'STATUS', 'Poison')
    """)
    poison_50_effect_id = cursor.lastrowid
    print(f"Created Badly Poison effect with ID: {poison_50_effect_id}")
else:
    poison_50_effect_id = poison_50_effect[0]
    print(f"\nUsing existing Poison effect ID: {poison_50_effect_id}")

# Now add the move effects
print("\n" + "="*80)
print("Adding move effect instances...")
print("="*80)

# Thunder Fang (422): Paralysis 10% + Flinch 10%
print("\nThunder Fang:")
try:
    cursor.execute("""
        INSERT INTO move_effect_instances (move_id, effect_id, probability, effect_order, triggers_on)
        VALUES (422, ?, 10, 1, 'OnHit')
    """, (paralysis_10_effect_id,))
    print(f"  Added Paralysis 10%")
except Exception as e:
    print(f"  Error adding Paralysis: {e}")

try:
    cursor.execute("""
        INSERT INTO move_effect_instances (move_id, effect_id, probability, effect_order, triggers_on)
        VALUES (422, ?, 10, 2, 'OnHit')
    """, (flinch_effect_id,))
    print(f"  Added Flinch 10%")
except Exception as e:
    print(f"  Error adding Flinch: {e}")

# Ice Fang (423): Freeze 10% + Flinch 10%
print("\nIce Fang:")
try:
    cursor.execute("""
        INSERT INTO move_effect_instances (move_id, effect_id, probability, effect_order, triggers_on)
        VALUES (423, ?, 10, 1, 'OnHit')
    """, (freeze_10_effect_id,))
    print(f"  Added Freeze 10%")
except Exception as e:
    print(f"  Error adding Freeze: {e}")

try:
    cursor.execute("""
        INSERT INTO move_effect_instances (move_id, effect_id, probability, effect_order, triggers_on)
        VALUES (423, ?, 10, 2, 'OnHit')
    """, (flinch_effect_id,))
    print(f"  Added Flinch 10%")
except Exception as e:
    print(f"  Error adding Flinch: {e}")

# Poison Fang (305): Badly Poison 50%
print("\nPoison Fang:")
try:
    cursor.execute("""
        INSERT INTO move_effect_instances (move_id, effect_id, probability, effect_order, triggers_on)
        VALUES (305, ?, 50, 1, 'OnHit')
    """, (poison_50_effect_id,))
    print(f"  Added Badly Poison 50%")
except Exception as e:
    print(f"  Error adding Badly Poison: {e}")

# Fake Out (252): Flinch 100%
print("\nFake Out:")
try:
    cursor.execute("""
        INSERT INTO move_effect_instances (move_id, effect_id, probability, effect_order, triggers_on)
        VALUES (252, ?, 100, 1, 'OnHit')
    """, (flinch_effect_id,))
    print(f"  Added Flinch 100%")
except Exception as e:
    print(f"  Error adding Flinch: {e}")

conn.commit()
print("\n" + "="*80)
print("DONE - Effects added successfully!")
print("="*80)
conn.close()
