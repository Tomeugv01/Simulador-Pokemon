"""
Pokemon class for Pokemon battle system.
Represents a battle-ready Pokemon instance with stats calculation,
HP management, status conditions, and stat stages.
"""

import sys
import os

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from src.repositories import PokemonRepository, MoveRepository
    from src.database import get_moves_at_level
except ImportError:
    # Try alternative import path
    try:
        from repositories import PokemonRepository, MoveRepository
        from database import get_moves_at_level
    except ImportError:
        import sys
        sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))
        from repositories import PokemonRepository, MoveRepository
        from database import get_moves_at_level

try:
    from Move import Move
except ImportError:
    from models.Move import Move

try:
    from experience import ExperienceCurve
except ImportError:
    from models.experience import ExperienceCurve


class Pokemon:
    """
    Pokemon class representing a battle-ready Pokemon instance.
    Handles stats calculation, HP management, status conditions, and stat stages.
    """
    
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
        return Pokemon.TYPE_NAMES.get(type_id, 'Unknown')
    
    @staticmethod
    def generate_ivs(round_number=None, is_starter=False):
        """
        Generate random IVs based on game progress or starter status.
        
        Args:
            round_number (int): Current game round (affects average IV quality)
            is_starter (bool): If True, biases IVs to be much higher
            
        Returns:
            dict: Dictionary of IVs {'hp': x, 'attack': y, ...}
        """
        import random
        
        ivs = {}
        stats = ['hp', 'attack', 'defense', 'sp_attack', 'sp_defense', 'speed']
        
        if is_starter:
            # Starters get biased rolls: Max 31 is guaranteed in 3 stats
            # The rest are rolled relatively high (15-31)
            guaranteed_max = random.sample(stats, 3)
            for stat in stats:
                if stat in guaranteed_max:
                    ivs[stat] = 31
                else:
                    ivs[stat] = random.randint(15, 31)
        
        elif round_number is not None:
            # Scale based on round number
            # Round 1: Avg 10
            # Round 10: Avg 25
            # Max round considered ~20
            
            # Base floor/ceiling increases with round
            min_val = min(20, round_number * 1)
            max_val = min(31, 15 + round_number * 1)
            
            for stat in stats:
                # Still allow some randomness, but skewed higher
                # 20% chance for perfect IV even in early rounds
                if random.random() < 0.1:
                    ivs[stat] = 31
                else:
                    ivs[stat] = random.randint(min_val, max_val)
        
        else:
            # Full random 0-31
            for stat in stats:
                ivs[stat] = random.randint(0, 31)
                
        return ivs

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
        self.type1 = Pokemon.get_type_name(base_data['type1'])
        self.type2 = Pokemon.get_type_name(base_data['type2']) if base_data['type2'] else None
        self.base_hp = base_data['hp']
        self.base_attack = base_data['attack']
        self.base_defense = base_data['defense']
        self.base_sp_attack = base_data['special_attack']
        self.base_sp_defense = base_data['special_defense']
        self.base_speed = base_data['speed']
        self.evolution_level = base_data['evolution_level']
        self.evolves_to_id = base_data.get('evolves_to_id')  # New evolution field
        self.exp_curve = base_data['exp_curve']
        
        # IVs and EVs (for more advanced stat calculation)
        if ivs is None:
            # Randomize IVs if not provided (default 0-31)
            import random
            self.ivs = {
                'hp': random.randint(0, 31), 
                'attack': random.randint(0, 31), 
                'defense': random.randint(0, 31),
                'sp_attack': random.randint(0, 31), 
                'sp_defense': random.randint(0, 31), 
                'speed': random.randint(0, 31)
            }
        else:
            self.ivs = ivs
            
        self.evs = evs or {
            'hp': 0, 'attack': 0, 'defense': 0,
            'sp_attack': 0, 'sp_defense': 0, 'speed': 0
        }
        
        # Level and Experience
        self.level = max(1, min(100, level))
        self.current_exp = ExperienceCurve.exp_for_level(self.level, self.exp_curve)
        
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
        self.trap_turns = 0  # Turns remaining for trap
        self.seeded = False  # Leech Seed
        self.protected = False  # Protect/Detect
        
        # Substitute
        self.substitute = False  # Has substitute active
        self.substitute_hp = 0  # HP of the substitute
        
        # Move restrictions
        self.encore = False  # Forced to repeat last move
        self.encore_turns = 0
        self.encore_move = None  # Which move to repeat
        self.taunted = False  # Can't use status moves
        self.taunt_turns = 0
        self.disabled_move = None  # Which move is disabled
        self.disable_turns = 0
        self.tormented = False  # Can't use same move twice in a row
        self.last_move_used = None  # Track for torment
        
        # Continuous healing/damage
        self.cursed = False  # Ghost-type Curse
        self.ingrain = False  # Can't switch, heals each turn
        self.aqua_ring = False  # Heals each turn
        
        # Transformation
        self.transformed = False
        self.original_stats = None  # To store original stats, moves, types
        
        # Other conditions
        self.embargo = False  # Can't use items
        self.embargo_turns = 0
        self.heal_block = False  # Can't heal
        self.heal_block_turns = 0
        self.yawn = False  # Will fall asleep next turn
        self.yawn_turns = 0
        
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
    
    def get_stat_changes_display(self):
        """Get a formatted string showing current stat stage changes
        
        Returns:
            str: Formatted stat changes like '+2 Atk, -1 Def' or empty string if no changes
        """
        stat_names = {
            'attack': 'Atk',
            'defense': 'Def',
            'sp_attack': 'SpA',
            'sp_defense': 'SpD',
            'speed': 'Spe',
            'accuracy': 'Acc',
            'evasion': 'Eva'
        }
        
        changes = []
        for stat, stage in self.stat_stages.items():
            if stage != 0:
                sign = '+' if stage > 0 else ''
                changes.append(f"{sign}{stage} {stat_names[stat]}")
        
        return ', '.join(changes) if changes else ''
    
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
        if self.fainted or self.heal_block:
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
    
    def create_substitute(self, hp_cost=None):
        """
        Create a substitute with 1/4 of max HP.
        
        Args:
            hp_cost (int): HP to use for substitute (defaults to 1/4 max HP)
        
        Returns:
            bool: True if substitute was created, False otherwise
        """
        if self.substitute:
            return False  # Already has substitute
        
        cost = hp_cost if hp_cost else max(1, self.max_hp // 4)
        
        if self.current_hp <= cost:
            return False  # Not enough HP
        
        self.take_damage(cost)
        self.substitute = True
        self.substitute_hp = cost
        return True
    
    def damage_substitute(self, damage):
        """
        Apply damage to substitute instead of Pokemon.
        
        Args:
            damage (int): Damage amount
        
        Returns:
            dict: {'broke': bool, 'remaining_damage': int}
        """
        if not self.substitute:
            return {'broke': False, 'remaining_damage': damage}
        
        actual_damage = min(damage, self.substitute_hp)
        self.substitute_hp -= actual_damage
        
        if self.substitute_hp <= 0:
            self.substitute = False
            self.substitute_hp = 0
            return {'broke': True, 'remaining_damage': damage - actual_damage}
        
        return {'broke': False, 'remaining_damage': 0}
    
    def can_use_move(self, move):
        """
        Check if a specific move can be used.
        
        Args:
            move: Move object or move index
        
        Returns:
            tuple: (can_use: bool, reason: str)
        """
        # Check if disabled
        if self.disabled_move and move == self.disabled_move:
            return False, "disabled"
        
        # Check if taunted (can't use status moves)
        if self.taunted and hasattr(move, 'is_status') and move.is_status():
            return False, "taunted"
        
        # Check if encored (must use specific move)
        if self.encore and move != self.encore_move:
            return False, "encored"
        
        # Check if tormented (can't use same move twice)
        if self.tormented and move == self.last_move_used:
            return False, "tormented"
        
        return True, None
    
    def transform(self, target):
        """
        Transform into the target Pokemon.
        Copies stats (except HP), moves, types, and stat stages.
        """
        if self.transformed:
            return False  # Already transformed
            
        # 1. Backup original state
        self.original_stats = {
            'attack': self.attack,
            'defense': self.defense,
            'sp_attack': self.sp_attack,
            'sp_defense': self.sp_defense,
            'speed': self.speed,
            'type1': self.type1,
            'type2': self.type2,
            'moves': [m.copy() for m in self.moves], # Deep copy of moves
        }
        
        # 2. Copy Target Stats (HP remains original)
        self.attack = target.attack
        self.defense = target.defense
        self.sp_attack = target.sp_attack
        self.sp_defense = target.sp_defense
        self.speed = target.speed
        
        # 3. Copy Target Types
        self.type1 = target.type1
        self.type2 = target.type2
        
        # 4. Copy Target Moves with 5 PP
        self.moves = []
        for move in target.moves:
            new_move = move.copy()
            
            # Handle Move object fields
            if hasattr(new_move, 'pp_current'):
                new_move.pp_current = 5
                new_move.pp_max = 5
            # Handle dict fields (fallback)
            elif isinstance(new_move, dict):
                new_move['pp'] = 5
                new_move['max_pp'] = 5
                
            self.moves.append(new_move)
            
        # 5. Copy Stat Stages
        self.stat_stages = target.stat_stages.copy()
        
        # 6. Set Flag
        self.transformed = True
        return True
    
    def reset_transform(self):
        """Revert transformation"""
        if not self.transformed or not self.original_stats:
            return
            
        # Restore stats
        self.attack = self.original_stats['attack']
        self.defense = self.original_stats['defense']
        self.sp_attack = self.original_stats['sp_attack']
        self.sp_defense = self.original_stats['sp_defense']
        self.speed = self.original_stats['speed']
        
        # Restore types
        self.type1 = self.original_stats['type1']
        self.type2 = self.original_stats['type2']
        
        # Restore moves
        self.moves = self.original_stats['moves']
        
        self.transformed = False
        self.original_stats = None

    def reset_volatile_conditions(self):
        """Reset all volatile battle conditions (when switching out)"""
        # Reset transformation first
        self.reset_transform()
        
        self.confused = False
        self.confusion_turns = 0
        self.flinched = False
        self.charging = False
        self.recharging = False
        self.protected = False
        
        # Reset stat stages
        self.reset_stat_stages()
        
        # Keep some conditions that persist through switches
        # (substitute, trap if applicable, etc.)
        if not self.ingrain:  # Ingrain prevents switching
            self.trapped = False
            self.trap_turns = 0
    
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
            'trap_damage': 0,
            'curse_damage': 0,
            'aqua_ring_heal': 0,
            'ingrain_heal': 0,
            'woke_up': False,
            'thawed': False,
            'fell_asleep': False  # From Yawn
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
        
        # Trap damage (Bind, Wrap, etc.) - 1/16 or 1/8 with Binding Band
        if self.trapped and self.trap_turns > 0:
            damage = max(1, self.max_hp // 16)
            effects['trap_damage'] = self.take_damage(damage)
            self.trap_turns -= 1
            if self.trap_turns <= 0:
                self.trapped = False
        
        # Leech Seed damage (already tracked elsewhere, but processed here)
        if self.seeded:
            damage = max(1, self.max_hp // 8)
            effects['leech_seed_damage'] = self.take_damage(damage)
        
        # Curse damage (Ghost-type Curse) - 1/4 max HP
        if self.cursed:
            damage = max(1, self.max_hp // 4)
            effects['curse_damage'] = self.take_damage(damage)
        
        # Aqua Ring healing - 1/16 max HP
        if self.aqua_ring:
            heal = max(1, self.max_hp // 16)
            effects['aqua_ring_heal'] = self.heal(heal)
        
        # Ingrain healing - 1/16 max HP
        if self.ingrain:
            heal = max(1, self.max_hp // 16)
            effects['ingrain_heal'] = self.heal(heal)
        
        # Move restriction countdowns
        if self.encore:
            self.encore_turns -= 1
            if self.encore_turns <= 0:
                self.encore = False
                self.encore_move = None
        
        if self.taunted:
            self.taunt_turns -= 1
            if self.taunt_turns <= 0:
                self.taunted = False
        
        if self.disabled_move:
            self.disable_turns -= 1
            if self.disable_turns <= 0:
                self.disabled_move = None
        
        if self.embargo:
            self.embargo_turns -= 1
            if self.embargo_turns <= 0:
                self.embargo = False
        
        if self.heal_block:
            self.heal_block_turns -= 1
            if self.heal_block_turns <= 0:
                self.heal_block = False
        
        # Yawn countdown - falls asleep after 1 turn
        if self.yawn:
            self.yawn_turns -= 1
            if self.yawn_turns <= 0:
                self.yawn = False
                if not self.status:  # Only if no other status
                    import random
                    self.apply_status('sleep', random.randint(1, 3))
                    effects['fell_asleep'] = True
        
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
    
    def gain_exp(self, exp_amount: int) -> dict:
        """
        Award experience points and handle level-ups.
        
        Args:
            exp_amount: EXP points to award
            
        Returns:
            dict: Level-up info {'leveled_up', 'old_level', 'new_level', 'stat_gains', 'exp_gained', 'total_exp'}
        """
        old_level = self.level
        old_stats = {
            'hp': self.max_hp,
            'attack': self.attack,
            'defense': self.defense,
            'sp_attack': self.sp_attack,
            'sp_defense': self.sp_defense,
            'speed': self.speed
        }
        
        # Add experience
        self.current_exp += exp_amount
        
        # Check for level up(s)
        new_level = ExperienceCurve.level_from_exp(self.current_exp, self.exp_curve)
        leveled_up = new_level > old_level
        
        if leveled_up and new_level <= 100:
            # Get HP percentage before level up
            hp_percentage = self.get_hp_percentage() / 100
            
            # Update level
            self.level = new_level
            
            # Recalculate stats
            self.max_hp = self._calculate_hp_stat()
            self.attack = self._calculate_stat('attack')
            self.defense = self._calculate_stat('defense')
            self.sp_attack = self._calculate_stat('sp_attack')
            self.sp_defense = self._calculate_stat('sp_defense')
            self.speed = self._calculate_stat('speed')
            
            # Restore HP percentage (but at least 1 HP if alive)
            if self.current_hp > 0:
                self.current_hp = max(1, int(self.max_hp * hp_percentage))
        
        # Calculate stat gains
        stat_gains = {
            'hp': self.max_hp - old_stats['hp'],
            'attack': self.attack - old_stats['attack'],
            'defense': self.defense - old_stats['defense'],
            'sp_attack': self.sp_attack - old_stats['sp_attack'],
            'sp_defense': self.sp_defense - old_stats['sp_defense'],
            'speed': self.speed - old_stats['speed']
        }
        
        return {
            'leveled_up': leveled_up,
            'old_level': old_level,
            'new_level': self.level,
            'stat_gains': stat_gains,
            'exp_gained': exp_amount,
            'total_exp': self.current_exp
        }
    
    def check_moves_learned_at_level(self, level):
        """
        Check what moves this Pokemon learns at a specific level.
        
        Args:
            level (int): Level to check
            
        Returns:
            list: List of move dicts with 'id' and 'name'
        """
        return get_moves_at_level(self.id, level)
    
    def learn_move(self, move_id, replace_index=None):
        """
        Learn a new move, optionally replacing an existing one.
        
        Args:
            move_id (int): ID of the move to learn
            replace_index (int): Index (0-3) of move to replace, or None to append
            
        Returns:
            dict: Result with 'success', 'message', and 'replaced_move' if applicable
        """
        # Load the move
        move_repo = MoveRepository()
        move_data = move_repo.get_by_id(move_id)
        
        if not move_data:
            return {'success': False, 'message': 'Move not found'}
        
        # Check if Pokemon already knows this move
        for i, existing_move in enumerate(self.moves):
            if existing_move.get('id') == move_id:
                # If replacing this exact move, allow it
                if replace_index == i:
                    break
                return {'success': False, 'message': f'Already knows {move_data["name"]}'}
        
        # If replace_index is specified, replace that move
        if replace_index is not None:
            if 0 <= replace_index < len(self.moves):
                old_move = self.moves[replace_index]
                self.moves[replace_index] = move_data
                return {
                    'success': True,
                    'message': f'Learned {move_data["name"]}!',
                    'replaced_move': old_move
                }
            else:
                return {'success': False, 'message': 'Invalid move slot'}
        
        # If less than 4 moves, just add it
        if len(self.moves) < 4:
            self.moves.append(move_data)
            return {'success': True, 'message': f'Learned {move_data["name"]}!'}
        
        # Already has 4 moves and no replacement specified
        return {'success': False, 'message': 'Already knows 4 moves'}
    
    def level_up(self, levels=1):
        """
        Directly increase Pokemon level (legacy method for compatibility).
        Prefer using gain_exp() for proper EXP-based leveling.
        
        Args:
            levels (int): Number of levels to gain (default 1)
            
        Returns:
            dict: Dictionary with level-up info {'old_level', 'new_level', 'stat_gains'}
        """
        # Calculate EXP needed for target level
        target_level = min(100, self.level + levels)
        target_exp = ExperienceCurve.exp_for_level(target_level, self.exp_curve)
        exp_needed = target_exp - self.current_exp
        
        # Use gain_exp to handle the level up
        result = self.gain_exp(exp_needed)
        
        return {
            'old_level': result['old_level'],
            'new_level': result['new_level'],
            'stat_gains': result['stat_gains']
        }
    
    def can_evolve(self):
        """
        Check if Pokemon can evolve at current level.
        Supports multiple evolution paths (e.g., Eevee) via pokemon_evolutions table.
        Works even if Pokemon level is higher than evolution threshold.
        
        Returns:
            tuple: (bool, list or None) - (can_evolve, list of evolution_ids)
                   If multiple evolutions available, returns all options
        """
        # Quick check: if legacy column is null, likely checks are unneeded, 
        # but to be sure we should check unless we are certain.
        # However, for performance, we trust the entity loader populated evolves_to_id 
        # as a flag that "some evolution exists".
        if not hasattr(self, 'evolves_to_id') or self.evolves_to_id is None:
            return False, None
            
        import sqlite3
        
        valid_evolutions = []
        conn = None
        
        try:
            conn = sqlite3.connect('data/pokemon_battle.db')
            cursor = conn.cursor()
            
            # Check for multiple evolutions in the new table
            cursor.execute('''
                SELECT evolves_to_id, evolution_level 
                FROM pokemon_evolutions 
                WHERE pokemon_id = ?
            ''', (self.id,))
            rows = cursor.fetchall()
            
            if rows:
                for evo_id, evo_lvl in rows:
                    if self.level >= evo_lvl:
                        valid_evolutions.append(evo_id)
            else:
                # Fallback to legacy behavior if table is empty for this mon
                if self.evolution_level and self.level >= self.evolution_level:
                    valid_evolutions.append(self.evolves_to_id)

        except sqlite3.Error as e:
            print(f"Database error in can_evolve: {e}")
            # Fallback
            if self.evolution_level and self.level >= self.evolution_level:
                valid_evolutions.append(self.evolves_to_id)
        finally:
            if conn:
                conn.close()
                
        if valid_evolutions:
            # Sort for consistency
            valid_evolutions = sorted(list(set(valid_evolutions)))
            return True, valid_evolutions
        
        return False, None
    
    def evolve(self, new_species_id):
        """
        Evolve Pokemon into a new species.
        Stats are recalculated based on new base stats.
        HP percentage is preserved.
        Moves are kept unless new species can't learn them.
        
        Args:
            new_species_id (int): ID of the evolved species
            
        Returns:
            dict: Evolution info {'old_name', 'new_name', 'stat_changes'}
        """
        old_name = self.name
        old_stats = {
            'hp': self.max_hp,
            'attack': self.attack,
            'defense': self.defense,
            'sp_attack': self.sp_attack,
            'sp_defense': self.sp_defense,
            'speed': self.speed
        }
        
        # Get HP percentage before evolution
        hp_percentage = self.get_hp_percentage() / 100
        
        # Load new species data
        repo = PokemonRepository()
        new_data = repo.get_by_id(new_species_id)
        
        if not new_data:
            raise ValueError(f"Cannot evolve: species {new_species_id} not found")
        
        # Update base data
        self.id = new_data['id']
        self.name = new_data['name']
        self.type1 = new_data['type1']
        self.type2 = new_data['type2']
        self.base_hp = new_data['hp']
        self.base_attack = new_data['attack']
        self.base_defense = new_data['defense']
        self.base_sp_attack = new_data['special_attack']
        self.base_sp_defense = new_data['special_defense']
        self.base_speed = new_data['speed']
        self.evolution_level = new_data['evolution_level']
        self.evolves_to_id = new_data.get('evolves_to_id')  # Store evolution target
        self.exp_curve = new_data['exp_curve']
        
        # Recalculate stats
        self.max_hp = self._calculate_hp_stat()
        self.attack = self._calculate_stat('attack')
        self.defense = self._calculate_stat('defense')
        self.sp_attack = self._calculate_stat('sp_attack')
        self.sp_defense = self._calculate_stat('sp_defense')
        self.speed = self._calculate_stat('speed')
        
        # Restore HP percentage (but at least 1 HP if alive)
        if self.current_hp > 0:
            self.current_hp = max(1, int(self.max_hp * hp_percentage))
        
        # Calculate stat changes
        stat_changes = {
            'hp': self.max_hp - old_stats['hp'],
            'attack': self.attack - old_stats['attack'],
            'defense': self.defense - old_stats['defense'],
            'sp_attack': self.sp_attack - old_stats['sp_attack'],
            'sp_defense': self.sp_defense - old_stats['sp_defense'],
            'speed': self.speed - old_stats['speed']
        }
        
        return {
            'old_name': old_name,
            'new_name': self.name,
            'stat_changes': stat_changes
        }
    
    def __repr__(self):
        status_str = f" [{self.status.upper()}]" if self.status else ""
        return f"{self.name} (Lv.{self.level}) - HP: {self.current_hp}/{self.max_hp}{status_str}"
    
    def __str__(self):
        return self.__repr__()
