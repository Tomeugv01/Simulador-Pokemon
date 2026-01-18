"""
Pokemon Battle Turn Logic
Handles the complete turn resolution for Pokemon battles following standard mechanics.
"""
import random
import sys
import os
from typing import List, Dict, Optional, Tuple, Any
from enum import Enum

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(__file__)), 'src'))

try:
    from src.repositories import MoveRepository
except ImportError:
    try:
        from repositories import MoveRepository
    except ImportError:
        MoveRepository = None


class ActionType(Enum):
    """Types of actions a player can take"""
    FIGHT = "fight"  # Use a move
    SWITCH = "switch"  # Switch Pokemon
    ITEM = "item"  # Use an item (future implementation)
    RUN = "run"  # Attempt to flee (future implementation)


class PriorityBracket(Enum):
    """Priority brackets for action resolution"""
    SWITCH = 7  # Switching and running
    MEGA_EVOLUTION = 6  # Mega Evolution (future)
    PURSUIT_SWITCH = 5  # Pursuit when target switches
    PRIORITY_4 = 4  # Extreme Speed
    PRIORITY_3 = 3  # Fake Out
    PRIORITY_2 = 2  # Feint, Extreme Speed variants
    PRIORITY_1 = 1  # Quick Attack, Aqua Jet, etc.
    NORMAL = 0  # Standard moves
    PRIORITY_NEG_1 = -1  # Vital Throw
    PRIORITY_NEG_2 = -2  # Focus Punch
    PRIORITY_NEG_3 = -3  # Beak Blast
    PRIORITY_NEG_4 = -4  # Avalanche
    PRIORITY_NEG_5 = -5  # Counter, Mirror Coat
    PRIORITY_NEG_6 = -6  # Roar, Whirlwind, Dragon Tail
    PRIORITY_NEG_7 = -7  # Trick Room


class BattleAction:
    """Represents a single action in battle"""
    def __init__(self, pokemon, action_type: ActionType, **kwargs):
        self.pokemon = pokemon
        self.action_type = action_type
        self.move = kwargs.get('move', None)
        self.target = kwargs.get('target', None)
        self.switch_target = kwargs.get('switch_target', None)
        self.item = kwargs.get('item', None)
        self.priority = self._calculate_priority()
        
    def _calculate_priority(self) -> int:
        """Calculate the priority of this action"""
        if self.action_type == ActionType.SWITCH:
            return PriorityBracket.SWITCH.value
        elif self.action_type == ActionType.FIGHT and self.move:
            # Get move priority from move data
            return self.move.get('priority', 0)
        else:
            return PriorityBracket.NORMAL.value


class TurnManager:
    """Manages the complete turn resolution for a Pokemon battle"""
    
    def __init__(self, battle_state: Dict[str, Any]):
        """
        Initialize the turn manager
        
        Args:
            battle_state: Dictionary containing:
                - player1_active: Active Pokemon for player 1
                - player2_active: Active Pokemon for player 2
                - player1_team: Full team for player 1
                - player2_team: Full team for player 2
                - weather: Current weather condition
                - field_effects: Active field effects (terrain, trick room, etc.)
                - turn_count: Current turn number
        """
        self.battle_state = battle_state
        self.turn_log = []
        self.fainted_pokemon = []
        self.move_repo = MoveRepository() if MoveRepository else None
        self.forced_switches = []  # Track Pokemon that must switch out
        
    def execute_turn(self, actions: List[BattleAction]) -> Dict[str, Any]:
        """
        Execute a complete battle turn
        
        Args:
            actions: List of BattleAction objects (one per active Pokemon)
            
        Returns:
            Dictionary with turn results and updated battle state
        """
        # IMPORTANT: Clear previous turn's log
        self.turn_log = []
        self.fainted_pokemon = []
        self.forced_switches = []  # Clear forced switches from previous turn
        
        # Phase 1: Pre-turn effects
        self._phase_pre_turn()
        
        # Phase 2: Sort and execute actions
        sorted_actions = self._sort_actions(actions)
        self._phase_execute_actions(sorted_actions)
        
        # Phase 3: End-of-turn effects
        self._phase_end_turn()
        
        # Phase 4: Handle fainted Pokemon
        self._phase_handle_faints()
        
        # Phase 5: Check win condition
        winner = self._check_win_condition()
        
        return {
            'battle_state': self.battle_state,
            'turn_log': self.turn_log,
            'fainted_pokemon': self.fainted_pokemon,
            'forced_switches': self.forced_switches,  # Return forced switches to main loop
            'winner': winner,
            'battle_ended': winner is not None
        }
    
    # ========== PHASE 1: PRE-TURN EFFECTS ==========
    
    def _phase_pre_turn(self):
        """Execute all pre-turn effects"""
        # Don't log turn number here - main.py already displays it
        # self._log("=== Beginning Turn {} ===".format(self.battle_state.get('turn_count', 1)))
        
        # Reset turn-based volatile conditions
        for pokemon in self._get_all_active_pokemon():
            pokemon.protected = False  # Protection lasts only one turn
            pokemon.flinched = False  # Flinch resets each turn
        
        # 1. Weather effects
        self._process_weather_tick()
        
        # 2. Field effect duration
        self._process_field_effects_tick()
        
        # 3. Ability triggers (start of turn)
        self._process_start_of_turn_abilities()
        
        # 4. Status condition effects and checks
        self._process_status_conditions()
        
        # 5. Item effects (start of turn)
        self._process_start_of_turn_items()
        
        # 6. Special effect ends (Roost flying-type restoration)
        self._process_effect_endings()
    
    def _process_weather_tick(self):
        """Process weather duration and damage"""
        weather = self.battle_state.get('weather', {})
        if not weather or weather.get('type') == 'None':
            return
            
        weather_type = weather.get('type')
        turns_remaining = weather.get('turns_remaining', 0)
        
        if turns_remaining > 0:
            self._log(f"{weather_type} continues...")
            
            # Apply weather damage (Sandstorm, Hail)
            if weather_type == 'Sandstorm':
                self._apply_sandstorm_damage()
            elif weather_type == 'Hail':
                self._apply_hail_damage()
                
            # Decrement duration (done in end phase)
        else:
            self._log(f"The {weather_type} faded.")
            self.battle_state['weather'] = {'type': 'None', 'turns_remaining': 0}
    
    def _apply_sandstorm_damage(self):
        """Apply sandstorm damage to non-immune Pokemon"""
        for pokemon in self._get_all_active_pokemon():
            # Immune types: Rock, Ground, Steel
            if pokemon.type1 not in ['Rock', 'Ground', 'Steel'] and \
               pokemon.type2 not in ['Rock', 'Ground', 'Steel']:
                damage = pokemon.max_hp // 16
                pokemon.take_damage(damage)
                self._log(f"{pokemon.name} is buffeted by the sandstorm! (-{damage} HP)")
    
    def _apply_hail_damage(self):
        """Apply hail damage to non-immune Pokemon"""
        for pokemon in self._get_all_active_pokemon():
            # Immune type: Ice
            if pokemon.type1 != 'Ice' and pokemon.type2 != 'Ice':
                damage = pokemon.max_hp // 16
                pokemon.take_damage(damage)
                self._log(f"{pokemon.name} is buffeted by the hail! (-{damage} HP)")
    
    def _process_field_effects_tick(self):
        """Process field effect durations"""
        field_effects = self.battle_state.get('field_effects', {})
        
        # Terrain effects
        terrain = field_effects.get('terrain', {})
        if terrain.get('type') and terrain.get('type') != 'None':
            turns_remaining = terrain.get('turns_remaining', 0)
            if turns_remaining <= 0:
                self._log(f"The {terrain.get('type')} faded.")
                field_effects['terrain'] = {'type': 'None', 'turns_remaining': 0}
        
        # Trick Room
        if field_effects.get('trick_room', False):
            turns_remaining = field_effects.get('trick_room_turns', 0)
            if turns_remaining <= 0:
                self._log("The twisted dimensions returned to normal!")
                field_effects['trick_room'] = False
                field_effects['trick_room_turns'] = 0
        
        # Gravity
        if field_effects.get('gravity', False):
            turns_remaining = field_effects.get('gravity_turns', 0)
            if turns_remaining <= 0:
                self._log("Gravity returned to normal!")
                field_effects['gravity'] = False
                field_effects['gravity_turns'] = 0
    
    def _process_start_of_turn_abilities(self):
        """Trigger abilities that activate at the start of turn"""
        for pokemon in self._get_all_active_pokemon():
            if pokemon.current_hp <= 0:
                continue
                
            ability = pokemon.ability if hasattr(pokemon, 'ability') else None
            if not ability:
                continue
            
            # Speed Boost
            if ability == 'Speed Boost':
                pokemon.modify_stat_stage('speed', 1)
                self._log(f"{pokemon.name}'s Speed Boost raised its Speed!")
            
            # Shed Skin (cure status)
            elif ability == 'Shed Skin' and pokemon.status != 'healthy':
                if random.random() < 0.33:  # 33% chance
                    old_status = pokemon.status
                    pokemon.cure_status()
                    self._log(f"{pokemon.name} shed its skin and cured its {old_status}!")
            
            # Poison Heal
            elif ability == 'Poison Heal' and pokemon.status in ['poison', 'badly_poison']:
                heal_amount = pokemon.max_hp // 8
                pokemon.heal(heal_amount)
                self._log(f"{pokemon.name} restored HP using its Poison Heal!")
            
            # Hydration (cure status in rain)
            elif ability == 'Hydration' and self.battle_state.get('weather', {}).get('type') == 'Rain':
                if pokemon.status != 'healthy':
                    old_status = pokemon.status
                    pokemon.cure_status()
                    self._log(f"{pokemon.name} was cured of {old_status} by Hydration!")
    
    def _process_status_conditions(self):
        """Process status condition effects and checks"""
        for pokemon in self._get_all_active_pokemon():
            if pokemon.current_hp <= 0:
                continue
            
            status = pokemon.status
            
            # Poison damage
            if status == 'poison':
                damage = pokemon.max_hp // 8
                pokemon.take_damage(damage)
                self._log(f"{pokemon.name} is hurt by poison! (-{damage} HP)")
            
            # Badly poisoned damage (increases each turn)
            elif status == 'badly_poison':
                toxic_counter = pokemon.toxic_counter if hasattr(pokemon, 'toxic_counter') else 1
                damage = (pokemon.max_hp * toxic_counter) // 16
                pokemon.take_damage(damage)
                self._log(f"{pokemon.name} is hurt by poison! (-{damage} HP)")
                if hasattr(pokemon, 'toxic_counter'):
                    pokemon.toxic_counter += 1
            
            # Burn damage (and Attack reduction handled in damage calculation)
            elif status == 'burn':
                damage = pokemon.max_hp // 16
                pokemon.take_damage(damage)
                self._log(f"{pokemon.name} is hurt by its burn! (-{damage} HP)")
            
            # Sleep counter decrement
            elif status == 'sleep':
                if pokemon.sleep_turns > 0:
                    pokemon.sleep_turns -= 1
                    if pokemon.sleep_turns == 0:
                        pokemon.cure_status()
                        self._log(f"{pokemon.name} woke up!")
                    else:
                        self._log(f"{pokemon.name} is fast asleep.")
            
            # Freeze thaw check (~20% chance)
            elif status == 'freeze':
                if random.random() < 0.20:
                    pokemon.cure_status()
                    self._log(f"{pokemon.name} thawed out!")
                else:
                    self._log(f"{pokemon.name} is frozen solid!")
            
            # Confusion self-hit check
            if pokemon.confused:
                if pokemon.confusion_turns > 0:
                    pokemon.confusion_turns -= 1
                    if pokemon.confusion_turns == 0:
                        pokemon.confused = False
                        self._log(f"{pokemon.name} snapped out of confusion!")
                    else:
                        # 33% chance to hit self
                        if random.random() < 0.33:
                            # Calculate confusion self-damage
                            damage = self._calculate_confusion_damage(pokemon)
                            pokemon.take_damage(damage)
                            self._log(f"{pokemon.name} hurt itself in confusion! (-{damage} HP)")
    
    def _process_start_of_turn_items(self):
        """Process held item effects at start of turn"""
        for pokemon in self._get_all_active_pokemon():
            if pokemon.current_hp <= 0:
                continue
                
            held_item = pokemon.held_item if hasattr(pokemon, 'held_item') else None
            if not held_item:
                continue
            
            # Leftovers
            if held_item == 'Leftovers':
                heal_amount = pokemon.max_hp // 16
                pokemon.heal(heal_amount)
                self._log(f"{pokemon.name} restored HP using its Leftovers!")
            
            # Black Sludge
            elif held_item == 'Black Sludge':
                if pokemon.type1 == 'Poison' or pokemon.type2 == 'Poison':
                    heal_amount = pokemon.max_hp // 16
                    pokemon.heal(heal_amount)
                    self._log(f"{pokemon.name} restored HP using its Black Sludge!")
                else:
                    damage = pokemon.max_hp // 8
                    pokemon.take_damage(damage)
                    self._log(f"{pokemon.name} was hurt by the Black Sludge! (-{damage} HP)")
            
            # Flame Orb activation (if not already burned)
            elif held_item == 'Flame Orb' and pokemon.status == 'healthy':
                if self.battle_state.get('turn_count', 1) > 1:  # Activates after first turn
                    pokemon.apply_status('burn')
                    self._log(f"{pokemon.name} was burned by its Flame Orb!")
            
            # Toxic Orb activation (if not already poisoned)
            elif held_item == 'Toxic Orb' and pokemon.status == 'healthy':
                if self.battle_state.get('turn_count', 1) > 1:
                    pokemon.apply_status('badly_poison')
                    self._log(f"{pokemon.name} was badly poisoned by its Toxic Orb!")
    
    def _process_effect_endings(self):
        """Process effects that end at start of turn"""
        for pokemon in self._get_all_active_pokemon():
            # Roost: restore Flying type if used last turn
            if hasattr(pokemon, 'roosted') and pokemon.roosted:
                pokemon.roosted = False
                # Restore flying type logic would go here
    
    # ========== PHASE 2: ACTION EXECUTION ==========
    
    def _sort_actions(self, actions: List[BattleAction]) -> List[BattleAction]:
        """
        Sort actions by priority and speed
        
        Returns actions in order of execution
        """
        # Separate by priority bracket
        sorted_actions = sorted(actions, key=lambda a: (
            -a.priority,  # Higher priority first (negative for descending)
            -self._calculate_effective_speed(a.pokemon),  # Higher speed first
            random.random()  # Random tiebreaker
        ))
        
        # Check for Trick Room reversal
        field_effects = self.battle_state.get('field_effects', {})
        if field_effects.get('trick_room', False):
            # Within each priority bracket, reverse speed order
            # Group by priority, reverse speed within groups
            priority_groups = {}
            for action in sorted_actions:
                if action.priority not in priority_groups:
                    priority_groups[action.priority] = []
                priority_groups[action.priority].append(action)
            
            # Reverse speed order within each priority group
            sorted_actions = []
            for priority in sorted(priority_groups.keys(), reverse=True):
                group = priority_groups[priority]
                # Sort by speed ascending (slowest first) in Trick Room
                group.sort(key=lambda a: (
                    self._calculate_effective_speed(a.pokemon),
                    random.random()
                ))
                sorted_actions.extend(group)
        
        return sorted_actions
    
    def _calculate_effective_speed(self, pokemon) -> int:
        """Calculate effective speed with all modifiers"""
        # Use the Pokemon's get_effective_stat method which includes stage changes and status
        base_speed = pokemon.get_effective_stat('speed')
        
        # Tailwind doubles speed (paralysis already handled in get_effective_stat)
        # Check which side the pokemon is on
        side_effects = self._get_side_effects(pokemon)
        if side_effects.get('tailwind', False):
            base_speed *= 2
        
        # Choice Scarf multiplies by 1.5
        if hasattr(pokemon, 'held_item') and pokemon.held_item == 'Choice Scarf':
            base_speed = int(base_speed * 1.5)
        
        return base_speed
    
    def _phase_execute_actions(self, actions: List[BattleAction]):
        """Execute all actions in sorted order"""
        for action in actions:
            pokemon = action.pokemon
            
            # Skip if Pokemon fainted
            if pokemon.current_hp <= 0:
                continue
            
            # Execute based on action type
            if action.action_type == ActionType.SWITCH:
                self._execute_switch(pokemon, action.switch_target)
            elif action.action_type == ActionType.FIGHT:
                # Get the current active opponent (in case of switches)
                current_target = self._get_current_target(pokemon)
                self._execute_move(pokemon, action.move, current_target)
    
    def _get_current_target(self, user):
        """Get the currently active opponent Pokemon (handles mid-turn switches)"""
        # Determine which side the user is on
        if user == self.battle_state.get('player1_active') or user in self.battle_state.get('player1_team', []):
            # User is player1, target is player2's active
            return self.battle_state.get('player2_active')
        else:
            # User is player2, target is player1's active
            return self.battle_state.get('player1_active')
    
    def _execute_switch(self, pokemon, switch_target):
        """Execute a Pokemon switch"""
        # Handle switch-out effects (trapping moves, etc.)
        if pokemon.trapped and not self._can_switch(pokemon):
            self._log(f"{pokemon.name} can't switch out!")
            return
        
        # Reset volatile status on switch
        pokemon.reset_volatile_conditions()
        
        # Determine which trainer owns this Pokemon
        trainer_name = "Player" if pokemon in self.battle_state.get('player1_team', []) else "Opponent"
        
        # Perform the switch
        self._log(f"{trainer_name} withdrew {pokemon.name}!")
        
        # Update battle state with new Pokemon
        if pokemon == self.battle_state.get('player1_active'):
            self.battle_state['player1_active'] = switch_target
        else:
            self.battle_state['player2_active'] = switch_target
        
        self._log(f"{trainer_name} sent out {switch_target.name}!")
        
        # Apply entry hazards
        self._apply_entry_hazards(switch_target)
        
        # Trigger switch-in abilities
        self._trigger_switch_in_ability(switch_target)
    
    def _execute_move(self, user, move, target):
        """Execute a move with full battle mechanics"""
        move_name = move.get('name', 'Unknown Move')
        
        # Pre-move checks
        if not self._can_use_move(user, move):
            return
        
        self._log(f"{user.name} used {move_name}!")
        
        # Decrement PP
        if hasattr(user, 'current_moves'):
            # Find and decrement PP for this move
            pass
        
        # Handle status moves first (Protect, Detect, stat changes, etc.)
        if not move.get('causes_damage', False):
            self._handle_status_move(user, target, move)
            return
        
        # Protection check (Protect, Detect, etc.)
        if self._is_protected(target, move):
            self._log(f"{target.name} protected itself!")
            return
        
        # Accuracy check
        if not self._accuracy_check(user, target, move):
            self._log(f"{user.name}'s attack missed!")
            return
        
        # Damage calculation (if damaging move)
        damage = 0
        critical_hit = False
        
        if move.get('causes_damage', False):
            # Check if this is a multi-hit move
            num_hits = self._determine_num_hits(move)
            
            if num_hits > 1:
                # Multi-hit move - show each hit
                total_damage = 0
                for hit_num in range(num_hits):
                    hit_damage, hit_crit = self._calculate_damage(user, target, move)
                    
                    if hit_crit:
                        self._log(f"Hit {hit_num + 1}! A critical hit!")
                    else:
                        self._log(f"Hit {hit_num + 1}!")
                    
                    target.take_damage(hit_damage)
                    total_damage += hit_damage
                
                self._log(f"Hit {num_hits} time(s) for {total_damage} total damage!")
                damage = total_damage
                
                # Type effectiveness message after all hits
                effectiveness = self._get_type_effectiveness(move.get('type'), target)
                if effectiveness > 1.0:
                    self._log("It's super effective!")
                elif effectiveness < 1.0 and effectiveness > 0:
                    self._log("It's not very effective...")
            else:
                # Single-hit move
                damage, critical_hit = self._calculate_damage(user, target, move)
                
                if critical_hit:
                    self._log("A critical hit!")
                
                # Type effectiveness messages
                effectiveness = self._get_type_effectiveness(move.get('type'), target)
                if effectiveness > 1.0:
                    self._log("It's super effective!")
                elif effectiveness < 1.0 and effectiveness > 0:
                    self._log("It's not very effective...")
                elif effectiveness == 0:
                    self._log("It doesn't affect {target.name}...")
                    return
                
                # Apply damage
                target.take_damage(damage)
                self._log(f"{target.name} took {damage} damage!")
        
        # Apply move effects (including drain)
        self._apply_move_effects(user, target, move, damage, critical_hit)
        
        # Check for forced switch moves (U-turn, Volt Switch, Flip Turn, etc.)
        if damage > 0 and self._is_forced_switch_move(move):
            # Only switch if the target didn't faint and user is still alive
            if target.current_hp > 0 and user.current_hp > 0:
                self.forced_switches.append(user)
                self._log(f"{user.name} went back to its trainer!")
        
        # Recoil damage
        if move.get('recoil_percentage', 0) > 0:
            recoil = (damage * move['recoil_percentage']) // 100
            user.take_damage(recoil)
            self._log(f"{user.name} took {recoil} recoil damage!")
    
    def _can_use_move(self, pokemon, move) -> bool:
        """Check if Pokemon can use the move"""
        # Sleep check
        if pokemon.status == 'sleep':
            self._log(f"{pokemon.name} is fast asleep!")
            return False
        
        # Freeze check
        if pokemon.status == 'freeze':
            self._log(f"{pokemon.name} is frozen solid!")
            return False
        
        # Paralysis check (25% chance to be fully paralyzed)
        if pokemon.status == 'paralysis':
            if random.random() < 0.25:
                self._log(f"{pokemon.name} is paralyzed! It can't move!")
                return False
        
        # Confusion check (handled separately but can prevent move)
        if pokemon.confused:
            if random.random() < 0.33:
                damage = self._calculate_confusion_damage(pokemon)
                pokemon.take_damage(damage)
                self._log(f"{pokemon.name} hurt itself in confusion! (-{damage} HP)")
                return False
        
        # Flinch check
        if hasattr(pokemon, 'flinched') and pokemon.flinched:
            self._log(f"{pokemon.name} flinched!")
            pokemon.flinched = False
            return False
        
        # Disabled/Taunted checks
        if not pokemon.can_use_move(move):
            self._log(f"{pokemon.name} can't use {move.get('name')}!")
            return False
        
        return True
    
    def _determine_num_hits(self, move) -> int:
        """Determine how many times a multi-hit move hits"""
        move_name = move.get('name', '')
        
        # Define multi-hit moves and their hit ranges
        # 2-5 hits (most common multi-hit moves)
        two_to_five_hits = [
            'Fury Attack', 'Fury Swipes', 'Double Slap', 'Comet Punch',
            'Pin Missile', 'Spike Cannon', 'Barrage', 'Bone Rush',
            'Icicle Spear', 'Rock Blast', 'Tail Slap', 'Bullet Seed',
            'Water Shuriken', 'Scale Shot'
        ]
        
        # Fixed 2 hits
        two_hits = ['Double Kick', 'Bonemerang', 'Double Iron Bash', 'Gear Grind', 'Twineedle']
        
        # Fixed 3 hits
        three_hits = ['Triple Kick', 'Triple Axel', 'Water Shuriken']  # Water Shuriken varies
        
        # Fixed 5 hits
        five_hits = ['Beat Up']  # Actually depends on team size, but simplified
        
        # Check which category this move belongs to
        if move_name in two_hits:
            return 2
        elif move_name in three_hits:
            return 3
        elif move_name in five_hits:
            return 5
        elif move_name in two_to_five_hits:
            # 2-5 hits with specific probability distribution
            # 35% for 2 hits, 35% for 3 hits, 15% for 4 hits, 15% for 5 hits
            roll = random.random()
            if roll < 0.35:
                return 2
            elif roll < 0.70:
                return 3
            elif roll < 0.85:
                return 4
            else:
                return 5
        
        # Default: single hit
        return 1
    
    def _is_forced_switch_move(self, move) -> bool:
        """Check if a move forces the user to switch out after hitting"""
        move_name = move.get('name', '')
        forced_switch_moves = [
            'U-turn', 'Volt Switch', 'Flip Turn', 'Baton Pass',
            'Parting Shot', 'Teleport'  # Gen 8+
        ]
        return move_name in forced_switch_moves
    
    def _is_protected(self, target, move) -> bool:
        """Check if target is protected from this move"""
        if not hasattr(target, 'protected') or not target.protected:
            return False
        
        # Some moves bypass protection
        if move.get('bypasses_protection', False):
            return False
        
        return True
    
    def _accuracy_check(self, user, target, move) -> bool:
        """Perform accuracy check"""
        # Moves that never miss
        if move.get('never_miss', False):
            return True
        
        move_accuracy = move.get('accuracy')
        if move_accuracy is None:
            return True  # Status moves with no accuracy always hit
        
        # Calculate accuracy modifiers
        accuracy_stage = user.stat_stages.get('accuracy', 0)
        evasion_stage = target.stat_stages.get('evasion', 0)
        
        # Stat stage modifier
        stage_diff = accuracy_stage - evasion_stage
        if stage_diff >= 0:
            modifier = (3 + stage_diff) / 3
        else:
            modifier = 3 / (3 - stage_diff)
        
        final_accuracy = move_accuracy * modifier
        
        # Roll for hit
        return random.randint(1, 100) <= final_accuracy
    
    def _calculate_damage(self, attacker, defender, move) -> Tuple[int, bool]:
        """
        Calculate damage for a move
        
        Returns: (damage, critical_hit)
        """
        # Get move power
        power = move.get('power', 0)
        
        # Handle None or 0 power (status moves, some special moves)
        if power is None or power == 0:
            return 0, False
        
        # Determine if physical or special
        category = move.get('category', 'Physical')
        if category == 'Physical':
            attack_stat = attacker.get_effective_stat('attack')
            defense_stat = defender.get_effective_stat('defense')
            
            # Burn halves physical attack
            if attacker.status == 'burn':
                attack_stat = attack_stat // 2
        else:  # Special
            attack_stat = attacker.get_effective_stat('sp_attack')
            defense_stat = defender.get_effective_stat('sp_defense')
        
        # Critical hit check
        crit_stage = 0  # Can be modified by items/abilities
        
        # Check for High Crit Ratio effect
        if hasattr(move, 'effects'):
            for effect in move.effects:
                if effect.get('field_condition') == 'HighCritRatio':
                    crit_stage = 1  # Higher crit ratio
                    break
        
        crit_chance = [1/24, 1/8, 1/2, 1/1][min(crit_stage, 3)]
        critical_hit = random.random() < crit_chance
        
        if critical_hit:
            # Ignore negative attack stages and positive defense stages
            attack_stat = attacker.attack if category == 'Physical' else attacker.sp_attack
            defense_stat = defender.defense if category == 'Physical' else defender.sp_defense
        
        # Level (assume level 50 for now, or get from Pokemon)
        level = getattr(attacker, 'level', 50)
        
        # Base damage formula
        damage = ((2 * level / 5 + 2) * power * attack_stat / defense_stat) / 50 + 2
        
        # Critical hit multiplier
        if critical_hit:
            damage = damage * 1.5
        
        # STAB (Same Type Attack Bonus)
        move_type = move.get('type')
        if move_type == attacker.type1 or move_type == attacker.type2:
            damage = damage * 1.5
        
        # Type effectiveness
        effectiveness = self._get_type_effectiveness(move_type, defender)
        damage = damage * effectiveness
        
        # Weather modifiers
        weather = self.battle_state.get('weather', {}).get('type')
        if weather == 'Sun':
            if move_type == 'Fire':
                damage = damage * 1.5
            elif move_type == 'Water':
                damage = damage * 0.5
        elif weather == 'Rain':
            if move_type == 'Water':
                damage = damage * 1.5
            elif move_type == 'Fire':
                damage = damage * 0.5
        
        # Random factor (85% to 100%)
        damage = damage * random.randint(85, 100) / 100
        
        return int(damage), critical_hit
    
    def _get_type_effectiveness(self, attack_type: str, defender) -> float:
        """Calculate type effectiveness multiplier"""
        # Simplified type chart - expand as needed
        type_chart = {
            'Fire': {'Grass': 2.0, 'Ice': 2.0, 'Bug': 2.0, 'Steel': 2.0,
                    'Water': 0.5, 'Fire': 0.5, 'Rock': 0.5, 'Dragon': 0.5},
            'Water': {'Fire': 2.0, 'Ground': 2.0, 'Rock': 2.0,
                     'Water': 0.5, 'Grass': 0.5, 'Dragon': 0.5},
            'Grass': {'Water': 2.0, 'Ground': 2.0, 'Rock': 2.0,
                     'Fire': 0.5, 'Grass': 0.5, 'Poison': 0.5, 'Flying': 0.5,
                     'Bug': 0.5, 'Dragon': 0.5, 'Steel': 0.5},
            'Electric': {'Water': 2.0, 'Flying': 2.0,
                        'Electric': 0.5, 'Grass': 0.5, 'Dragon': 0.5,
                        'Ground': 0.0},
            'Fighting': {'Normal': 2.0, 'Ice': 2.0, 'Rock': 2.0, 'Dark': 2.0, 'Steel': 2.0,
                        'Poison': 0.5, 'Flying': 0.5, 'Psychic': 0.5, 'Bug': 0.5, 'Fairy': 0.5,
                        'Ghost': 0.0},
            # Add more type matchups as needed
        }
        
        multiplier = 1.0
        
        # Check against both types
        for def_type in [defender.type1, defender.type2]:
            if def_type and attack_type in type_chart:
                multiplier *= type_chart[attack_type].get(def_type, 1.0)
        
        return multiplier
    
    def _apply_move_effects(self, user, target, move, damage: int, critical_hit: bool):
        """Apply secondary effects of a move using database-driven approach"""
        # Get effects from database
        effects = self._get_move_effects(move)
        
        # Apply each effect
        for effect in effects:
            # Check if effect should trigger
            triggers_on = effect.get('triggers_on', 'OnHit')
            
            # Skip if conditions not met
            if triggers_on == 'OnCrit' and not critical_hit:
                continue
            if triggers_on == 'OnHit' and damage == 0:
                continue
            
            self._apply_single_effect(user, target, effect, damage, critical_hit)
    
    def _get_move_effects(self, move):
        """Query move effects from database or Move object"""
        # First, check if move has effects already loaded (Move object)
        if hasattr(move, 'effects'):
            effects = move.effects
            if effects:
                return effects
            else:
                self._log(f"(Debug: Move object '{getattr(move, 'name', 'unknown')}' has no effects)")
                return []
        
        # Fallback: try to get from dict
        if isinstance(move, dict) and 'effects' in move:
            return move.get('effects', [])
        
        # Last resort: query database
        if not self.move_repo:
            self._log("(Debug: No move repository available)")
            return []
        
        move_id = move.get('id')
        if not move_id:
            self._log(f"(Debug: Move has no ID: {move.get('name')}")
            return []
        
        try:
            move_with_effects = self.move_repo.get_with_effects(move_id)
            effects = move_with_effects.get('effects', [])
            if not effects:
                self._log(f"(Debug: Move ID {move_id} '{move.get('name')}' has no effects in database)")
            return effects
        except Exception as e:
            self._log(f"(Debug: Error retrieving effects: {e})")
            return []
    
    def _handle_status_move(self, user, target, move):
        """Handle non-damaging status moves using database-driven approach"""
        # Get effects from database
        effects = self._get_move_effects(move)
        
        if not effects:
            # Fallback: if no database effects, just log
            move_name = move.get('name', 'a move')
            self._log(f"{user.name} used {move_name}!")
            self._log(f"(Debug: No effects found for move ID {move.get('id')})")
            return
        
        # Apply each effect
        for effect in effects:
            self._apply_single_effect(user, target, effect, 0, False)
    
    def _apply_single_effect(self, user, target, effect, damage_dealt=0, critical_hit=False):
        """Apply a single move effect based on database data"""
        effect_type = effect.get('effect_type')
        effect_target_str = effect.get('effect_target', 'Target')
        probability = effect.get('probability', 100)
        
        self._log(f"(Debug: Processing effect - type: {effect_type}, target: {effect_target_str}, probability: {probability}%)")
        
        # Probability check
        if random.randint(1, 100) > probability:
            self._log(f"(Debug: Effect failed probability check)")
            return
        
        # Determine who receives the effect
        effect_target = target if effect_target_str == 'Target' else user
        
        self._log(f"(Debug: Applying {effect_type} to {effect_target.name})")
        
        # Apply based on effect type
        if effect_type == 'STAT_CHANGE':
            self._apply_stat_change_effect(effect_target, effect)
        elif effect_type == 'STATUS':
            self._apply_status_effect(effect_target, effect)
        elif effect_type == 'HEAL':
            self._apply_heal_effect(user, effect, damage_dealt)
        elif effect_type == 'WEATHER':
            self._apply_weather_effect(effect)
        elif effect_type == 'FIELD_EFFECT':
            self._apply_field_effect(effect)
        elif effect_type == 'OTHER':
            self._apply_other_effect(user, target, effect)
    
    def _apply_stat_change_effect(self, pokemon, effect):
        """Apply stat change from database effect"""
        stat_to_change = effect.get('stat_to_change', '')
        stat_change_amount = effect.get('stat_change_amount', 0)
        
        if stat_to_change == 'All':
            # Raise/lower all stats
            for stat in ['attack', 'defense', 'sp_attack', 'sp_defense', 'speed']:
                pokemon.modify_stat_stage(stat, stat_change_amount)
            self._log(f"{pokemon.name}'s stats {'rose' if stat_change_amount > 0 else 'fell'}!")
        elif stat_to_change:
            # Convert database stat names to Pokemon attribute names
            stat_map = {
                'Attack': 'attack',
                'Defense': 'defense',
                'SpAttack': 'sp_attack',
                'SpDefense': 'sp_defense',
                'Speed': 'speed',
                'Accuracy': 'accuracy',
                'Evasion': 'evasion'
            }
            stat_key = stat_map.get(stat_to_change, stat_to_change.lower())
            pokemon.modify_stat_stage(stat_key, stat_change_amount)
            
            # Generate appropriate message
            if stat_to_change == 'SpAttack':
                stat_display = 'Special Attack'
            elif stat_to_change == 'SpDefense':
                stat_display = 'Special Defense'
            else:
                stat_display = stat_to_change
            
            if abs(stat_change_amount) >= 2:
                change_word = 'sharply rose' if stat_change_amount > 0 else 'harshly fell'
            else:
                change_word = 'rose' if stat_change_amount > 0 else 'fell'
            self._log(f"{pokemon.name}'s {stat_display} {change_word}!")
    
    def _apply_status_effect(self, pokemon, effect):
        """Apply status condition from database effect"""
        status_condition = effect.get('status_condition', 'None')
        
        self._log(f"(Debug: Applying status effect - condition: {status_condition}, target: {pokemon.name})")
        
        if status_condition == 'None' or not status_condition:
            self._log(f"(Debug: Status condition is None or empty)")
            return
        
        # Check if Pokemon can be statused
        if pokemon.status and pokemon.status != '':
            self._log(f"But it failed!")
            self._log(f"(Debug: {pokemon.name} already has status: {pokemon.status})")
            return
        
        # Map database status names to Pokemon status names
        status_map = {
            'Burn': 'burn',
            'Paralysis': 'paralysis',
            'Freeze': 'freeze',
            'Poison': 'poison',
            'Sleep': 'sleep',
            'Confusion': 'confusion'
        }
        status_name = status_map.get(status_condition, status_condition.lower())
        
        self._log(f"(Debug: Mapped '{status_condition}' to '{status_name}')")
        
        pokemon.apply_status(status_name)
        
        # Generate message
        status_messages = {
            'burn': 'was burned',
            'paralysis': 'was paralyzed',
            'freeze': 'was frozen solid',
            'poison': 'was poisoned',
            'badly_poison': 'was badly poisoned',
            'sleep': 'fell asleep',
            'confusion': 'became confused'
        }
        message = status_messages.get(status_name, f'was afflicted with {status_name}')
        self._log(f"{pokemon.name} {message}!")
    
    def _apply_heal_effect(self, pokemon, effect, damage_dealt=0):
        """Apply healing from database effect"""
        heal_percentage = effect.get('heal_percentage', 0)
        
        if heal_percentage > 0:
            # Check if it's drain (heals based on damage) or direct heal
            if damage_dealt > 0:
                # Drain effect - heal based on damage
                heal_amount = int(damage_dealt * heal_percentage / 100)
            else:
                # Direct heal - heal based on max HP
                heal_amount = int(pokemon.max_hp * heal_percentage / 100)
            
            actual_heal = min(heal_amount, pokemon.max_hp - pokemon.current_hp)
            pokemon.current_hp = min(pokemon.max_hp, pokemon.current_hp + actual_heal)
            
            if actual_heal > 0:
                if damage_dealt > 0:
                    self._log(f"{pokemon.name} drained {actual_heal} HP!")
                else:
                    self._log(f"{pokemon.name} restored {actual_heal} HP!")
            else:
                self._log(f"{pokemon.name}'s HP is already full!")
    
    def _apply_weather_effect(self, effect):
        """Apply weather change from database effect"""
        weather_type = effect.get('weather_type', 'None')
        
        if weather_type and weather_type != 'None':
            self.battle_state['weather'] = {
                'type': weather_type,
                'turns_remaining': 5
            }
            self._log(f"{weather_type} began!")
    
    def _apply_field_effect(self, effect):
        """Apply field effect from database effect"""
        field_condition = effect.get('field_condition')
        
        if field_condition:
            # Handle Break Screens (removes protective screens)
            if field_condition == 'BreakScreens':
                if 'field_effects' not in self.battle_state:
                    self.battle_state['field_effects'] = {}
                    
                removed_any = False
                screens_to_remove = ['lightscreen', 'reflect', 'auroraveil']
                for screen in screens_to_remove:
                    if screen in self.battle_state['field_effects']:
                        del self.battle_state['field_effects'][screen]
                        removed_any = True
                if removed_any:
                    self._log("The protective screens were shattered!")
                return
            
            # Store in field_effects
            if 'field_effects' not in self.battle_state:
                self.battle_state['field_effects'] = {}
            
            # Most field effects last 5 turns
            self.battle_state['field_effects'][field_condition.lower()] = {
                'active': True,
                'turns_remaining': 5
            }
            self._log(f"{field_condition} was set up!")
    
    def _apply_other_effect(self, user, target, effect):
        """Apply special effects from database"""
        effect_name = effect.get('effect_name', '')
        field_condition = effect.get('field_condition', '')
        
        # Flinch effect
        if 'Flinch' in effect_name or effect_name == 'Flinch':
            # Only flinch if target hasn't acted yet this turn
            if not hasattr(target, 'has_acted'):
                target.has_acted = False
            
            if not target.has_acted:
                target.flinched = True
                self._log(f"{target.name} flinched!")
            return
        
        # Confusion effect
        if 'Confusion' in effect_name or 'Confuse' in effect_name:
            # Apply confusion as a status condition
            if not target.status or target.status == '':
                target.apply_status('confusion')
                self._log(f"{target.name} became confused!")
            else:
                self._log(f"But it failed!")
            return
        
        # OHKO moves
        if field_condition == 'OHKO' or 'OHKO' in effect_name:
            # One-Hit KO - reduce target to 0 HP
            damage = target.current_hp
            target.take_damage(damage)
            self._log(f"It's a one-hit KO!")
            return
        
        # Protection effects
        if 'Protect' in effect_name:
            user.protected = True
            self._log(f"{user.name} protected itself!")
        # Add more special cases as needed
    
    
    def _calculate_confusion_damage(self, pokemon) -> int:
        """Calculate self-inflicted confusion damage"""
        # Confusion damage is typeless 40 power physical move
        attack = pokemon.get_effective_stat('attack')
        defense = pokemon.get_effective_stat('defense')
        level = getattr(pokemon, 'level', 50)
        
        damage = ((2 * level / 5 + 2) * 40 * attack / defense) / 50 + 2
        return int(damage)
    
    # ========== PHASE 3: END-OF-TURN EFFECTS ==========
    
    def _phase_end_turn(self):
        """Execute all end-of-turn effects"""
        # self._log("=== End of Turn ===")  # Don't clutter output
        
        # 1. Weather damage (again for some mechanics)
        # Already handled in pre-turn
        
        # 2. End-of-turn abilities
        self._process_end_of_turn_abilities()
        
        # 3. End-of-turn items
        self._process_end_of_turn_items()
        
        # 4. Volatile status effects
        self._process_volatile_effects()
        
        # 5. Decrement turn counters
        self._decrement_turn_counters()
    
    def _process_end_of_turn_abilities(self):
        """Process abilities that trigger at end of turn"""
        for pokemon in self._get_all_active_pokemon():
            if pokemon.current_hp <= 0:
                continue
            
            ability = pokemon.ability if hasattr(pokemon, 'ability') else None
            if not ability:
                continue
            
            # Bad Dreams (damages sleeping opponents)
            if ability == 'Bad Dreams':
                for opponent in self._get_opponents(pokemon):
                    if opponent.status == 'sleep':
                        damage = opponent.max_hp // 8
                        opponent.take_damage(damage)
                        self._log(f"{opponent.name} was tormented by Bad Dreams! (-{damage} HP)")
            
            # Ice Body (heal in hail)
            elif ability == 'Ice Body' and self.battle_state.get('weather', {}).get('type') == 'Hail':
                heal_amount = pokemon.max_hp // 16
                pokemon.heal(heal_amount)
                self._log(f"{pokemon.name} restored HP with Ice Body!")
            
            # Rain Dish (heal in rain)
            elif ability == 'Rain Dish' and self.battle_state.get('weather', {}).get('type') == 'Rain':
                heal_amount = pokemon.max_hp // 16
                pokemon.heal(heal_amount)
                self._log(f"{pokemon.name} restored HP with Rain Dish!")
    
    def _process_end_of_turn_items(self):
        """Process held items at end of turn"""
        for pokemon in self._get_all_active_pokemon():
            if pokemon.current_hp <= 0:
                continue
            
            held_item = pokemon.held_item if hasattr(pokemon, 'held_item') else None
            if not held_item:
                continue
            
            # Shell Bell healing is handled after damage dealt
            pass
    
    def _process_volatile_effects(self):
        """Process end-of-turn volatile effects"""
        for pokemon in self._get_all_active_pokemon():
            if pokemon.current_hp <= 0:
                continue
            
            # Let Pokemon class handle its own end-of-turn processing
            if hasattr(pokemon, 'process_end_of_turn_effects'):
                effects = pokemon.process_end_of_turn_effects()
                
                # Log the effects
                if effects.get('burn_damage', 0) > 0:
                    self._log(f"{pokemon.name} was hurt by its burn!")
                if effects.get('poison_damage', 0) > 0:
                    self._log(f"{pokemon.name} was hurt by poison!")
                if effects.get('leech_seed_damage', 0) > 0:
                    self._log(f"{pokemon.name} was hurt by Leech Seed!")
                if effects.get('trap_damage', 0) > 0:
                    self._log(f"{pokemon.name} was hurt by the trap!")
                if effects.get('curse_damage', 0) > 0:
                    self._log(f"{pokemon.name} was hurt by the curse!")
                if effects.get('aqua_ring_heal', 0) > 0:
                    self._log(f"{pokemon.name} restored HP with Aqua Ring!")
                if effects.get('ingrain_heal', 0) > 0:
                    self._log(f"{pokemon.name} restored HP with Ingrain!")
                if effects.get('woke_up'):
                    self._log(f"{pokemon.name} woke up!")
                if effects.get('thawed'):
                    self._log(f"{pokemon.name} thawed out!")
                if effects.get('fell_asleep'):
                    self._log(f"{pokemon.name} fell asleep from Yawn!")
    
    def _decrement_turn_counters(self):
        """Decrement all active turn counters"""
        # Weather
        weather = self.battle_state.get('weather', {})
        if weather.get('turns_remaining', 0) > 0:
            weather['turns_remaining'] -= 1
        
        # Field effects
        field_effects = self.battle_state.get('field_effects', {})
        
        # Terrain
        terrain = field_effects.get('terrain', {})
        if terrain.get('turns_remaining', 0) > 0:
            terrain['turns_remaining'] -= 1
        
        # Trick Room
        if field_effects.get('trick_room_turns', 0) > 0:
            field_effects['trick_room_turns'] -= 1
        
        # Gravity
        if field_effects.get('gravity_turns', 0) > 0:
            field_effects['gravity_turns'] -= 1
        
        # Side effects (Reflect, Light Screen, Tailwind, etc.)
        for side in ['player1', 'player2']:
            side_effects = self.battle_state.get(f'{side}_side_effects', {})
            
            if side_effects.get('reflect_turns', 0) > 0:
                side_effects['reflect_turns'] -= 1
                if side_effects['reflect_turns'] == 0:
                    self._log(f"{side}'s Reflect wore off!")
            
            if side_effects.get('light_screen_turns', 0) > 0:
                side_effects['light_screen_turns'] -= 1
                if side_effects['light_screen_turns'] == 0:
                    self._log(f"{side}'s Light Screen wore off!")
            
            if side_effects.get('tailwind_turns', 0) > 0:
                side_effects['tailwind_turns'] -= 1
                if side_effects['tailwind_turns'] == 0:
                    self._log(f"{side}'s Tailwind wore off!")
        
        # Increment turn counter
        self.battle_state['turn_count'] = self.battle_state.get('turn_count', 0) + 1
    
    # ========== PHASE 4: HANDLE FAINTS ==========
    
    def _phase_handle_faints(self):
        """Handle Pokemon that fainted during the turn"""
        # Collect all fainted Pokemon
        for pokemon in self._get_all_active_pokemon():
            if pokemon.current_hp <= 0 and pokemon not in self.fainted_pokemon:
                self.fainted_pokemon.append(pokemon)
                self._log(f"{pokemon.name} fainted!")
        
        # In a real implementation, would prompt for replacements
        # For now, just log the faints
    
    # ========== PHASE 5: WIN CONDITION ==========
    
    def _check_win_condition(self) -> Optional[str]:
        """Check if either player has won"""
        player1_has_usable = self._has_usable_pokemon('player1')
        player2_has_usable = self._has_usable_pokemon('player2')
        
        if not player1_has_usable and not player2_has_usable:
            self._log("It's a draw!")
            return 'draw'
        elif not player1_has_usable:
            self._log("Player 2 wins!")
            return 'player2'
        elif not player2_has_usable:
            self._log("Player 1 wins!")
            return 'player1'
        
        return None
    
    def _has_usable_pokemon(self, player: str) -> bool:
        """Check if player has any Pokemon that can battle"""
        team = self.battle_state.get(f'{player}_team', [])
        for pokemon in team:
            if pokemon.current_hp > 0:
                return True
        return False
    
    # ========== HELPER METHODS ==========
    
    def _get_all_active_pokemon(self) -> List:
        """Get all currently active Pokemon"""
        active = []
        if self.battle_state.get('player1_active'):
            active.append(self.battle_state['player1_active'])
        if self.battle_state.get('player2_active'):
            active.append(self.battle_state['player2_active'])
        return active
    
    def _get_opponents(self, pokemon) -> List:
        """Get opponent Pokemon"""
        if pokemon == self.battle_state.get('player1_active'):
            return [self.battle_state.get('player2_active')]
        else:
            return [self.battle_state.get('player1_active')]
    
    def _get_side_effects(self, pokemon) -> Dict:
        """Get side effects for the Pokemon's side"""
        if pokemon == self.battle_state.get('player1_active'):
            return self.battle_state.get('player1_side_effects', {})
        else:
            return self.battle_state.get('player2_side_effects', {})
    
    def _can_switch(self, pokemon) -> bool:
        """Check if Pokemon can switch out"""
        # Check for trapping moves/abilities
        if hasattr(pokemon, 'trapped') and pokemon.trapped:
            return False
        
        # Ingrain prevents switching
        if hasattr(pokemon, 'ingrain') and pokemon.ingrain:
            return False
        
        return True
    
    def _apply_entry_hazards(self, pokemon):
        """Apply entry hazard damage when Pokemon switches in"""
        # Determine which side
        if pokemon == self.battle_state.get('player1_active'):
            hazards = self.battle_state.get('player1_side_effects', {}).get('hazards', {})
        else:
            hazards = self.battle_state.get('player2_side_effects', {}).get('hazards', {})
        
        # Stealth Rock
        if hazards.get('stealth_rock'):
            # Calculate type effectiveness against Rock type
            effectiveness = self._get_type_effectiveness('Rock', pokemon)
            damage = int(pokemon.max_hp * effectiveness / 8)
            pokemon.take_damage(damage)
            self._log(f"{pokemon.name} was hurt by Stealth Rock! (-{damage} HP)")
        
        # Spikes
        spikes_layers = hazards.get('spikes', 0)
        if spikes_layers > 0 and pokemon.type1 != 'Flying' and pokemon.type2 != 'Flying':
            damage = pokemon.max_hp * spikes_layers // 8
            pokemon.take_damage(damage)
            self._log(f"{pokemon.name} was hurt by Spikes! (-{damage} HP)")
        
        # Toxic Spikes
        toxic_spikes_layers = hazards.get('toxic_spikes', 0)
        if toxic_spikes_layers > 0 and pokemon.status == 'healthy':
            if pokemon.type1 != 'Flying' and pokemon.type2 != 'Flying':
                if toxic_spikes_layers == 1:
                    pokemon.apply_status('poison')
                    self._log(f"{pokemon.name} was poisoned by Toxic Spikes!")
                else:
                    pokemon.apply_status('badly_poison')
                    self._log(f"{pokemon.name} was badly poisoned by Toxic Spikes!")
    
    def _trigger_switch_in_ability(self, pokemon):
        """Trigger ability when Pokemon switches in"""
        ability = pokemon.ability if hasattr(pokemon, 'ability') else None
        if not ability:
            return
        
        # Intimidate
        if ability == 'Intimidate':
            for opponent in self._get_opponents(pokemon):
                opponent.modify_stat_stage('attack', -1)
                self._log(f"{pokemon.name}'s Intimidate lowered {opponent.name}'s Attack!")
        
        # Weather abilities
        elif ability == 'Drought':
            self.battle_state['weather'] = {'type': 'Sun', 'turns_remaining': 5}
            self._log(f"{pokemon.name}'s Drought intensified the sun!")
        elif ability == 'Drizzle':
            self.battle_state['weather'] = {'type': 'Rain', 'turns_remaining': 5}
            self._log(f"{pokemon.name}'s Drizzle made it rain!")
        elif ability == 'Sand Stream':
            self.battle_state['weather'] = {'type': 'Sandstorm', 'turns_remaining': 5}
            self._log(f"{pokemon.name}'s Sand Stream whipped up a sandstorm!")
        elif ability == 'Snow Warning':
            self.battle_state['weather'] = {'type': 'Hail', 'turns_remaining': 5}
            self._log(f"{pokemon.name}'s Snow Warning made it hail!")
    
    def _log(self, message: str):
        """Add message to turn log"""
        self.turn_log.append(message)
