import sqlite3

conn = sqlite3.connect('data/pokemon_battle.db')
cursor = conn.cursor()

# Query to check the first 15 Pokemon with their types
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
WHERE p.id <= 15
ORDER BY p.id
''')

pokemon = cursor.fetchall()

print("Pokemon con tipos (verificando que type1/type2 son IDs):")
print("=" * 80)
for p in pokemon:
    type2_str = f"{p[4]:2d} ({p[5]:10s})" if p[4] else "--  (None)      "
    print(f"{p[0]:3d}. {p[1]:15s} | Type1: {p[2]:2d} ({p[3]:10s}) | Type2: {type2_str}")

conn.close()
