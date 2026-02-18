"""Populate pokemon_abilities table from export data."""
import sqlite3
import sys
sys.path.insert(0, '.')

from pokemon_abilities_export import POKEMON_ABILITIES

conn = sqlite3.connect('data/pokemon_battle.db')
cursor = conn.cursor()

# Check current state
cursor.execute('SELECT COUNT(*) FROM pokemon_abilities')
print(f'Current pokemon_abilities rows: {cursor.fetchone()[0]}')

# Insert pokemon abilities
cursor.executemany('''
    INSERT OR REPLACE INTO pokemon_abilities (pokemon_id, ability_id, is_hidden, slot)
    VALUES (?, ?, ?, ?)
''', POKEMON_ABILITIES)

conn.commit()

cursor.execute('SELECT COUNT(*) FROM pokemon_abilities')
print(f'After insert pokemon_abilities rows: {cursor.fetchone()[0]}')

# Verify sample data
cursor.execute('''
    SELECT pa.pokemon_id, p.name, a.name, pa.is_hidden, pa.slot
    FROM pokemon_abilities pa
    JOIN pokemon p ON pa.pokemon_id = p.id
    JOIN abilities a ON pa.ability_id = a.id
    WHERE pa.pokemon_id IN (1, 4, 7, 25, 150)
    ORDER BY pa.pokemon_id, pa.slot
''')
print('\nSample data:')
for row in cursor.fetchall():
    print(f'  #{row[0]} {row[1]}: {row[2]} (hidden={row[3]}, slot={row[4]})')

conn.close()
print('\nDone!')
