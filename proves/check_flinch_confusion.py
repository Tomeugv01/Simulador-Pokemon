import sys, os
sys.path.insert(0, 'src')
from database import DatabaseManager

db = DatabaseManager()
conn = db.get_connection()
cur = conn.cursor()

print("Flinch effects:")
cur.execute("SELECT id, name, effect_type FROM move_effects WHERE name LIKE '%Flinch%'")
for row in cur.fetchall():
    print(f"  ID {row[0]}: {row[1]} ({row[2]})")

print("\nConfusion effects:")
cur.execute("SELECT id, name, effect_type FROM move_effects WHERE name LIKE '%Confusion%' OR name LIKE '%Confuse%'")
for row in cur.fetchall():
    print(f"  ID {row[0]}: {row[1]} ({row[2]})")

conn.close()
