import sqlite3

conn = sqlite3.connect('data/pokemon_battle.db')
cursor = conn.cursor()

# Check some specific Pokemon to verify type IDs are correct
test_pokemon = [
    (25, "Pikachu", "Electric", None),
    (6, "Charizard", "Fire", "Flying"),
    (94, "Gengar", "Ghost", "Poison"),
    (130, "Gyarados", "Water", "Flying"),
    (150, "Mewtwo", "Psychic", None),
    (81, "Magnemite", "Electric", "Steel"),
    (138, "Omanyte", "Rock", "Water"),
]

print("Verificación de Pokemon específicos:")
print("=" * 70)

for pokemon_id, expected_name, expected_t1, expected_t2 in test_pokemon:
    cursor.execute('''
    SELECT 
        p.id, 
        p.name, 
        p.type1,
        t1.name as type1_name,
        p.type2,
        t2.name as type2_name
    FROM pokemon p
    JOIN types t1 ON p.type1 = t1.id
    LEFT JOIN types t2 ON p.type2 = t2.id
    WHERE p.id = ?
    ''', (pokemon_id,))
    
    p = cursor.fetchone()
    if p:
        type2_display = f"{p[5]}" if p[5] else "None"
        status = "✓" if p[3] == expected_t1 and (p[5] == expected_t2 or (p[5] is None and expected_t2 is None)) else "✗"
        print(f"{status} #{p[0]:3d} {p[1]:12s}: {p[3]:10s} / {type2_display:10s} (IDs: {p[2]}, {p[4] if p[4] else 'NULL'})")

conn.close()
