"""
Model classes for Pokemon battle system.
Contains Pokemon and Move classes with battle mechanics.
"""

try:
    from .repositories import PokemonRepository, MoveRepository
except ImportError:
    from repositories import PokemonRepository, MoveRepository


class Pokemon:
    """
    Pokemon class representing a battle-ready Pokemon instance.
    Handles stats calculation, HP management, status conditions, and stat stages.
    """
    
    def __init__(self, pokemon_id, level=50, moveset=None, ivs=None, evs=None):
        """
        Create a Pokemon instance.
        
        Args:
            pokemon_id (int): Pokemon ID from database (1-151)
            level (int): Pokemon level (1-100), default 50 for competitive
            moveset (list): List of move IDs (max 4), e.g., [85, 93, 99, 12]
            ivs (dict): Individual Values (0-31) for each stat, optional
            evs (dict): Effort Values (0-255, max 510 total) for each stat, optional
        
        Example:
            pikachu = Pokemon(25, level=50, moveset=[85, 93, 99, 12])
        """
        # Load base data from database
        repo = PokemonRepository()
        base_data = repo.get_by_id(pokemon_id)
        
        if not base_data:
            raise ValueError(f"Pokemon with ID {pokemon_id} does not exist in database")
        
        # Immutable base data
        self.id = base_data['id']
        self.name = base_data['name']
        self.type1 = base_data['type1']
        self.type2 = base_data['type2']
        self.base_hp = base_data['hp']
        self.base_attack = base_data['attack']
        self.base_defense = base_data['defense']
        self.base_sp_attack = base_data['special_attack']
        self.base_sp_defense = base_data['special_defense']
        self.base_speed = base_data['speed']
        self.evolution_level = base_data['evolution_level']
        self.exp_curve = base_data['exp_curve']
        
        # IVs and EVs (for more advanced stat calculation)
        self.ivs = ivs or {
            'hp': 31, 'attack': 31, 'defense': 31,
            'sp_attack': 31, 'sp_defense': 31, 'speed': 31
        }
        self.evs = evs or {
            'hp': 0, 'attack': 0, 'defense': 0,
            'sp_attack': 0, 'sp_defense': 0, 'speed': 0
        }
        
        # Level
        self.level = max(1, min(100, level))
        
        # Calculate stats
        self.max_hp = self._calculate_hp_stat()
        self.current_hp = self.max_hp
        self.attack = self._calculate_stat('attack')
        self.defense = self._calculate_stat('defense')
        self.sp_attack = self._calculate_stat('sp_attack')
        self.sp_defense = self._calculate_stat('sp_defense')
        self.speed = self._calculate_stat('speed')
        
        # Battle status
        self.status = None  # 'burn', 'paralysis', 'poison', 'badly_poison', 'sleep', 'freeze'
        self.sleep_turns = 0  # Remaining sleep turns
        self.toxic_counter = 0  # For badly poison damage calculation
        self.fainted = False
        
        # Stat stages (modifiers from -6 to +6)
        self.stat_stages = {
            'attack': 0,
            'defense': 0,
            'sp_attack': 0,
            'sp_defense': 0,
            'speed': 0,
            'accuracy': 0,
            'evasion': 0
        }
        
        # Volatile battle conditions
        self.confused = False
        self.confusion_turns = 0
        self.flinched = False  # Reset each turn
        self.charging = False  # For moves like Solar Beam
        self.recharging = False  # For moves like Hyper Beam
        self.trapped = False  # From moves like Bind, Wrap
        self.seeded = False  # Leech Seed
        self.protected = False  # Protect/Detect
        
        # Moves
        self.moves = []
        if moveset:
            self._load_moves(moveset)
    
    def _calculate_hp_stat(self):
        """
        Calculate max HP stat.
        Gen 1-2 Formula: floor(((Base + IV) * 2 + floor(sqrt(EV) / 4)) * Level / 100) + Level + 10
        Simplified: ((Base * 2 + IV + EV/4) * Level / 100) + Level + 10
        """
        base = self.base_hp
        iv = self.ivs['hp']
        ev = self.evs['hp'] // 4
        
        return int(((base * 2 + iv + ev) * self.level / 100) + self.level + 10)
    
    def _calculate_stat(self, stat_name):
        """
        Calculate non-HP stat.
        Gen 1-2 Formula: floor(((Base + IV) * 2 + floor(sqrt(EV) / 4)) * Level / 100) + 5
        """
        base_map = {
            'attack': self.base_attack,
            'defense': self.base_defense,
            'sp_attack': self.base_sp_attack,
            'sp_defense': self.base_sp_defense,
            'speed': self.base_speed
        }
        
        base = base_map[stat_name]
        iv = self.ivs[stat_name]
        ev = self.evs[stat_name] // 4
        
        return int(((base * 2 + iv + ev) * self.level / 100) + 5)
    
    def get_effective_stat(self, stat_name):
        """
        Get stat with stage modifiers applied.
        Stage multipliers: (2 + max(0, stage)) / (2 - min(0, stage))
        
        Args:
            stat_name (str): 'attack', 'defense', 'sp_attack', 'sp_defense', 'speed'
        
        Returns:
            int: Effective stat value
        """
        stat_map = {
            'attack': self.attack,
            'defense': self.defense,
            'sp_attack': self.sp_attack,
            'sp_defense': self.sp_defense,
            'speed': self.speed
        }
        
        base_stat = stat_map.get(stat_name, 0)
        stage = self.stat_stages.get(stat_name, 0)
        
        # Calculate multiplier
        if stage >= 0:
            multiplier = (2 + stage) / 2.0
        else:
            multiplier = 2.0 / (2 - stage)
        
        effective = int(base_stat * multiplier)
        
        # Apply burn modifier to physical attack
        if stat_name == 'attack' and self.status == 'burn':
            effective = effective // 2
        
        # Apply paralysis modifier to speed
        if stat_name == 'speed' and self.status == 'paralysis':
            effective = effective // 4
        
        return effective
    
    def modify_stat_stage(self, stat_name, change):
        """
        Modify a stat stage by a certain amount.
        
        Args:
            stat_name (str): Stat to modify
            change (int): Amount to change (-6 to +6)
        
        Returns:
            int: Actual change applied (may be limited by min/max)
        """
        if stat_name not in self.stat_stages:
            return 0
        
        old_stage = self.stat_stages[stat_name]
        new_stage = max(-6, min(6, old_stage + change))
        actual_change = new_stage - old_stage
        
        self.stat_stages[stat_name] = new_stage
        return actual_change
    
    def reset_stat_stages(self):
        """Reset all stat stages to 0"""
        for stat in self.stat_stages:
            self.stat_stages[stat] = 0
    
    def _load_moves(self, moveset):
        """
        Load moves from database.
        
        Args:
            moveset (list): List of move IDs (max 4)
        """
        move_repo = MoveRepository()
        
        for move_id in moveset[:4]:  # Max 4 moves
            move_data = move_repo.get_with_effects(move_id)
            if move_data:
                self.moves.append(Move(move_data))
            else:
                print(f"Warning: Move with ID {move_id} not found")
    
    def take_damage(self, damage):
        """
        Apply damage to Pokemon.
        
        Args:
            damage (int): Damage amount
        
        Returns:
            int: Actual damage dealt
        """
        actual_damage = min(damage, self.current_hp)
        self.current_hp = max(0, self.current_hp - damage)
        
        if self.current_hp == 0:
            self.fainted = True
            self.status = None  # Status is cleared when fainted
        
        return actual_damage
    
    def heal(self, amount):
        """
        Heal HP.
        
        Args:
            amount (int): Amount to heal
        
        Returns:
            int: Actual HP restored
        """
        if self.fainted:
            return 0
        
        old_hp = self.current_hp
        self.current_hp = min(self.max_hp, self.current_hp + amount)
        return self.current_hp - old_hp
    
    def restore_pp(self, move_index=None, amount=10):
        """
        Restore PP for a move or all moves.
        
        Args:
            move_index (int): Index of move to restore (None = all moves)
            amount (int): Amount of PP to restore
        """
        if move_index is not None:
            if 0 <= move_index < len(self.moves):
                self.moves[move_index].restore_pp(amount)
        else:
            for move in self.moves:
                move.restore_pp(amount)
    
    def apply_status(self, status, duration=0):
        """
        Apply status condition.
        
        Args:
            status (str): 'burn', 'paralysis', 'poison', 'badly_poison', 'sleep', 'freeze'
            duration (int): Duration for sleep (1-7 turns)
        
        Returns:
            bool: True if status was applied, False if already has status
        """
        if self.fainted:
            return False
        
        # Can only have one major status at a time
        if self.status is not None:
            return False
        
        self.status = status
        
        if status == 'sleep':
            self.sleep_turns = duration if duration > 0 else 3  # Default 3 turns
        elif status == 'badly_poison':
            self.toxic_counter = 1
        
        return True
    
    def cure_status(self):
        """Cure status condition"""
        self.status = None
        self.sleep_turns = 0
        self.toxic_counter = 0
    
    def process_end_of_turn_effects(self):
        """
        Process status effects at end of turn.
        
        Returns:
            dict: Dictionary with effects that occurred
        """
        effects = {
            'burn_damage': 0,
            'poison_damage': 0,
            'leech_seed_damage': 0,
            'woke_up': False,
            'thawed': False
        }
        
        if self.fainted:
            return effects
        
        # Burn damage (1/16 of max HP)
        if self.status == 'burn':
            damage = max(1, self.max_hp // 16)
            effects['burn_damage'] = self.take_damage(damage)
        
        # Poison damage
        elif self.status == 'poison':
            damage = max(1, self.max_hp // 8)
            effects['poison_damage'] = self.take_damage(damage)
        
        # Badly Poison (Toxic) - increases each turn
        elif self.status == 'badly_poison':
            damage = max(1, (self.max_hp * self.toxic_counter) // 16)
            effects['poison_damage'] = self.take_damage(damage)
            self.toxic_counter += 1
        
        # Sleep countdown
        elif self.status == 'sleep':
            self.sleep_turns -= 1
            if self.sleep_turns <= 0:
                self.cure_status()
                effects['woke_up'] = True
        
        # Confusion countdown
        if self.confused:
            self.confusion_turns -= 1
            if self.confusion_turns <= 0:
                self.confused = False
        
        return effects
    
    def can_move(self):
        """
        Check if Pokemon can move this turn.
        
        Returns:
            tuple: (can_move: bool, reason: str)
        """
        if self.fainted:
            return False, "fainted"
        
        if self.status == 'sleep':
            return False, "sleep"
        
        if self.status == 'freeze':
            # 20% chance to thaw in Gen 1
            import random
            if random.random() < 0.2:
                self.cure_status()
                return True, "thawed"
            return False, "freeze"
        
        if self.status == 'paralysis':
            # 25% chance to be fully paralyzed
            import random
            if random.random() < 0.25:
                return False, "paralysis"
        
        if self.confused:
            # Confusion: 50% chance to hurt itself
            import random
            if random.random() < 0.5:
                return False, "confusion"
        
        if self.flinched:
            self.flinched = False  # Reset after checking
            return False, "flinch"
        
        if self.recharging:
            self.recharging = False
            return False, "recharging"
        
        return True, None
    
    def has_type(self, type_name):
        """
        Check if Pokemon has a specific type.
        
        Args:
            type_name (str): Type to check
        
        Returns:
            bool: True if Pokemon has this type
        """
        return self.type1 == type_name or self.type2 == type_name
    
    def is_alive(self):
        """Check if Pokemon is alive"""
        return not self.fainted and self.current_hp > 0
    
    def get_hp_percentage(self):
        """Get current HP as percentage"""
        return (self.current_hp / self.max_hp) * 100 if self.max_hp > 0 else 0
    
    def __repr__(self):
        status_str = f" [{self.status.upper()}]" if self.status else ""
        return f"{self.name} (Lv.{self.level}) - HP: {self.current_hp}/{self.max_hp}{status_str}"
    
    def __str__(self):
        return self.__repr__()


class Move:
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
        self.type = move_data['type']
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
    
    def __repr__(self):
        power_str = f"Pwr:{self.power}" if self.power else "Status"
        return f"{self.name} ({power_str}, {self.pp_current}/{self.pp_max} PP)"
    
    def __str__(self):
        return self.__repr__()


# Example usage and testing
if __name__ == "__main__":
    print("=" * 70)
    print("TESTING POKEMON CLASS")
    print("=" * 70)
    
    # Create a Pikachu
    print("\n1. Creating Pikachu (Level 50) with 4 moves...")
    pikachu = Pokemon(
        pokemon_id=25,
        level=50,
        moveset=[85, 93, 99, 113]  # Some example move IDs
    )
    
    print(f"   {pikachu}")
    print(f"   Type: {pikachu.type1}")
    print(f"   Base Stats: HP:{pikachu.max_hp} Atk:{pikachu.attack} Def:{pikachu.defense} " +
          f"SpA:{pikachu.sp_attack} SpD:{pikachu.sp_defense} Spe:{pikachu.speed}")
    print(f"   Moves ({len(pikachu.moves)}):")
    for i, move in enumerate(pikachu.moves):
        print(f"      {i+1}. {move}")
    
    # Test damage
    print("\n2. Testing damage mechanics...")
    print(f"   Before damage: {pikachu}")
    damage = pikachu.take_damage(50)
    print(f"   After 50 damage: {pikachu} (dealt {damage} damage)")
    
    # Test healing
    print("\n3. Testing healing...")
    healed = pikachu.heal(30)
    print(f"   After healing 30 HP: {pikachu} (restored {healed} HP)")
    
    # Test status
    print("\n4. Testing status conditions...")
    success = pikachu.apply_status('burn')
    print(f"   Applied burn: {pikachu}")
    print(f"   Effective Attack (with burn): {pikachu.get_effective_stat('attack')} " +
          f"(base: {pikachu.attack})")
    
    # Test stat stages
    print("\n5. Testing stat stages...")
    pikachu.modify_stat_stage('attack', 2)
    print(f"   Attack +2 stages: {pikachu.get_effective_stat('attack')}")
    pikachu.modify_stat_stage('speed', -1)
    print(f"   Speed -1 stage: {pikachu.get_effective_stat('speed')}")
    
    # Test end of turn
    print("\n6. Testing end of turn effects...")
    effects = pikachu.process_end_of_turn_effects()
    print(f"   After end of turn: {pikachu}")
    print(f"   Burn damage dealt: {effects['burn_damage']}")
    
    # Create a Charizard for comparison
    print("\n7. Creating Charizard (Level 50)...")
    charizard = Pokemon(pokemon_id=6, level=50, moveset=[52, 17, 83, 115])
    print(f"   {charizard}")
    print(f"   Types: {charizard.type1}/{charizard.type2}")
    print(f"   Speed: {charizard.speed}")
    
    print("\n" + "=" * 70)
    print("✅ All tests completed successfully!")
    print("=" * 70)
