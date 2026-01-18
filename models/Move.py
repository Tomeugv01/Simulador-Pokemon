"""
Move class for Pokemon battle system.
Represents a Pokemon move with all its properties and effects.
"""


class Move:
    # Type ID to name mapping
    TYPE_NAMES = {
        1: 'Normal', 2: 'Fire', 3: 'Water', 4: 'Electric', 5: 'Grass',
        6: 'Ice', 7: 'Fighting', 8: 'Poison', 9: 'Ground', 10: 'Flying',
        11: 'Psychic', 12: 'Bug', 13: 'Rock', 14: 'Ghost', 15: 'Dragon',
        16: 'Dark', 17: 'Steel', 18: 'Fairy'
    }
    
    @staticmethod
    def get_type_name(type_id):
        """Convert type ID to type name"""
        if isinstance(type_id, str):
            return type_id  # Already a name
        return Move.TYPE_NAMES.get(type_id, 'Unknown')
    """
    Move class representing a Pokemon move with all its properties and effects.
    """
    
    def __init__(self, move_data):
        """
        Create a Move instance from database data.
        
        Args:
            move_data (dict): Move data from MoveRepository.get_with_effects()
        """
        # Basic properties
        self.id = move_data['id']
        self.name = move_data['name']
        self.type = Move.get_type_name(move_data['type'])
        self.category = move_data['category']  # 'Physical', 'Special', 'Status'
        self.power = move_data['power']
        self.accuracy = move_data['accuracy']
        self.pp_max = move_data['pp']
        self.pp_current = self.pp_max
        self.priority = move_data['priority']
        self.target_type = move_data['target_type']
        self.description = move_data['description']
        
        # Battle properties
        self.causes_damage = move_data['causes_damage']
        self.makes_contact = move_data['makes_contact']
        
        # Effects
        self.effects = move_data.get('effects', [])
    
    def can_use(self):
        """Check if move has PP remaining"""
        return self.pp_current > 0
    
    def use(self):
        """
        Use the move (decrement PP).
        
        Returns:
            bool: True if move was used, False if no PP
        """
        if not self.can_use():
            return False
        
        self.pp_current -= 1
        return True
    
    def restore_pp(self, amount=None):
        """
        Restore PP.
        
        Args:
            amount (int): Amount to restore (None = restore to max)
        
        Returns:
            int: Actual PP restored
        """
        old_pp = self.pp_current
        
        if amount is None:
            self.pp_current = self.pp_max
        else:
            self.pp_current = min(self.pp_max, self.pp_current + amount)
        
        return self.pp_current - old_pp
    
    def get_effect_by_name(self, effect_name):
        """
        Get a specific effect from this move.
        
        Args:
            effect_name (str): Name of effect to find
        
        Returns:
            dict: Effect data or None
        """
        for effect in self.effects:
            if effect['effect_name'] == effect_name:
                return effect
        return None
    
    def has_effect(self, effect_name):
        """Check if move has a specific effect"""
        return self.get_effect_by_name(effect_name) is not None
    
    def has_effect_type(self, effect_type):
        """
        Check if move has any effect of the specified type.
        
        Args:
            effect_type (str): Effect type to check (STATUS, STAT_CHANGE, HEAL, etc.)
        
        Returns:
            bool: True if move has at least one effect of that type
        """
        return any(eff.get('effect_type') == effect_type for eff in self.effects)
    
    def get_effects_by_type(self, effect_type):
        """
        Get all effects of a specific type.
        
        Args:
            effect_type (str): Effect type to filter by
        
        Returns:
            list: List of matching effects
        """
        return [eff for eff in self.effects if eff.get('effect_type') == effect_type]
    
    def is_damaging(self):
        """Check if move deals damage"""
        return self.causes_damage and self.power is not None and self.power > 0
    
    def is_physical(self):
        """Check if move is physical category"""
        return self.category == 'Physical'
    
    def is_special(self):
        """Check if move is special category"""
        return self.category == 'Special'
    
    def is_status(self):
        """Check if move is status category"""
        return self.category == 'Status'

    def copy(self):
        """Create a copy of this move instance"""
        import copy
        # Create a shallow copy
        new_move = copy.copy(self)
        # Ensure effects list is also copied (list of dicts)
        if hasattr(self, 'effects'):
            new_move.effects = [e.copy() for e in self.effects]
        return new_move
    
    def __getitem__(self, key):
        """Allow dictionary-style access for compatibility"""
        if key == 'pp':
            return self.pp_max
        return getattr(self, key, None)
    
    def get(self, key, default=None):
        """Allow dict.get() style access for compatibility"""
        if key == 'pp':
            return self.pp_max
        return getattr(self, key, default)
    
    def __repr__(self):
        power_str = f"Pwr:{self.power}" if self.power else "Status"
        return f"{self.name} ({power_str}, {self.pp_current}/{self.pp_max} PP)"
    
    def __str__(self):
        return self.__repr__()
