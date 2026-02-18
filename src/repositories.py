"""
Repository classes for database queries.
Provides clean interfaces to access Pokemon, Moves, and Effects data.
"""

import sqlite3
from pathlib import Path

try:
    from .database import DatabaseManager
except ImportError:
    from database import DatabaseManager


class PokemonRepository:
    """Repository for Pokemon data access"""

    def __init__(self, db_path="data/pokemon_battle.db"):
        self.db_manager = DatabaseManager(db_path)
        self.db_path = db_path

    # *** PUBLIC ***
    # region Getters

    def get_abilities(self, pokemon_id):
        """
        Get all abilities for a Pokemon, including hidden abilities.
        
        Args:
            pokemon_id (int): The Pokemon's ID
            
        Returns:
            list: List of ability dicts with 'id', 'name', 'description', 'is_hidden', 'slot'
        """
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT a.id, a.name, a.description, pa.is_hidden, pa.slot
            FROM pokemon_abilities pa
            JOIN abilities a ON pa.ability_id = a.id
            WHERE pa.pokemon_id = ?
            ORDER BY pa.is_hidden, pa.slot
        ''', (pokemon_id,))
        
        rows = cursor.fetchall()
        conn.close()
        
        return [
            {
                'id': row[0],
                'name': row[1],
                'description': row[2],
                'is_hidden': bool(row[3]),
                'slot': row[4]
            }
            for row in rows
        ]

    def get_all(self, order_by='id'):
        """
        Get all Pokemon.
        
        Args:
            order_by (str): Field to order by (id, name, total_stats)
            
        Returns:
            list: List of Pokemon dictionaries
        """
        conn = self.get_connection()
        cursor = conn.cursor()
        
        valid_orders = ['id', 'name', 'total_stats', 'speed', 'attack']
        if order_by not in valid_orders:
            order_by = 'id'
        
        cursor.execute(f'''
            SELECT id, name, type1, type2, hp, attack, defense, 
                   special_attack, special_defense, speed, total_stats,
                   evolution_level, exp_curve
            FROM pokemon 
            ORDER BY {order_by}
        ''')
        
        rows = cursor.fetchall()
        conn.close()
        
        return [
            {
                'id': row[0],
                'name': row[1],
                'type1': row[2],
                'type2': row[3],
                'hp': row[4],
                'attack': row[5],
                'defense': row[6],
                'special_attack': row[7],
                'special_defense': row[8],
                'speed': row[9],
                'total_stats': row[10],
                'evolution_level': row[11],
                'exp_curve': row[12]
            }
            for row in rows
        ]

    def get_by_id(self, pokemon_id):
        """
        Get a Pokemon by its ID with all its information.
        
        Args:
            pokemon_id (int): The Pokemon's ID (1-151)
            
        Returns:
            dict: Pokemon data or None if not found
        """
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id, name, type1, type2, hp, attack, defense, 
                   special_attack, special_defense, speed, total_stats,
                   evolution_level, exp_curve
            FROM pokemon 
            WHERE id = ?
        ''', (pokemon_id,))
        
        row = cursor.fetchone()
        conn.close()
        
        if not row:
            return None
        
        return {
            'id': row[0],
            'name': row[1],
            'type1': row[2],
            'type2': row[3],
            'hp': row[4],
            'attack': row[5],
            'defense': row[6],
            'special_attack': row[7],
            'special_defense': row[8],
            'speed': row[9],
            'total_stats': row[10],
            'evolution_level': row[11],
            'exp_curve': row[12]
        }

    def get_by_name(self, name):
        """
        Get a Pokemon by its name.
        
        Args:
            name (str): The Pokemon's name
            
        Returns:
            dict: Pokemon data or None if not found
        """
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id, name, type1, type2, hp, attack, defense, 
                   special_attack, special_defense, speed, total_stats,
                   evolution_level, exp_curve
            FROM pokemon 
            WHERE name = ?
        ''', (name,))
        
        row = cursor.fetchone()
        conn.close()
        
        if not row:
            return None
        
        return {
            'id': row[0],
            'name': row[1],
            'type1': row[2],
            'type2': row[3],
            'hp': row[4],
            'attack': row[5],
            'defense': row[6],
            'special_attack': row[7],
            'special_defense': row[8],
            'speed': row[9],
            'total_stats': row[10],
            'evolution_level': row[11],
            'exp_curve': row[12]
        }

    def get_connection(self):
        """Get database connection"""
        return self.db_manager.get_connection()

    def get_evolution_chain(self, pokemon_id):
        """
        Get the evolution chain for a Pokemon.
        
        Args:
            pokemon_id (int): The Pokemon's ID
            
        Returns:
            list: List of Pokemon in the evolution chain
        """
        # This is a simplified version - you might need more complex logic
        # based on how evolution data is structured
        pokemon = self.get_by_id(pokemon_id)
        if not pokemon:
            return []
        
        # For now, just return the pokemon itself
        # TODO: Implement full evolution chain logic
        return [pokemon]

    # endregion Getters

    def search_by_type(self, pokemon_type):
        """
        Search Pokemon by type (primary or secondary).
        
        Args:
            pokemon_type (str): The type to search for
            
        Returns:
            list: List of Pokemon with that type
        """
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id, name, type1, type2, hp, attack, defense, 
                   special_attack, special_defense, speed, total_stats,
                   evolution_level, exp_curve
            FROM pokemon 
            WHERE type1 = ? OR type2 = ?
            ORDER BY name
        ''', (pokemon_type, pokemon_type))
        
        rows = cursor.fetchall()
        conn.close()
        
        return [
            {
                'id': row[0],
                'name': row[1],
                'type1': row[2],
                'type2': row[3],
                'hp': row[4],
                'attack': row[5],
                'defense': row[6],
                'special_attack': row[7],
                'special_defense': row[8],
                'speed': row[9],
                'total_stats': row[10],
                'evolution_level': row[11],
                'exp_curve': row[12]
            }
            for row in rows
        ]


class MoveRepository:
    """Repository for Move data access"""

    def __init__(self, db_path="data/pokemon_battle.db"):
        self.db_manager = DatabaseManager(db_path)
        self.db_path = db_path

    # *** PUBLIC ***
    # region Getters

    def get_all(self, order_by='id'):
        """
        Get all Moves.
        
        Args:
            order_by (str): Field to order by (id, name, power, type)
            
        Returns:
            list: List of Move dictionaries
        """
        conn = self.get_connection()
        cursor = conn.cursor()
        
        valid_orders = ['id', 'name', 'power', 'type', 'category']
        if order_by not in valid_orders:
            order_by = 'id'
        
        cursor.execute(f'''
            SELECT id, name, type, category, pp, power, accuracy, 
                   causes_damage, makes_contact, priority, target_type, description
            FROM moves 
            ORDER BY {order_by}
        ''')
        
        rows = cursor.fetchall()
        conn.close()
        
        return [
            {
                'id': row[0],
                'name': row[1],
                'type': row[2],
                'category': row[3],
                'pp': row[4],
                'power': row[5],
                'accuracy': row[6],
                'causes_damage': row[7],
                'makes_contact': row[8],
                'priority': row[9],
                'target_type': row[10],
                'description': row[11]
            }
            for row in rows
        ]

    def get_by_id(self, move_id):
        """
        Get a Move by its ID.
        
        Args:
            move_id (int): The Move's ID
            
        Returns:
            dict: Move data or None if not found
        """
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id, name, type, category, pp, power, accuracy, 
                   causes_damage, makes_contact, priority, target_type, description
            FROM moves 
            WHERE id = ?
        ''', (move_id,))
        
        row = cursor.fetchone()
        conn.close()
        
        if not row:
            return None
        
        return {
            'id': row[0],
            'name': row[1],
            'type': row[2],
            'category': row[3],
            'pp': row[4],
            'power': row[5],
            'accuracy': row[6],
            'causes_damage': row[7],
            'makes_contact': row[8],
            'priority': row[9],
            'target_type': row[10],
            'description': row[11]
        }

    def get_connection(self):
        """Get database connection"""
        return self.db_manager.get_connection()

    def get_with_effects(self, move_id):
        """
        Get a Move with all its effects.
        
        Args:
            move_id (int): The Move's ID
            
        Returns:
            dict: Move data with effects list or None if not found
        """
        move = self.get_by_id(move_id)
        if not move:
            return None
        
        # Get effects for this move with all necessary fields
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT me.id, me.name, me.description, me.effect_type, me.effect_target,
                   me.status_condition, me.stat_to_change, me.stat_change_amount,
                   me.heal_percentage, me.heal_fixed_amount, me.recoil_percentage,
                   me.weather_type, me.field_condition, 
                   mei.probability, mei.effect_order, mei.triggers_on
            FROM move_effect_instances mei
            JOIN move_effects me ON mei.effect_id = me.id
            WHERE mei.move_id = ?
            ORDER BY mei.effect_order
        ''', (move_id,))
        
        effects = []
        for row in cursor.fetchall():
            effects.append({
                'effect_id': row[0],
                'effect_name': row[1],
                'description': row[2],
                'effect_type': row[3],
                'effect_target': row[4],
                'status_condition': row[5],
                'stat_to_change': row[6],
                'stat_change_amount': row[7],
                'heal_percentage': row[8],
                'heal_fixed_amount': row[9],
                'recoil_percentage': row[10],
                'weather_type': row[11],
                'field_condition': row[12],
                'probability': row[13],
                'effect_order': row[14],
                'triggers_on': row[15]
            })
        
        conn.close()
        
        move['effects'] = effects
        return move

    # endregion Getters

    def search_by_category(self, category):
        """
        Search Moves by category (Physical, Special, Status).
        
        Args:
            category (str): The category to search for
            
        Returns:
            list: List of Moves with that category
        """
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id, name, type, category, pp, power, accuracy, 
                   causes_damage, makes_contact, priority, target_type, description
            FROM moves 
            WHERE category = ?
            ORDER BY name
        ''', (category,))
        
        rows = cursor.fetchall()
        conn.close()
        
        return [
            {
                'id': row[0],
                'name': row[1],
                'type': row[2],
                'category': row[3],
                'pp': row[4],
                'power': row[5],
                'accuracy': row[6],
                'causes_damage': row[7],
                'makes_contact': row[8],
                'priority': row[9],
                'target_type': row[10],
                'description': row[11]
            }
            for row in rows
        ]

    def search_by_type(self, move_type):
        """
        Search Moves by type.
        
        Args:
            move_type (str): The type to search for
            
        Returns:
            list: List of Moves with that type
        """
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id, name, type, category, pp, power, accuracy, 
                   causes_damage, makes_contact, priority, target_type, description
            FROM moves 
            WHERE type = ?
            ORDER BY name
        ''', (move_type,))
        
        rows = cursor.fetchall()
        conn.close()
        
        return [
            {
                'id': row[0],
                'name': row[1],
                'type': row[2],
                'category': row[3],
                'pp': row[4],
                'power': row[5],
                'accuracy': row[6],
                'causes_damage': row[7],
                'makes_contact': row[8],
                'priority': row[9],
                'target_type': row[10],
                'description': row[11]
            }
            for row in rows
        ]


class EffectRepository:
    """Repository for Effect data access"""

    def __init__(self, db_path="data/pokemon_battle.db"):
        self.db_manager = DatabaseManager(db_path)
        self.db_path = db_path

    # *** PUBLIC ***
    # region Getters

    def get_all(self):
        """
        Get all Effects.
        
        Returns:
            list: List of Effect dictionaries
        """
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id, name, description
            FROM move_effects 
            ORDER BY name
        ''')
        
        rows = cursor.fetchall()
        conn.close()
        
        return [
            {
                'id': row[0],
                'name': row[1],
                'description': row[2]
            }
            for row in rows
        ]

    def get_by_id(self, effect_id):
        """
        Get an Effect by its ID.
        
        Args:
            effect_id (int): The Effect's ID
            
        Returns:
            dict: Effect data or None if not found
        """
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id, name, description
            FROM move_effects 
            WHERE id = ?
        ''', (effect_id,))
        
        row = cursor.fetchone()
        conn.close()
        
        if not row:
            return None
        
        return {
            'id': row[0],
            'name': row[1],
            'description': row[2]
        }

    def get_connection(self):
        """Get database connection"""
        return self.db_manager.get_connection()

    def get_effects_for_move(self, move_id):
        """
        Get all effects for a specific move.
        
        Args:
            move_id (int): The Move's ID
            
        Returns:
            list: List of effects with probability
        """
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT me.id, me.name, me.description, mei.probability
            FROM move_effect_instances mei
            JOIN move_effects me ON mei.effect_id = me.id
            WHERE mei.move_id = ?
            ORDER BY mei.probability DESC
        ''', (move_id,))
        
        rows = cursor.fetchall()
        conn.close()
        
        return [
            {
                'effect_id': row[0],
                'effect_name': row[1],
                'description': row[2],
                'probability': row[3]
            }
            for row in rows
        ]

    def get_moves_with_effect(self, effect_id):
        """
        Get all moves that have a specific effect.
        
        Args:
            effect_id (int): The Effect's ID
            
        Returns:
            list: List of moves with this effect
        """
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT m.id, m.name, m.type, m.category, m.pp, m.power, 
                   m.accuracy, mei.probability
            FROM move_effect_instances mei
            JOIN moves m ON mei.move_id = m.id
            WHERE mei.effect_id = ?
            ORDER BY m.name
        ''', (effect_id,))
        
        rows = cursor.fetchall()
        conn.close()
        
        return [
            {
                'move_id': row[0],
                'move_name': row[1],
                'type': row[2],
                'category': row[3],
                'pp': row[4],
                'power': row[5],
                'accuracy': row[6],
                'probability': row[7]
            }
            for row in rows
        ]

    # endregion Getters


def get_effect(effect_id):
    """Quick function to get an Effect by ID"""
    repo = EffectRepository()
    return repo.get_by_id(effect_id)


def get_move(move_id, with_effects=True):
    """Quick function to get a Move by ID"""
    repo = MoveRepository()
    if with_effects:
        return repo.get_with_effects(move_id)
    return repo.get_by_id(move_id)


# Convenience functions for quick access
def get_pokemon(pokemon_id):
    """Quick function to get a Pokemon by ID"""
    repo = PokemonRepository()
    return repo.get_by_id(pokemon_id)


# Example usage and testing
if __name__ == "__main__":
    print("=== Testing Pokemon Repository ===")
    pokemon_repo = PokemonRepository()
    
    # Test get by ID
    pikachu = pokemon_repo.get_by_id(25)
    if pikachu:
        print(f"\nPokemon #{pikachu['id']}: {pikachu['name']}")
        print(f"  Type: {pikachu['type1']}")
        print(f"  HP: {pikachu['hp']} | Attack: {pikachu['attack']} | Speed: {pikachu['speed']}")
        print(f"  Exp Curve: {pikachu['exp_curve']}")
    
    # Test get by name
    charizard = pokemon_repo.get_by_name('Charizard')
    if charizard:
        print(f"\nPokemon: {charizard['name']}")
        print(f"  Types: {charizard['type1']}/{charizard['type2']}")
        print(f"  Total Stats: {charizard['total_stats']}")
    
    # Test search by type
    fire_types = pokemon_repo.search_by_type('Fire')
    print(f"\n{len(fire_types)} Fire-type Pokemon found")
    
    print("\n=== Testing Move Repository ===")
    move_repo = MoveRepository()
    
    # Test get move with effects
    thunderbolt = move_repo.get_with_effects(85)  # Thunderbolt
    if thunderbolt:
        print(f"\nMove: {thunderbolt['name']}")
        print(f"  Type: {thunderbolt['type']} | Power: {thunderbolt['power']} | Accuracy: {thunderbolt['accuracy']}")
        print(f"  Effects: {len(thunderbolt['effects'])}")
        for effect in thunderbolt['effects']:
            print(f"    - {effect['effect_name']} ({effect['probability']}%)")
    
    print("\n=== Testing Effect Repository ===")
    effect_repo = EffectRepository()
    
    # Test get effect by ID
    effect = effect_repo.get_by_id(1)
    if effect:
        print(f"\nEffect: {effect['name']}")
        print(f"  Description: {effect['description']}")
        
        # Get moves with this effect
        moves_with_effect = effect_repo.get_moves_with_effect(1)
        print(f"  Used by {len(moves_with_effect)} moves")
