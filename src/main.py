try:
    from .database import DatabaseManager, get_all_moves, get_move_details, search_moves_by_type
except ImportError:
    from database import DatabaseManager, get_all_moves, get_move_details, search_moves_by_type

def display_move(move):
    """Display a single move in a formatted way"""
    move_id, name, move_type, category, pp, power, accuracy, causes_damage, makes_contact, priority, target_type, description = move
    
    print(f"ID: {move_id:3} | {name:20} | Type: {move_type:10} | Category: {category:8} | ", end="")
    if power:
        print(f"Power: {power:3} | ", end="")
    else:
        print(f"Power: N/A | ", end="")
    
    if accuracy:
        print(f"Accuracy: {accuracy:3}")
    else:
        print(f"Accuracy: N/A")
    
    print(f"     PP: {pp} | Contact: {makes_contact} | Priority: {priority} | Target: {target_type}")
    print(f"     {description}")

def display_move_with_effects(move_details):
    """Display a move with all its effects"""
    move = move_details['move']
    effects = move_details['effects']
    
    display_move(move)
    
    if effects:
        print("\n     Effects:")
        for effect in effects:
            effect_name, effect_desc, effect_type, status_cond, stat_change, stat_amount, heal_pct, recoil_pct, weather_type, field_cond, probability, order, triggers_on = effect
            print(f"       [{order}] {effect_name} ({probability}% chance)")
            print(f"           {effect_desc}")
            if status_cond and status_cond != 'None':
                print(f"           Status: {status_cond}")
            if stat_change and stat_amount != 0:
                change_type = "Raises" if stat_amount > 0 else "Lowers"
                print(f"           {change_type} {stat_change} by {abs(stat_amount)} stage(s)")
            if heal_pct > 0:
                print(f"           Heals: {heal_pct}%")
            if recoil_pct > 0:
                print(f"           Recoil: {recoil_pct}%")
            if weather_type and weather_type != 'None':
                print(f"           Weather: {weather_type}")
            if field_cond:
                print(f"           Field: {field_cond}")
            print(f"           Triggers: {triggers_on}")
    else:
        print("\n     No additional effects")

def list_all_moves():
    """Display all moves"""
    moves = get_all_moves()
    print(f"\nFound {len(moves)} moves:")
    print("-" * 80)
    
    for move in moves:
        display_move(move)
        print("-" * 80)

def search_move_by_id():
    """Search for a move by ID"""
    try:
        move_id = int(input("Enter move ID: "))
        move_details = get_move_details(move_id)
        
        if move_details:
            print(f"\nMove Details:")
            print("=" * 80)
            display_move_with_effects(move_details)
            print("=" * 80)
        else:
            print(f"Move with ID {move_id} not found.")
    except ValueError:
        print("Please enter a valid number.")

def search_move_by_name():
    """Search for moves by name"""
    name = input("Enter move name (or part of name): ").strip()
    if not name:
        print("Please enter a name to search for.")
        return
    
    db = DatabaseManager()
    conn = db.get_connection()
    cursor = conn.cursor()
    
    cursor.execute('SELECT * FROM moves WHERE name LIKE ? ORDER BY name', (f'%{name}%',))
    moves = cursor.fetchall()
    conn.close()
    
    if moves:
        print(f"\nFound {len(moves)} moves matching '{name}':")
        print("=" * 80)
        for move in moves:
            display_move(move)
            print("-" * 80)
    else:
        print(f"No moves found matching '{name}'.")

def search_moves_by_type_menu():
    """Search moves by type"""
    types = [
        'Normal', 'Fire', 'Water', 'Electric', 'Grass', 'Ice', 'Fighting', 'Poison',
        'Ground', 'Flying', 'Psychic', 'Bug', 'Rock', 'Ghost', 'Dragon', 'Dark', 'Steel', 'Fairy'
    ]
    
    print("\nAvailable types:")
    for i, type_name in enumerate(types, 1):
        print(f"{i:2}. {type_name}")
    
    try:
        choice = int(input("\nSelect type (1-18): "))
        if 1 <= choice <= 18:
            selected_type = types[choice - 1]
            moves = search_moves_by_type(selected_type)
            
            print(f"\nFound {len(moves)} {selected_type}-type moves:")
            print("=" * 80)
            for move in moves:
                display_move(move)
                print("-" * 80)
        else:
            print("Invalid choice. Please select 1-18.")
    except ValueError:
        print("Please enter a valid number.")

def main():
    """Main application loop"""
    print("=== Pokemon Battle Move Database ===")
    
    # Check if database exists, only initialize if it doesn't
    import os
    if not os.path.exists("data/pokemon_battle.db"):
        db = DatabaseManager()
        db.initialize_database()
    
    while True:
        print("\nOptions:")
        print("1. List all moves")
        print("2. Search move by ID")
        print("3. Search move by name")
        print("4. Search moves by type")
        print("5. Exit")
        
        choice = input("\nEnter your choice (1-5): ").strip()
        
        if choice == '1':
            list_all_moves()
        elif choice == '2':
            search_move_by_id()
        elif choice == '3':
            search_move_by_name()
        elif choice == '4':
            search_moves_by_type_menu()
        elif choice == '5':
            print("Goodbye!")
            break
        else:
            print("Invalid choice. Please enter 1-5.")

if __name__ == "__main__":
    main()