import sqlite3

conn = sqlite3.connect('data/pokemon_battle.db')
cursor = conn.cursor()

# Verificar pokemon con evolución
print("=== Pokémon con nivel de evolución ===")
cursor.execute('SELECT id, name, evolution_level, exp_curve FROM pokemon WHERE evolution_level IS NOT NULL ORDER BY id LIMIT 10')
for row in cursor.fetchall():
    print(f"  ID: {row[0]:3d} | {row[1]:15s} | Evolve: Lv.{row[2]:2d} | Curve: {row[3]}")

# Verificar pokemon sin evolución
print("\n=== Pokémon sin evolución (sample) ===")
cursor.execute('SELECT id, name, evolution_level, exp_curve FROM pokemon WHERE evolution_level IS NULL ORDER BY id LIMIT 10')
for row in cursor.fetchall():
    print(f"  ID: {row[0]:3d} | {row[1]:15s} | Evolve: None  | Curve: {row[3]}")

# Estadísticas por curva
print("\n=== Distribución de curvas de experiencia ===")
cursor.execute('SELECT exp_curve, COUNT(*) as count FROM pokemon GROUP BY exp_curve ORDER BY count DESC')
for row in cursor.fetchall():
    print(f"  {row[0]:15s}: {row[1]:3d} pokemon")

# Verificar algunos pokemon específicos
print("\n=== Verificación de cadenas evolutivas ===")
chains = [
    ('Bulbasaur', 'Ivysaur', 'Venusaur'),
    ('Dratini', 'Dragonair', 'Dragonite'),
    ('Magikarp', 'Gyarados', None),
    ('Pikachu', 'Raichu', None)
]

for chain in chains:
    print(f"\n  Cadena: {' -> '.join(filter(None, chain))}")
    for poke_name in chain:
        if poke_name:
            cursor.execute('SELECT id, name, evolution_level, exp_curve FROM pokemon WHERE name = ?', (poke_name,))
            row = cursor.fetchone()
            if row:
                evo = f"Lv.{row[2]}" if row[2] else "None"
                print(f"    {row[1]:12s} - Evolve: {evo:6s} | Curve: {row[3]}")

conn.close()
