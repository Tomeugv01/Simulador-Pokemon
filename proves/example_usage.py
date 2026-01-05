"""
Ejemplo de uso de los Repositories para acceder a datos.
"""

from src.repositories import PokemonRepository, MoveRepository, EffectRepository

def example_pokemon_queries():
    """Ejemplos de consultas de Pokemon"""
    print("=" * 60)
    print("EJEMPLOS DE CONSULTAS DE POKEMON")
    print("=" * 60)
    
    repo = PokemonRepository()
    
    # 1. Obtener un Pokemon por ID
    print("\n1. Obtener Pikachu por ID (25):")
    pikachu = repo.get_by_id(25)
    if pikachu:
        print(f"   {pikachu['name']} - {pikachu['type1']}")
        print(f"   HP: {pikachu['hp']}, Attack: {pikachu['attack']}, Speed: {pikachu['speed']}")
        print(f"   Curva de experiencia: {pikachu['exp_curve']}")
    
    # 2. Obtener un Pokemon por nombre
    print("\n2. Obtener Charizard por nombre:")
    charizard = repo.get_by_name('Charizard')
    if charizard:
        print(f"   #{charizard['id']} - {charizard['name']}")
        print(f"   Tipos: {charizard['type1']}/{charizard['type2']}")
        print(f"   Stats totales: {charizard['total_stats']}")
    
    # 3. Buscar Pokemon por tipo
    print("\n3. Buscar Pokemon de tipo Dragon:")
    dragons = repo.search_by_type('Dragon')
    print(f"   Encontrados {len(dragons)} Pokemon tipo Dragon:")
    for poke in dragons[:5]:  # Solo primeros 5
        print(f"   - {poke['name']} (Total: {poke['total_stats']})")
    
    # 4. Obtener todos los Pokemon ordenados por stats
    print("\n4. Top 5 Pokemon más poderosos:")
    all_pokemon = repo.get_all(order_by='total_stats')
    for poke in all_pokemon[-5:]:  # Últimos 5 (más poderosos)
        types = f"{poke['type1']}/{poke['type2']}" if poke['type2'] else poke['type1']
        print(f"   {poke['name']:15s} - {types:20s} (Stats: {poke['total_stats']})")


def example_move_queries():
    """Ejemplos de consultas de Movimientos"""
    print("\n" + "=" * 60)
    print("EJEMPLOS DE CONSULTAS DE MOVIMIENTOS")
    print("=" * 60)
    
    repo = MoveRepository()
    
    # 1. Obtener un movimiento con sus efectos
    print("\n1. Obtener Thunderbolt (ID 85) con sus efectos:")
    thunderbolt = repo.get_with_effects(85)
    if thunderbolt:
        print(f"   {thunderbolt['name']}")
        print(f"   Tipo: {thunderbolt['type']}, Categoría: {thunderbolt['category']}")
        print(f"   Poder: {thunderbolt['power']}, Precisión: {thunderbolt['accuracy']}, PP: {thunderbolt['pp']}")
        print(f"   Efectos ({len(thunderbolt['effects'])}):")
        for effect in thunderbolt['effects']:
            print(f"      - {effect['effect_name']} ({effect['probability']}% chance)")
    
    # 2. Buscar movimientos por tipo
    print("\n2. Movimientos de tipo Fire (primeros 5):")
    fire_moves = repo.search_by_type('Fire')
    for move in fire_moves[:5]:
        power = move['power'] if move['power'] else 'N/A'
        print(f"   - {move['name']:20s} | Poder: {power:3} | PP: {move['pp']}")
    
    # 3. Buscar movimientos por categoría
    print("\n3. Movimientos de estado (Status) - primeros 5:")
    status_moves = repo.search_by_category('Status')
    for move in status_moves[:5]:
        print(f"   - {move['name']:20s} | PP: {move['pp']} | Target: {move['target_type']}")
    
    # 4. Movimientos más poderosos
    print("\n4. Top 5 movimientos más poderosos:")
    all_moves = repo.get_all(order_by='power')
    powerful_moves = [m for m in all_moves if m['power'] is not None][-5:]
    for move in powerful_moves:
        print(f"   {move['name']:20s} - Poder: {move['power']}, Tipo: {move['type']}")


def example_effect_queries():
    """Ejemplos de consultas de Efectos"""
    print("\n" + "=" * 60)
    print("EJEMPLOS DE CONSULTAS DE EFECTOS")
    print("=" * 60)
    
    repo = EffectRepository()
    
    # 1. Obtener un efecto por ID
    print("\n1. Obtener efecto de paralización (ID 5):")
    effect = repo.get_by_id(5)
    if effect:
        print(f"   {effect['name']}")
        print(f"   Descripción: {effect['description']}")
    
    # 2. Ver todos los efectos de un movimiento
    print("\n2. Efectos del movimiento Thunderbolt (ID 85):")
    effects = repo.get_effects_for_move(85)
    for effect in effects:
        print(f"   - {effect['effect_name']}: {effect['description']} ({effect['probability']}%)")
    
    # 3. Ver qué movimientos tienen un efecto específico
    print("\n3. Movimientos que causan quemadura (Burn 10%, ID 1):")
    moves = repo.get_moves_with_effect(1)
    print(f"   Encontrados {len(moves)} movimientos con este efecto (primeros 5):")
    for move in moves[:5]:
        print(f"   - {move['move_name']:20s} | Tipo: {move['type']:10s} | {move['probability']}% chance")
    
    # 4. Listar todos los efectos
    print("\n4. Primeros 10 efectos disponibles:")
    all_effects = repo.get_all()
    for effect in all_effects[:10]:
        print(f"   {effect['id']:3d}. {effect['name']}")


def example_combined_queries():
    """Ejemplos de consultas combinadas"""
    print("\n" + "=" * 60)
    print("EJEMPLOS DE CONSULTAS COMBINADAS")
    print("=" * 60)
    
    poke_repo = PokemonRepository()
    move_repo = MoveRepository()
    
    # 1. Pokemon y sus posibles movimientos del mismo tipo
    print("\n1. Charizard y movimientos de tipo Fire:")
    charizard = poke_repo.get_by_name('Charizard')
    if charizard:
        fire_moves = move_repo.search_by_type(charizard['type1'])
        print(f"   {charizard['name']} puede aprender {len(fire_moves)} movimientos de tipo {charizard['type1']}")
        print(f"   Algunos ejemplos (con poder):")
        powerful_fire = [m for m in fire_moves if m['power'] and m['power'] > 80][:5]
        for move in powerful_fire:
            print(f"      - {move['name']:20s} (Poder: {move['power']})")
    
    # 2. Pokemon más rápidos
    print("\n2. Los 5 Pokemon más rápidos:")
    all_pokemon = poke_repo.get_all(order_by='speed')
    fastest = all_pokemon[-5:]
    for poke in fastest:
        print(f"   {poke['name']:15s} - Speed: {poke['speed']:3d} | {poke['type1']}")


if __name__ == "__main__":
    # Ejecutar todos los ejemplos
    example_pokemon_queries()
    example_move_queries()
    example_effect_queries()
    example_combined_queries()
    
    print("\n" + "=" * 60)
    print("✅ Todos los ejemplos ejecutados correctamente")
    print("=" * 60)
