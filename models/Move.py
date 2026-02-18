"""
Move class for Pokemon battle system.
Represents a Pokemon move with all its properties and effects.
"""

try:
    from constants import TYPE_NAMES as _TYPE_NAMES, get_type_name as _get_type_name
except ImportError:
    from models.constants import TYPE_NAMES as _TYPE_NAMES, get_type_name as _get_type_name


class Move:
    # Type data from shared constants module
    TYPE_NAMES = _TYPE_NAMES

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

    # *** PUBLIC ***

    def can_use(self):
        """Check if move has PP remaining"""
        return self.pp_current > 0

    def copy(self):
        """Create a copy of this move instance"""
        import copy
        # Create a shallow copy
        new_move = copy.copy(self)
        # Ensure effects list is also copied (list of dicts)
        if hasattr(self, 'effects'):
            new_move.effects = [e.copy() for e in self.effects]
        return new_move

    def get(self, key, default=None):
        """Allow dict.get() style access for compatibility"""
        if key == 'pp':
            return self.pp_max
        return getattr(self, key, default)

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

    def get_effects_by_type(self, effect_type):
        """
        Get all effects of a specific type.
        
        Args:
            effect_type (str): Effect type to filter by
        
        Returns:
            list: List of matching effects
        """
        return [eff for eff in self.effects if eff.get('effect_type') == effect_type]

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

    # *** PUBLIC STATIC ***

    @staticmethod
    def get_type_name(type_id):
        """Convert type ID to type name"""
        return _get_type_name(type_id)

    # *** DUNDER METHODS ***

    def __getitem__(self, key):
        """Allow dictionary-style access for compatibility"""
        if key == 'pp':
            return self.pp_max
        return getattr(self, key, None)

    def __repr__(self):
        power_str = f"Pwr:{self.power}" if self.power else "Status"
        return f"{self.name} ({power_str}, {self.pp_current}/{self.pp_max} PP)"

    def __str__(self):
        return self.__repr__()
