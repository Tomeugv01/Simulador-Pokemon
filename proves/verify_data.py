import sqlite3

conn = sqlite3.connect('data/pokemon_battle.db')
cursor = conn.cursor()

cursor.execute('SELECT COUNT(*) FROM pokemon')
count = cursor.fetchone()[0]
print(f'Total pokemon: {count}')

cursor.execute('SELECT id, name, evolution_level, exp_curve FROM pokemon LIMIT 5')
print('\nFirst 5 pokemon:')
for row in cursor.fetchall():
    print(f'  ID: {row[0]}, Name: {row[1]}, Evo Level: {row[2]}, Exp Curve: {row[3]}')

conn.close()
