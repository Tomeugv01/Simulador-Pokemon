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

try:
    from models.ability import AbilityHandler, CONTACT_OVERRIDE_NO
except ImportError:
    try:
        from ability import AbilityHandler, CONTACT_OVERRIDE_NO
    except ImportError:
        AbilityHandler = None
        CONTACT_OVERRIDE_NO = set()

try:
    from models.constants import TYPE_CHART, get_type_effectiveness as _calc_type_eff
except ImportError:
    try:
        from constants import TYPE_CHART, get_type_effectiveness as _calc_type_eff
    except ImportError:
        TYPE_CHART = {}
        _calc_type_eff = None


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

    # *** PRIVATE ***

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
        self.just_switched_in = []  # Track Pokemon that switched in this turn

    # *** PUBLIC ***

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
        self.just_switched_in = []  # Clear switches from previous turn
        
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

    # *** PRIVATE ***

    def _accuracy_check(self, user, target, move) -> bool:
        """Perform accuracy check with ability integration"""
        # Moves that never miss
        if move.get('never_miss', False):
            return True
        
        # Check for Never Miss effect from database
        effects = self._get_move_effects(move)
        for effect in effects:
            if effect.get('effect_name', '') == 'Never Miss':
                return True
        
        # Check for Lock-On / Mind Reader (user has lock_on flag)
        if hasattr(user, 'lock_on') and user.lock_on:
            user.lock_on = False  # Consumed on next attack
            return True
        
        move_accuracy = move.get('accuracy')
        if move_accuracy is None:
            return True  # Status moves with no accuracy always hit
        
        # --- Ability: Modify accuracy (Compound Eyes, No Guard, Sand Veil, etc.) ---
        if AbilityHandler:
            original_acc = move_accuracy
            move_accuracy, always_hit = AbilityHandler.modify_accuracy(
                user, target, move_accuracy, move, self.battle_state)
            if always_hit:
                self._log(f"(Ability: No Guard \u2014 move always hits)")
                return True
            if move_accuracy != original_acc:
                self._log(f"(Ability: Accuracy modified {original_acc} \u2192 {move_accuracy})")
        
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
    # region Effects

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

    def _apply_field_effect(self, effect):
        """Apply field effect from database effect"""
        field_condition = effect.get('field_condition')
        effect_name = effect.get('effect_name', '')
        
        if not field_condition and not effect_name:
            return
        
        condition = field_condition or effect_name
        
        # Initialize field_effects if needed
        if 'field_effects' not in self.battle_state:
            self.battle_state['field_effects'] = {}
        
        # === Haze: Reset all stat changes ===
        if condition in ('Haze', 'haze') or 'Haze' in effect_name:
            for pokemon in self._get_all_active_pokemon():
                if hasattr(pokemon, 'stat_stages'):
                    for stat in pokemon.stat_stages:
                        pokemon.stat_stages[stat] = 0
            self._log("All stat changes were reset!")
            return
        
        # === Remove Hazards ===
        if condition == 'RemoveHazards' or 'Remove Hazards' in effect_name:
            # Remove hazards from both sides
            for side in ['player1_side_effects', 'player2_side_effects']:
                side_effects = self.battle_state.get(side, {})
                if 'hazards' in side_effects:
                    side_effects['hazards'] = {}
            # Also remove screens (Brick Break / Psychic Fangs)
            self._log("The hazards were removed!")
            return
        
        # === Break Screens ===
        if condition == 'BreakScreens':
            removed_any = False
            for side in ['player1_side_effects', 'player2_side_effects']:
                side_effects = self.battle_state.get(side, {})
                for screen in ['reflect_turns', 'light_screen_turns', 'aurora_veil_turns']:
                    if side_effects.get(screen, 0) > 0:
                        side_effects[screen] = 0
                        removed_any = True
            if removed_any:
                self._log("The protective screens were shattered!")
            return
        
        # === Reflect ===
        if condition == 'Reflect' or 'Reflect' in effect_name:
            # Determine which side sets it
            # In the current flow, effect applies to user's side
            # We need to figure out which player is using it
            for side in ['player1_side_effects', 'player2_side_effects']:
                if side not in self.battle_state:
                    self.battle_state[side] = {}
            # For simplicity, store in 'user' side - the caller context determines side
            # We'll set it for the active user's side
            p1 = self.battle_state.get('player1_active')
            p2 = self.battle_state.get('player2_active')
            # Check which side recently used the move
            target_str = effect.get('effect_target', 'UserSide')
            if target_str in ('UserSide', 'User'):
                # This is set on user's side - handled by the caller
                pass
            
            # Set reflect on both sides as a default (will be refined by caller context)
            for side_key in ['player1_side_effects', 'player2_side_effects']:
                side = self.battle_state.get(side_key, {})
                if side_key not in self.battle_state:
                    self.battle_state[side_key] = {}
            # Actually, just set it in field_effects and let damage calc check
            self.battle_state['field_effects']['reflect'] = {'active': True, 'turns_remaining': 5}
            # Also set reflect_turns for the side effect approach used in damage calc
            self._set_user_side_effect('reflect_turns', 5)
            self._log("Reflect raised the physical defense of the team!")
            return
        
        # === Light Screen ===
        if condition == 'Light Screen' or 'Light Screen' in effect_name:
            self.battle_state['field_effects']['lightscreen'] = {'active': True, 'turns_remaining': 5}
            self._set_user_side_effect('light_screen_turns', 5)
            self._log("Light Screen raised the special defense of the team!")
            return
        
        # === Aurora Veil ===
        if condition == 'Aurora Veil' or 'Aurora Veil' in effect_name:
            weather = self.battle_state.get('weather', {}).get('type')
            if weather == 'Hail':
                self.battle_state['field_effects']['auroraveil'] = {'active': True, 'turns_remaining': 5}
                self._log("Aurora Veil made the team stronger against both physical and special moves!")
            else:
                self._log("But it failed! (requires Hail)")
            return
        
        # === Safeguard ===
        if condition == 'Safeguard' or 'Safeguard' in effect_name:
            self.battle_state['field_effects']['safeguard'] = {'active': True, 'turns_remaining': 5}
            self._log("The team became cloaked in a protective veil!")
            return
        
        # === Mist ===
        if condition == 'Mist' or 'Mist' in effect_name:
            self.battle_state['field_effects']['mist'] = {'active': True, 'turns_remaining': 5}
            self._log("The team became shrouded in mist!")
            return
        
        # === Lucky Chant ===
        if condition == 'Lucky Chant' or 'Lucky Chant' in effect_name:
            self.battle_state['field_effects']['luckychant'] = {'active': True, 'turns_remaining': 5}
            self._log("The Lucky Chant shielded the team from critical hits!")
            return
        
        # === Tailwind ===
        if condition == 'Tailwind' or 'Tailwind' in effect_name:
            self._set_user_side_effect('tailwind_turns', 4)
            self._set_user_side_effect('tailwind', True)
            self._log("The tailwind blew from behind the team!")
            return
        
        # === Trick Room ===
        if condition == 'Trick Room' or 'Trick Room' in effect_name:
            field_effects = self.battle_state.get('field_effects', {})
            if field_effects.get('trick_room', False):
                field_effects['trick_room'] = False
                field_effects['trick_room_turns'] = 0
                self._log("The twisted dimensions returned to normal!")
            else:
                field_effects['trick_room'] = True
                field_effects['trick_room_turns'] = 5
                self._log("The dimensions were twisted!")
            return
        
        # === Wide Guard ===
        if condition == 'Wide Guard' or 'Wide Guard' in effect_name:
            self.battle_state['field_effects']['wideguard'] = {'active': True, 'turns_remaining': 1}
            self._log("Wide Guard protected the team!")
            return
        
        # === Terrain Effects ===
        terrain_types = {
            'Electric Terrain': 'Electric',
            'Grassy Terrain': 'Grassy',
            'Misty Terrain': 'Misty',
            'Psychic Terrain': 'Psychic'
        }
        for terrain_name, terrain_type in terrain_types.items():
            if condition == terrain_name or terrain_name in effect_name:
                field_effects = self.battle_state.get('field_effects', {})
                field_effects['terrain'] = {'type': terrain_type, 'turns_remaining': 5}
                self.battle_state['field_effects'] = field_effects
                self._log(f"{terrain_type} Terrain covers the battlefield!")
                return
        
        # === Hazard effects (Spikes, Toxic Spikes, Stealth Rock, Sticky Web) ===
        if condition in ('Spikes', 'ToxicSpikes', 'StealthRock', 'Sticky Web',
                         'Set Stealth Rock', 'Set Spikes', 'Set Toxic Spikes'):
            # Determine opponent side
            opp_side = self._get_opponent_side_key()
            if opp_side not in self.battle_state:
                self.battle_state[opp_side] = {}
            if 'hazards' not in self.battle_state[opp_side]:
                self.battle_state[opp_side]['hazards'] = {}
            
            hazards = self.battle_state[opp_side]['hazards']
            
            if condition in ('Spikes', 'Set Spikes'):
                current = hazards.get('spikes', 0)
                if current < 3:
                    hazards['spikes'] = current + 1
                    self._log("Spikes were scattered on the ground!")
                else:
                    self._log("But it failed! (max layers)")
            elif condition in ('ToxicSpikes', 'Set Toxic Spikes'):
                current = hazards.get('toxic_spikes', 0)
                if current < 2:
                    hazards['toxic_spikes'] = current + 1
                    self._log("Poison spikes were scattered on the ground!")
                else:
                    self._log("But it failed! (max layers)")
            elif condition in ('StealthRock', 'Set Stealth Rock'):
                if not hazards.get('stealth_rock'):
                    hazards['stealth_rock'] = True
                    self._log("Pointed stones float in the air!")
                else:
                    self._log("But it failed! (already set)")
            elif condition == 'Sticky Web':
                if not hazards.get('sticky_web'):
                    hazards['sticky_web'] = True
                    self._log("A sticky web was laid out on the ground!")
                else:
                    self._log("But it failed! (already set)")
            return
        
        # === Generic field effect fallback ===
        self.battle_state['field_effects'][condition.lower()] = {
            'active': True,
            'turns_remaining': 5
        }
        self._log(f"{condition} was set up!")

    def _apply_hail_damage(self):
        """Apply hail damage to non-immune Pokemon"""
        for pokemon in self._get_all_active_pokemon():
            # Immune type: Ice
            if pokemon.type1 != 'Ice' and pokemon.type2 != 'Ice':
                # --- Ability: Weather immunity (Overcoat, Ice Body, Magic Guard, etc.) ---
                if AbilityHandler and AbilityHandler.check_weather_immunity(pokemon, 'Hail'):
                    self._log(f"(Ability: {pokemon.name}'s {pokemon.ability} grants Hail immunity)")
                    continue
                if AbilityHandler and AbilityHandler.check_indirect_damage_immunity(pokemon):
                    self._log(f"(Ability: {pokemon.name}'s {pokemon.ability} blocks indirect damage)")
                    continue
                damage = pokemon.max_hp // 16
                pokemon.take_damage(damage)
                self._log(f"{pokemon.name} is buffeted by the hail! (-{damage} HP)")

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

    def _apply_other_effect(self, user, target, effect):
        """Apply special effects from database"""
        effect_name = effect.get('effect_name', '')
        field_condition = effect.get('field_condition', '')
        
        # === Flinch ===
        if 'Flinch' in effect_name:
            if not hasattr(target, 'has_acted'):
                target.has_acted = False
            if not target.has_acted:
                target.flinched = True
                self._log(f"{target.name} flinched!")
            return
        
        # === Confusion ===
        if 'Confusion' in effect_name or 'Confuse' in effect_name:
            if not hasattr(target, 'confused') or not target.confused:
                target.confused = True
                target.confusion_turns = random.randint(1, 4)
                self._log(f"{target.name} became confused!")
            else:
                self._log(f"But it failed! ({target.name} is already confused)")
            return
        
        # === OHKO ===
        if field_condition == 'OHKO' or 'OHKO' in effect_name:
            damage = target.current_hp
            target.take_damage(damage)
            self._log(f"It's a one-hit KO!")
            return
        
        # === Yawn ===
        if 'Yawn' in effect_name:
            if not target.status or target.status == '' or target.status == 'healthy':
                target.yawn = True
                target.yawn_turns = 1
                self._log(f"{target.name} grew drowsy!")
            else:
                self._log(f"But it failed!")
            return
        
        # === Protect ===
        if 'Protect' in effect_name:
            user.protected = True
            self._log(f"{user.name} protected itself!")
            return
        
        # === High Crit / Always Crit ===
        # These are handled in _calculate_damage, no runtime action needed
        if 'High Crit' in effect_name or 'Always Crit' in effect_name:
            return
        
        # === Never Miss ===
        # Handled in _accuracy_check, no runtime action needed
        if 'Never Miss' in effect_name:
            return
        
        # === Priority +1 / +2 ===
        # Priority is already set on the move itself in the DB
        if 'Priority' in effect_name:
            return
        
        # === Variable Power ===
        # Handled in damage calculation for applicable moves, or is move-specific
        if 'Variable Power' in effect_name:
            return
        
        # === Damage Doubling / Speed Dependent / Pursuit Damage ===
        # Handled in _calculate_damage
        if 'Damage Doubling' in effect_name or 'Speed Dependent' in effect_name or 'Pursuit Damage' in effect_name:
            return
        
        # === Ignore Stat Changes ===
        # Handled conceptually in damage calc; no extra runtime needed
        if 'Ignore Stat Changes' in effect_name:
            return
        
        # === Item Dependent ===
        if 'Item Dependent' in effect_name:
            return
        
        # === Splash (no effect) ===
        if 'Splash' in effect_name:
            self._log("But nothing happened!")
            return
        
        # === Self Destruct (user faints) ===
        if 'Self Destruct' in effect_name:
            user.take_damage(user.current_hp)
            self._log(f"{user.name} fainted!")
            return
        
        # === Multi Hit ===
        if 'Multi Hit' in effect_name:
            # Multi-hit is handled in _determine_num_hits and _execute_move
            return
        
        # === Recharge Turn ===
        if 'Recharge Turn' in effect_name:
            user.recharging = True
            self._log(f"{user.name} must recharge!")
            return
        
        # === Charge Turn (Solar Beam, Skull Bash, etc.) ===
        if 'Charge Turn' in effect_name:
            # In a simplified model, charge moves just execute immediately
            # Full implementation would skip this turn and attack next
            return
        
        # === Trap ===
        if 'Trap' in effect_name:
            target.trapped = True
            if '4-5' in effect_name:
                target.trap_turns = random.randint(4, 5)
            else:
                target.trap_turns = random.randint(2, 5)
            self._log(f"{target.name} was trapped!")
            return
        
        # === Prevent Switching ===
        if 'Prevent Switching' in effect_name:
            target.trapped = True
            target.trap_turns = 999
            self._log(f"{target.name} can no longer escape!")
            return
        
        # === Switch Out (U-turn, Volt Switch) ===
        if 'Switch Out' in effect_name:
            # Handled in _execute_move via _is_forced_switch_move
            return
        
        # === Force Switch (Roar, Whirlwind, Dragon Tail) ===
        if 'Force Switch' in effect_name:
            self._log(f"{target.name} was forced to switch!")
            return
        
        # === Attract ===
        if 'Attract' in effect_name:
            if not hasattr(target, 'attracted'):
                target.attracted = False
            target.attracted = True
            self._log(f"{target.name} fell in love!")
            return
        
        # === Belly Drum ===
        if 'Belly Drum' in effect_name:
            cost = user.max_hp // 2
            if user.current_hp > cost:
                user.take_damage(cost)
                # Maximize attack
                if hasattr(user, 'stat_stages'):
                    user.stat_stages['attack'] = 6
                self._log(f"{user.name} cut its own HP and maximized Attack!")
            else:
                self._log(f"But it failed! (not enough HP)")
            return
        
        # === Destiny Bond ===
        if 'Destiny Bond' in effect_name:
            user.destiny_bond = True
            self._log(f"{user.name} is trying to take its foe with it!")
            return
        
        # === Focus Energy ===
        if 'Focus Energy' in effect_name:
            user.focus_energy = True
            self._log(f"{user.name} is getting pumped!")
            return
        
        # === Lock On / Mind Reader ===
        if 'Lock On' in effect_name:
            user.lock_on = True
            self._log(f"{user.name} took aim at {target.name}!")
            return
        
        # === Baton Pass ===
        if 'Baton Pass' in effect_name:
            # Mark for switch but keep stat changes
            self.forced_switches.append(user)
            self._log(f"{user.name} passed its boosts!")
            return
        
        # === Counter / Mirror Coat / Metal Burst ===
        if effect_name in ('Counter', 'Mirror Coat', 'Metal Burst'):
            # These return damage based on last hit received
            last_damage = getattr(user, 'last_damage_taken', 0)
            if last_damage > 0:
                multiplier = 1.5 if effect_name == 'Metal Burst' else 2.0
                return_damage = int(last_damage * multiplier)
                target.take_damage(return_damage)
                self._log(f"{target.name} took {return_damage} damage from {effect_name}!")
            else:
                self._log(f"But it failed!")
            return
        
        # === Bide ===
        if 'Bide' in effect_name:
            # Simplified: user endures for 2 turns then returns double damage
            self._log(f"{user.name} is storing energy!")
            return
        
        # === Copy Stat Stages (Psych Up) ===
        if 'Copy Stat Stages' in effect_name:
            if hasattr(user, 'stat_stages') and hasattr(target, 'stat_stages'):
                for stat in user.stat_stages:
                    if stat in target.stat_stages:
                        user.stat_stages[stat] = target.stat_stages[stat]
                self._log(f"{user.name} copied {target.name}'s stat changes!")
            return
        
        # === Steal Stat Boosts (Spectral Thief) ===
        if 'Steal Stat Boosts' in effect_name:
            if hasattr(user, 'stat_stages') and hasattr(target, 'stat_stages'):
                for stat in target.stat_stages:
                    boost = target.stat_stages[stat]
                    if boost > 0:
                        user.stat_stages[stat] = min(6, user.stat_stages.get(stat, 0) + boost)
                        target.stat_stages[stat] = 0
                self._log(f"{user.name} stole {target.name}'s stat boosts!")
            return
        
        # === Power Trick (swap Attack and Defense) ===
        if 'Power Trick' in effect_name:
            if hasattr(user, 'attack') and hasattr(user, 'defense'):
                user.attack, user.defense = user.defense, user.attack
                self._log(f"{user.name} swapped its Attack and Defense!")
            return
        
        # === Power Swap / Guard Swap ===
        if 'Power Swap' in effect_name:
            if hasattr(user, 'stat_stages') and hasattr(target, 'stat_stages'):
                for stat in ['attack', 'sp_attack']:
                    user.stat_stages[stat], target.stat_stages[stat] = \
                        target.stat_stages.get(stat, 0), user.stat_stages.get(stat, 0)
                self._log(f"{user.name} swapped Attack/Sp.Atk changes with {target.name}!")
            return
        
        if 'Guard Swap' in effect_name:
            if hasattr(user, 'stat_stages') and hasattr(target, 'stat_stages'):
                for stat in ['defense', 'sp_defense']:
                    user.stat_stages[stat], target.stat_stages[stat] = \
                        target.stat_stages.get(stat, 0), user.stat_stages.get(stat, 0)
                self._log(f"{user.name} swapped Defense/Sp.Def changes with {target.name}!")
            return
        
        # === Speed Swap ===
        if 'Speed Swap' in effect_name:
            if hasattr(user, 'speed') and hasattr(target, 'speed'):
                user.speed, target.speed = target.speed, user.speed
                self._log(f"{user.name} swapped Speed with {target.name}!")
            return
        
        # === Conversion (change user type) ===
        if 'Conversion' in effect_name:
            # Simplified: just note it happened
            self._log(f"{user.name}'s type changed!")
            return
        
        # === Copycat / Mimic / Mirror Move ===
        if effect_name in ('Copycat', 'Mirror Move'):
            self._log(f"{user.name} copied the last move!")
            return
        
        # === Metronome (random move) ===
        if 'Metronome' in effect_name:
            if self.move_repo:
                # Get all moves that can be called by Metronome
                all_moves = self.move_repo.get_all()
                
                # Filter out moves that Metronome cannot call
                excluded_moves = {
                    'Metronome', 'Struggle', 'Sketch', 'Mimic', 'Counter', 'Mirror Coat',
                    'Protect', 'Detect', 'Endure', 'Destiny Bond', 'Sleep Talk',
                    'Assist', 'Copycat', 'Mirror Move', 'Focus Punch', 'Follow Me',
                    'Helping Hand', 'Chatter', 'Me First', 'Transform'
                }
                
                valid_moves = [m for m in all_moves 
                              if m['name'] not in excluded_moves and m['power']]
                
                if valid_moves:
                    random_move = random.choice(valid_moves)
                    self._log(f"{user.name} used Metronome!")
                    self._log(f"  -> {random_move['name']}!")
                    
                    # Execute the random move
                    random_move_with_effects = self.move_repo.get_with_effects(random_move['id'])
                    if random_move_with_effects and random_move_with_effects.get('effects'):
                        for effect in random_move_with_effects['effects']:
                            # Calculate damage if it's a damaging move
                            metronome_damage = 0
                            metronome_crit = False
                            if random_move['causes_damage']:
                                metronome_damage, metronome_crit = self._calculate_damage(
                                    user, target, random_move_with_effects
                                )
                            
                            self._apply_single_effect(
                                effect, user, target, 
                                random_move_with_effects, 
                                metronome_damage, 
                                metronome_crit
                            )
                else:
                    self._log(f"{user.name} used Metronome, but it failed!")
            else:
                self._log(f"{user.name} used Metronome!")
            return
        
        # === Encore ===
        if 'Encore' in effect_name:
            target.encore = True
            target.encore_turns = 3
            target.encore_move = getattr(target, 'last_move_used', None)
            self._log(f"{target.name} received an encore!")
            return
        
        # === Taunt ===
        if 'Taunt' in effect_name:
            target.taunted = True
            target.taunt_turns = 3
            self._log(f"{target.name} fell for the taunt!")
            return
        
        # === Disable ===
        if 'Disable' in effect_name:
            target.disabled_move = getattr(target, 'last_move_used', None)
            target.disable_turns = 4
            self._log(f"{target.name}'s move was disabled!")
            return
        
        # === Torment ===
        if 'Torment' in effect_name:
            target.tormented = True
            self._log(f"{target.name} was subjected to torment!")
            return
        
        # === Spite / Grudge ===
        if 'Spite' in effect_name:
            self._log(f"{target.name}'s move lost PP!")
            return
        
        # === Nullify Ability ===
        if 'Nullify Ability' in effect_name:
            if hasattr(target, 'ability'):
                old_ability = target.ability
                target.ability = None
                self._log(f"{target.name}'s ability was nullified!")
            return
        
        # === Curse (Ghost-type) ===
        if 'Curse' in effect_name:
            target.cursed = True
            cost = user.max_hp // 2
            user.take_damage(cost)
            self._log(f"{user.name} cut its own HP and laid a curse on {target.name}!")
            return
        
        # === Remove Item / Swap Items ===
        if 'Remove Item' in effect_name:
            if hasattr(target, 'held_item') and target.held_item:
                self._log(f"{target.name}'s {target.held_item} was removed!")
                target.held_item = None
            return
        
        if 'Swap Items' in effect_name:
            if hasattr(user, 'held_item') and hasattr(target, 'held_item'):
                user.held_item, target.held_item = target.held_item, user.held_item
                self._log(f"{user.name} swapped items with {target.name}!")
            return
        
        # === Change Type ===
        if 'Change Type' in effect_name:
            self._log(f"{target.name}'s type changed!")
            return
        
        # === Self HP Cost ===
        if 'Self HP Cost' in effect_name:
            cost = (user.max_hp * 50) // 100
            user.take_damage(cost)
            self._log(f"{user.name} paid {cost} HP!")
            return
        
        # === Fly / Dig / Dive / Shadow Force (semi-invulnerable turn) ===
        if effect_name in ('Fly', 'Dig', 'Dive', 'Shadow Force'):
            # Simplified: these are two-turn moves; the first turn makes user semi-invulnerable
            self._log(f"{user.name} disappeared!")
            return
        
        # === Smack Down (grounds target) ===
        if 'Smack Down' in effect_name:
            if hasattr(target, 'grounded'):
                target.grounded = True
            self._log(f"{target.name} fell to the ground!")
            return
        
        # === Ingrain ===
        if 'Ingrain' in effect_name:
            user.ingrain = True
            self._log(f"{user.name} planted its roots!")
            return
        
        # === Aqua Ring ===
        if 'Aqua Ring' in effect_name:
            user.aqua_ring = True
            self._log(f"{user.name} surrounded itself with a veil of water!")
            return
        
        # === Embargo ===
        if 'Embargo' in effect_name:
            target.embargo = True
            target.embargo_turns = 5
            self._log(f"{target.name} can't use items anymore!")
            return
        
        # === Heal Block ===
        if 'Heal Block' in effect_name:
            target.heal_block = True
            target.heal_block_turns = 5
            self._log(f"{target.name} was prevented from healing!")
            return
        
        # === Nightmare ===
        if 'Nightmare' in effect_name:
            target.nightmare = True
            self._log(f"{target.name} began having a nightmare!")
            return
        
        # === Substitute ===
        if 'Substitute' in effect_name:
            if hasattr(user, 'create_substitute'):
                success = user.create_substitute()
                if success:
                    self._log(f"{user.name} created a substitute!")
                else:
                    self._log(f"But it failed! (not enough HP)")
            return
        
        # === Transform ===
        if 'Transform' in effect_name:
            if hasattr(user, 'transform'):
                success = user.transform(target)
                if success:
                    self._log(f"{user.name} transformed into {target.name}!")
                else:
                    self._log(f"But it failed!")
            return
        
        # === Telekinesis ===
        if 'Telekinesis' in effect_name:
            target.telekinesis = True
            self._log(f"{target.name} was hurled into the air!")
            return
        
        # === Teleport ===
        if 'Teleport' in effect_name:
            self.forced_switches.append(user)
            self._log(f"{user.name} teleported away!")
            return
        
        # === Pay Day ===
        if 'Pay Day' in effect_name:
            self._log(f"Coins scattered everywhere!")
            return
        
        # === Prevent Sound Moves ===
        if 'Prevent Sound Moves' in effect_name:
            target.throat_chop = True
            target.throat_chop_turns = 2
            self._log(f"{target.name} can't use sound-based moves!")
            return
        
        # === Damage Contact ===
        if 'Damage Contact' in effect_name:
            # Spiky Shield: handled similarly to Protect, damages attackers
            user.protected = True
            self._log(f"{user.name} protected itself with spikes!")
            return
        
        # === Use Target Attack (Foul Play) ===
        if 'Use Target Attack' in effect_name:
            # Handled in _calculate_damage
            return
        
        # === Type Dependent ===
        if 'Type Dependent' in effect_name:
            return
        
        # === Ignore Redirection ===
        if 'Ignore Redirection' in effect_name:
            return
        
        # === Default fallback ===
        self._log(f"{effect_name} activated!")

    def _apply_sandstorm_damage(self):
        """Apply sandstorm damage to non-immune Pokemon"""
        for pokemon in self._get_all_active_pokemon():
            # Immune types: Rock, Ground, Steel
            if pokemon.type1 not in ['Rock', 'Ground', 'Steel'] and \
               pokemon.type2 not in ['Rock', 'Ground', 'Steel']:
                # --- Ability: Weather immunity (Overcoat, Sand Veil, Magic Guard, etc.) ---
                if AbilityHandler and AbilityHandler.check_weather_immunity(pokemon, 'Sandstorm'):
                    self._log(f"(Ability: {pokemon.name}'s {pokemon.ability} grants Sandstorm immunity)")
                    continue
                if AbilityHandler and AbilityHandler.check_indirect_damage_immunity(pokemon):
                    self._log(f"(Ability: {pokemon.name}'s {pokemon.ability} blocks indirect damage)")
                    continue
                damage = pokemon.max_hp // 16
                pokemon.take_damage(damage)
                self._log(f"{pokemon.name} is buffeted by the sandstorm! (-{damage} HP)")

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
        
        # Check if Substitute blocks the effect
        # Substitute blocks offensive effects on the target
        if effect_target_str == 'Target' and hasattr(effect_target, 'substitute') and effect_target.substitute:
            blocked_types = ['STATUS', 'STAT_CHANGE', 'OTHER']
            # Note: sound-based moves or Infiltrator would bypass this in full mechanics
            
            if effect_type in blocked_types:
                # Exceptions within OTHER?
                # Transform is OTHER, but works on Substitute in some gens? No, usually fails.
                # Only "Special" effects that target the user should pass, but we're in effect_target_str == 'Target' block.
                
                self._log(f"But it failed! (Substitute protected {effect_target.name})")
                return
        
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
            # Set user side context for field effects
            if user == self.battle_state.get('player1_active'):
                self._current_user_side = 'player1_side_effects'
            else:
                self._current_user_side = 'player2_side_effects'
            self._apply_field_effect(effect)
        elif effect_type == 'RECOIL':
            recoil_pct = effect.get('recoil_percentage', 25)
            recoil_damage = max(1, (damage_dealt * recoil_pct) // 100)
            user.take_damage(recoil_damage)
            self._log(f"{user.name} took {recoil_damage} recoil damage!")
        elif effect_type == 'DAMAGE_MODIFIER':
            # Damage modifiers are handled in _calculate_damage, nothing to do here
            pass
        elif effect_type == 'OTHER':
            self._apply_other_effect(user, target, effect)

    def _apply_stat_change_effect(self, pokemon, effect):
        """Apply stat change from database effect with ability integration"""
        stat_to_change = effect.get('stat_to_change', '')
        stat_change_amount = effect.get('stat_change_amount', 0)
        
        # --- Ability: Contrary / Simple (invert or double stat changes) ---
        if AbilityHandler:
            original_amount = stat_change_amount
            stat_change_amount = AbilityHandler.modify_stat_change(pokemon, stat_to_change, stat_change_amount)
            if stat_change_amount != original_amount:
                self._log(f"(Ability: {pokemon.name}'s {pokemon.ability} modified stat change {original_amount} â†’ {stat_change_amount})")
        
        if stat_to_change == 'All':
            # Raise/lower all stats
            for stat in ['attack', 'defense', 'sp_attack', 'sp_defense', 'speed']:
                # --- Ability: Check stat drop immunity (Clear Body, etc.) ---
                if stat_change_amount < 0 and AbilityHandler:
                    is_blocked, counter = AbilityHandler.check_stat_drop_immunity(pokemon, stat, stat_change_amount)
                    if is_blocked:
                        self._log(f"(Ability: {pokemon.name}'s {pokemon.ability} blocks {stat} drop)")
                        continue
                    if counter:
                        self._log(f"(Ability: {pokemon.name}'s {pokemon.ability} triggers {counter[0]} +{counter[1]} counter-boost)")
                        pokemon.modify_stat_stage(counter[0], counter[1])
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
            
            # --- Ability: Check stat drop immunity (Clear Body, Defiant, Competitive) ---
            if stat_change_amount < 0 and AbilityHandler:
                is_blocked, counter = AbilityHandler.check_stat_drop_immunity(
                    pokemon, stat_key, stat_change_amount)
                if is_blocked:
                    ability = getattr(pokemon, 'ability', '')
                    self._log(f"(Ability: {pokemon.name}'s {ability} blocks {stat_key} drop)")
                    self._log(f"{pokemon.name}'s {ability} prevents stat reduction!")
                    return
                if counter:
                    # Defiant / Competitive counter-boost
                    self._log(f"(Ability: {pokemon.name}'s {getattr(pokemon, 'ability', '')} triggers {counter[0]} +{counter[1]} counter-boost)")
                    pokemon.modify_stat_stage(counter[0], counter[1])
                    counter_display = counter[0].replace('_', ' ').title()
                    self._log(f"{pokemon.name}'s {getattr(pokemon, 'ability', '')} raised its {counter_display}!")
            
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
        """Apply status condition from database effect with ability immunity check"""
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
        
        # --- Ability: Status immunity (Immunity, Limber, Insomnia, etc.) ---
        if AbilityHandler and AbilityHandler.check_status_immunity(pokemon, status_name, self.battle_state):
            ability = getattr(pokemon, 'ability', '')
            self._log(f"(Ability: {pokemon.name}'s {ability} grants immunity to {status_name})")
            self._log(f"{pokemon.name}'s {ability} prevents {status_condition}!")
            return
        
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

    def _apply_weather_effect(self, effect):
        """Apply weather change from database effect"""
        weather_type = effect.get('weather_type', 'None')
        
        if weather_type and weather_type != 'None':
            self.battle_state['weather'] = {
                'type': weather_type,
                'turns_remaining': 5
            }
            self._log(f"{weather_type} began!")

    # endregion Effects
    # region Calculations

    def _calculate_confusion_damage(self, pokemon) -> int:
        """Calculate self-inflicted confusion damage"""
        # Confusion damage is typeless 40 power physical move
        attack = pokemon.get_effective_stat('attack')
        defense = pokemon.get_effective_stat('defense')
        level = getattr(pokemon, 'level', 50)
        
        damage = ((2 * level / 5 + 2) * 40 * attack / defense) / 50 + 2
        return int(damage)

    def _calculate_damage(self, attacker, defender, move) -> Tuple[int, bool]:
        """
        Calculate damage for a move with full ability integration.
        
        Returns: (damage, critical_hit)
        """
        # Get move effects for special damage handling
        effects = self._get_move_effects(move)
        
        # --- Ability: Type immunity check (Levitate, Flash Fire, Water/Volt Absorb, etc.) ---
        if AbilityHandler:
            # Check Mold Breaker before type immunity
            ignore_defensive = AbilityHandler.check_mold_breaker(attacker)
            if ignore_defensive:
                self._log(f"(Ability: {attacker.name}'s {attacker.ability} ignores defensive abilities)")
            if not ignore_defensive:
                is_immune, heal_frac, stat_boost = AbilityHandler.check_type_immunity(
                    defender, move, self.battle_state, self._log)
                if is_immune:
                    self._log(f"(Ability: {defender.name}'s {defender.ability} grants immunity to {move.get('type')} moves)")
                    if heal_frac > 0:
                        heal_amt = max(1, int(defender.max_hp * heal_frac))
                        actual = min(heal_amt, defender.max_hp - defender.current_hp)
                        defender.current_hp = min(defender.max_hp, defender.current_hp + actual)
                        if actual > 0:
                            self._log(f"{defender.name} restored {actual} HP!")
                    if stat_boost:
                        stat_name, stages = stat_boost
                        defender.modify_stat_stage(stat_name, stages)
                    return 0, False
        
        # --- Ability: Disguise check (blocks first hit) ---
        if AbilityHandler:
            if AbilityHandler.check_disguise(defender, move, self._log):
                self._log(f"(Ability: {defender.name}'s Disguise absorbed the hit)")
                return 0, False
        
        # Check for DAMAGE_MODIFIER effects that override normal calculation
        for effect in effects:
            if effect.get('effect_type') != 'DAMAGE_MODIFIER':
                continue
            effect_name = effect.get('effect_name', '')
            
            # Fixed Damage effects - bypass normal calculation entirely
            if effect_name == 'Fixed Damage 20':
                return 20, False
            elif effect_name == 'Fixed Damage 40':
                return 40, False
            elif effect_name == 'Fixed Damage Level':
                level = getattr(attacker, 'level', 50)
                return level, False
            elif effect_name == 'Fixed Damage Random':
                level = getattr(attacker, 'level', 50)
                return int(level * random.randint(50, 150) / 100), False
            elif effect_name == 'Fixed Damage 50% HP':
                return max(1, defender.current_hp // 2), False
            elif effect_name == 'Endeavor':
                if attacker.current_hp < defender.current_hp:
                    return defender.current_hp - attacker.current_hp, False
                return 0, False
            elif effect_name == 'Final Gambit':
                damage = attacker.current_hp
                attacker.take_damage(attacker.current_hp)
                self._log(f"{attacker.name} fainted!")
                return damage, False
        
        # Get move power
        power = move.get('power', 0)
        
        # Handle None or 0 power (status moves, some special moves)
        if power is None or power == 0:
            return 0, False
        
        # --- Ability: Type change (Pixilate, Refrigerate, Aerilate, etc.) ---
        move_type = move.get('type')
        type_change_mult = 1.0
        if AbilityHandler:
            new_type, tc_mult = AbilityHandler.check_type_change(attacker, move)
            if new_type:
                self._log(f"(Ability: {attacker.name}'s {attacker.ability} changes {move.get('name')} to {new_type} type, {tc_mult}x boost)")
                move_type = new_type
                type_change_mult = tc_mult
        
        # Apply DAMAGE_MODIFIER power modifiers
        for effect in effects:
            if effect.get('effect_type') != 'DAMAGE_MODIFIER':
                continue
            effect_name = effect.get('effect_name', '')
            
            if effect_name == 'HP Scaling High':
                # Power scales with user HP ratio (e.g., Eruption, Water Spout)
                hp_ratio = attacker.current_hp / attacker.max_hp
                power = max(1, int(power * hp_ratio))
            elif effect_name == 'Weight Damage':
                # Power based on target weight (Low Kick, Grass Knot)
                weight = getattr(defender, 'weight', 50)
                if weight >= 200:
                    power = 120
                elif weight >= 100:
                    power = 100
                elif weight >= 50:
                    power = 80
                elif weight >= 25:
                    power = 60
                elif weight >= 10:
                    power = 40
                else:
                    power = 20
            elif effect_name == 'Speed Dependent':
                # Gyro Ball: Power based on speed ratio
                user_speed = max(1, attacker.get_effective_stat('speed'))
                target_speed = max(1, defender.get_effective_stat('speed'))
                power = min(150, max(1, int(25 * target_speed / user_speed)))
            elif effect_name == 'Stat Boost Scaling':
                # Stored Power / Power Trip: +20 per stat boost
                total_boosts = sum(max(0, stage) for stage in attacker.stat_stages.values())
                power = 20 + (20 * total_boosts)
            elif effect_name == 'Stat Dependent Damage':
                # Psyshock etc: Uses SpAtk vs Def instead of SpDef
                pass  # Handled below in stat selection
            elif effect_name == 'Terrain Dependent':
                # Weather Ball: Power and type change with weather
                weather = self.battle_state.get('weather', {}).get('type')
                if weather and weather != 'None':
                    power = power * 2
        
        # Determine if physical or special
        category = move.get('category', 'Physical')
        
        # Check for Stat Dependent Damage (Psyshock: Special move, but hits Defense)
        use_physical_defense = False
        for effect in effects:
            if effect.get('effect_name') == 'Stat Dependent Damage':
                use_physical_defense = True
                break
        
        # Check for Use Target Attack (Foul Play)
        use_target_attack = False
        for effect in effects:
            if effect.get('effect_name') == 'Use Target Attack':
                use_target_attack = True
                break
        
        # --- Ability: Unaware (ignore stat changes) ---
        ignore_atk_boosts = False
        ignore_def_boosts = False
        if AbilityHandler:
            ignore_atk_boosts, ignore_def_boosts = AbilityHandler.check_unaware(attacker, defender, move)
            if ignore_atk_boosts or ignore_def_boosts:
                self._log(f"(Ability: Unaware active â€” ignore atk boosts: {ignore_atk_boosts}, def boosts: {ignore_def_boosts})")
        
        if category == 'Physical':
            if use_target_attack:
                attack_stat = defender.get_effective_stat('attack') if not ignore_atk_boosts else defender.attack
            else:
                attack_stat = attacker.get_effective_stat('attack') if not ignore_atk_boosts else attacker.attack
            defense_stat = defender.get_effective_stat('defense') if not ignore_def_boosts else defender.defense
            
            # Burn halves physical attack (unless user has Guts or it's Facade)
            if attacker.status == 'burn' and not use_target_attack:
                # --- Ability: Guts negates burn reduction ---
                burn_negated = AbilityHandler.check_burn_attack_reduction(attacker) if AbilityHandler else False
                if burn_negated:
                    self._log(f"(Ability: {attacker.name}'s Guts negates burn Attack reduction)")
                if not burn_negated:
                    attack_stat = attack_stat // 2
        else:  # Special
            if use_target_attack:
                attack_stat = defender.get_effective_stat('sp_attack') if not ignore_atk_boosts else defender.sp_attack
            else:
                attack_stat = attacker.get_effective_stat('sp_attack') if not ignore_atk_boosts else attacker.sp_attack
            if use_physical_defense:
                defense_stat = defender.get_effective_stat('defense') if not ignore_def_boosts else defender.defense
            else:
                defense_stat = defender.get_effective_stat('sp_defense') if not ignore_def_boosts else defender.sp_defense
        
        # Critical hit check
        crit_stage = 0
        
        # Check for crit-boosting effects
        for effect in effects:
            effect_name = effect.get('effect_name', '')
            if effect_name == 'Always Crit':
                crit_stage = 3  # Guaranteed crit
            elif effect_name == 'High Crit 1':
                crit_stage = max(crit_stage, 1)
            elif effect_name == 'Focus Energy':
                crit_stage = max(crit_stage, 2)
        
        # Check if user has Focus Energy active
        if hasattr(attacker, 'focus_energy') and attacker.focus_energy:
            crit_stage = min(3, crit_stage + 2)
        
        # --- Ability: Crit stage modification (Super Luck, Merciless, Battle Armor) ---
        crit_blocked = False
        if AbilityHandler:
            original_stage = crit_stage
            crit_stage, crit_blocked = AbilityHandler.modify_crit_stage(attacker, defender, crit_stage)
            if crit_stage != original_stage or crit_blocked:
                self._log(f"(Ability: Crit stage {original_stage} â†’ {crit_stage}, blocked={crit_blocked})")
        
        if crit_blocked:
            critical_hit = False
        else:
            crit_chance = [1/24, 1/8, 1/2, 1/1][min(crit_stage, 3)]
            critical_hit = random.random() < crit_chance
        
        if critical_hit:
            # Ignore negative attack stages and positive defense stages
            attack_stat = attacker.attack if category == 'Physical' else attacker.sp_attack
            defense_stat = defender.defense if category == 'Physical' else defender.sp_defense
        
        # Level (assume level 50 for now, or get from Pokemon)
        level = getattr(attacker, 'level', 50)
        
        # --- Ability: Attacker damage modifiers (Huge Power, Technician, etc.) ---
        move_name = move.get('name', '')
        is_contact = category == 'Physical' and move_name not in CONTACT_OVERRIDE_NO
        if AbilityHandler:
            power, atk_multiplier, extra_mult = AbilityHandler.modify_outgoing_damage(
                attacker, defender, move, power, 0,
                self._get_type_effectiveness(move_type, defender),
                self.battle_state, is_contact)
            if atk_multiplier != 1.0 or extra_mult != 1.0:
                self._log(f"(Ability: {attacker.name}'s {attacker.ability} â€” atk mult={atk_multiplier}, extra mult={extra_mult}, power={power})")
        else:
            atk_multiplier = 1.0
            extra_mult = 1.0
        
        # Apply type change multiplier (Pixilate etc.)
        power = int(power * type_change_mult)
        
        # --- Ability: Flash Fire boost ---
        flash_fire_mult = 1.0
        if AbilityHandler and move_type == 'Fire':
            flash_fire_mult = AbilityHandler.get_flash_fire_boost(attacker)
            if flash_fire_mult != 1.0:
                self._log(f"(Ability: {attacker.name}'s Flash Fire boosts Fire moves by {flash_fire_mult}x)")
        
        # Base damage formula
        damage = ((2 * level / 5 + 2) * power * (attack_stat * atk_multiplier) / defense_stat) / 50 + 2
        
        # Critical hit multiplier
        if critical_hit:
            crit_mult = 1.5
            if AbilityHandler:
                crit_mult = AbilityHandler.modify_crit_damage(attacker, crit_mult)
                if crit_mult != 1.5:
                    self._log(f"(Ability: {attacker.name}'s {attacker.ability} modifies crit multiplier to {crit_mult})")
            damage = damage * crit_mult
        
        # STAB (Same Type Attack Bonus)
        if move_type == attacker.type1 or move_type == attacker.type2:
            stab = 1.5
            # --- Ability: Adaptability (2.0 STAB) ---
            if AbilityHandler:
                stab = AbilityHandler.modify_stab(attacker, stab)
                if stab != 1.5:
                    self._log(f"(Ability: {attacker.name}'s Adaptability boosts STAB to {stab})")
            damage = damage * stab
        
        # Type effectiveness
        effectiveness = self._get_type_effectiveness(move_type, defender)
        damage = damage * effectiveness
        
        # --- Ability: Defender damage reduction (Thick Fat, Filter, Multiscale, etc.) ---
        if AbilityHandler:
            def_multiplier = AbilityHandler.modify_incoming_damage(
                attacker, defender, move, damage, effectiveness,
                self.battle_state, is_contact)
            if def_multiplier != 1.0:
                self._log(f"(Ability: {defender.name}'s {defender.ability} reduces incoming damage to {def_multiplier}x)")
            damage = damage * def_multiplier
        
        # Apply Flash Fire boost
        damage = damage * flash_fire_mult
        
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
        
        # Screen effects (Reflect / Light Screen)
        if not critical_hit:
            # Determine defender's side
            if defender == self.battle_state.get('player1_active'):
                side_key = 'player1_side_effects'
            else:
                side_key = 'player2_side_effects'
            side_effects = self.battle_state.get(side_key, {})
            
            if category == 'Physical' and side_effects.get('reflect_turns', 0) > 0:
                damage = damage * 0.5
            elif category == 'Special' and side_effects.get('light_screen_turns', 0) > 0:
                damage = damage * 0.5
            
            # Aurora Veil reduces all damage
            field_effects = self.battle_state.get('field_effects', {})
            if field_effects.get('auroraveil', {}).get('active', False):
                damage = damage * 0.5
        
        # Damage Doubling conditions
        for effect in effects:
            if effect.get('effect_name') == 'Damage Doubling':
                move_name = move.get('name', '')
                should_double = False
                
                # Facade: double if user has status condition
                if move_name == 'Facade' and attacker.status and attacker.status != 'healthy':
                    should_double = True
                # Hex: double if target has status condition
                elif move_name == 'Hex' and defender.status and defender.status != 'healthy':
                    should_double = True
                # Smelling Salts: double if target is paralyzed
                elif move_name == 'Smelling Salts' and defender.status == 'paralysis':
                    should_double = True
                # Wake-Up Slap: double if target is asleep
                elif move_name == 'Wake-Up Slap' and defender.status == 'sleep':
                    should_double = True
                # Assurance: double if target was already hit this turn
                elif move_name == 'Assurance' and hasattr(defender, 'hit_this_turn') and defender.hit_this_turn:
                    should_double = True
                # Avalanche/Revenge/Payback: double if user was already hit
                elif move_name in ['Avalanche', 'Revenge', 'Payback', 'Retaliate']:
                    if hasattr(attacker, 'hit_this_turn') and attacker.hit_this_turn:
                        should_double = True
                # Stomping Tantrum: double if last move failed
                elif move_name == 'Stomping Tantrum':
                    if hasattr(attacker, 'last_move_failed') and attacker.last_move_failed:
                        should_double = True
                # Rollout/Ice Ball: doubles each consecutive use (simplified)
                elif move_name in ['Rollout', 'Ice Ball', 'Fury Cutter', 'Echoed Voice']:
                    consecutive = getattr(attacker, 'consecutive_uses', 0)
                    damage = damage * (2 ** min(consecutive, 4))
                    should_double = False  # Already handled
                # Fusion Flare/Bolt: double if preceded by the other
                elif move_name in ['Fusion Flare', 'Fusion Bolt']:
                    should_double = False  # Complex mechanic, skip for simplicity
                # Round: double if another Pokemon also used Round
                elif move_name == 'Round':
                    should_double = False  # Doubles mechanic, skip
                
                if should_double:
                    damage = damage * 2
        
        # Random factor (85% to 100%)
        damage = damage * random.randint(85, 100) / 100
        
        damage = max(1, int(damage))
        
        # --- Ability: Sturdy (survive OHKO at full HP) ---
        if AbilityHandler:
            original_damage = damage
            damage = AbilityHandler.check_sturdy(defender, damage, self._log)
            if damage != original_damage:
                self._log(f"(Ability: {defender.name}'s Sturdy reduced lethal damage {original_damage} â†’ {damage})")
        
        return damage, critical_hit

    def _calculate_effective_speed(self, pokemon) -> int:
        """Calculate effective speed with all modifiers and ability integration"""
        # Use the Pokemon's get_effective_stat method which includes stage changes and status
        base_speed = pokemon.get_effective_stat('speed')
        
        # --- Ability: Speed modifiers (Swift Swim, Chlorophyll, Sand Rush, etc.) ---
        if AbilityHandler:
            original_speed = base_speed
            base_speed = AbilityHandler.modify_speed(pokemon, base_speed, self.battle_state)
            if base_speed != original_speed:
                self._log(f"(Ability: {pokemon.name}'s {pokemon.ability} modified speed {original_speed} â†’ {base_speed})")
        
        # Tailwind doubles speed (paralysis already handled in get_effective_stat)
        # Check which side the pokemon is on
        side_effects = self._get_side_effects(pokemon)
        if side_effects.get('tailwind', False):
            base_speed *= 2
        
        # Choice Scarf multiplies by 1.5
        if hasattr(pokemon, 'held_item') and pokemon.held_item == 'Choice Scarf':
            base_speed = int(base_speed * 1.5)
        
        return base_speed

    # endregion Calculations

    def _can_switch(self, pokemon) -> bool:
        """Check if Pokemon can switch out"""
        # Check for trapping moves/abilities
        if hasattr(pokemon, 'trapped') and pokemon.trapped:
            return False
        
        # Ingrain prevents switching
        if hasattr(pokemon, 'ingrain') and pokemon.ingrain:
            return False
        
        return True

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
            # --- Ability: Inner Focus prevents flinch, Steadfast boosts Speed ---
            flinch_prevented = False
            if AbilityHandler:
                ability = getattr(pokemon, 'ability', None)
                if ability:
                    self._log(f"(Ability: Flinch check â€” {pokemon.name}'s {ability})")
                flinch_prevented = AbilityHandler.on_flinch(pokemon, self._log)
            if not flinch_prevented:
                self._log(f"{pokemon.name} flinched!")
                pokemon.flinched = False
                return False
            pokemon.flinched = False
        
        # Disabled/Taunted checks
        if not pokemon.can_use_move(move):
            self._log(f"{pokemon.name} can't use {move.get('name')}!")
            return False
        
        return True

        # In a real implementation, would prompt for replacements
        # For now, just log the faints
    
    
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
        
        # Increment turns_active for all active Pokemon (except those that just switched in)
        for pokemon in self._get_all_active_pokemon():
            if hasattr(pokemon, 'turns_active') and pokemon not in self.just_switched_in:
                pokemon.turns_active += 1

    def _determine_num_hits(self, move, user=None) -> int:
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
            num_hits = 2
        elif move_name in three_hits:
            num_hits = 3
        elif move_name in five_hits:
            num_hits = 5
        elif move_name in two_to_five_hits:
            # 2-5 hits with specific probability distribution
            # 35% for 2 hits, 35% for 3 hits, 15% for 4 hits, 15% for 5 hits
            roll = random.random()
            if roll < 0.35:
                num_hits = 2
            elif roll < 0.70:
                num_hits = 3
            elif roll < 0.85:
                num_hits = 4
            else:
                num_hits = 5
        else:
            # Default: single hit
            num_hits = 1
        
        # --- Ability: Skill Link (always 5 hits), Parental Bond (always 2 hits) ---
        if AbilityHandler and user and num_hits > 1:
            original_hits = num_hits
            num_hits = AbilityHandler.modify_multi_hit(user, num_hits)
            if num_hits != original_hits:
                self._log(f"(Ability: {user.name}'s {user.ability} modified hits {original_hits} \u2192 {num_hits})")
        elif AbilityHandler and user and num_hits == 1:
            # Parental Bond turns single hits into double hits
            ability = getattr(user, 'ability', None)
            if ability == 'Parental Bond':
                self._log(f"(Ability: {user.name}'s Parental Bond \u2014 double hit)")
                num_hits = 2
        
        return num_hits

    def _execute_move(self, user, move, target):
        """Execute a move with full battle mechanics and ability integration"""
        move_name = move.get('name', 'Unknown Move')
        
        # Check for first-turn-only moves (Fake Out, First Impression)
        if move_name in ['Fake Out', 'First Impression']:
            turns_active = getattr(user, 'turns_active', 0)
            if turns_active > 0:
                self._log(f"{user.name} used {move_name}!")
                self._log(f"But it failed!")
                return
        
        # Pre-move checks
        if not self._can_use_move(user, move):
            return
        
        # --- Ability: Before-move triggers (Protean type change) ---
        if AbilityHandler:
            ability = getattr(user, 'ability', None)
            if ability:
                self._log(f"(Ability: Checking before-move trigger for {user.name}'s {ability})")
            AbilityHandler.on_before_move(user, move, self.battle_state, self._log)
        
        self._log(f"{user.name} used {move_name}!")
        
        # Decrement PP
        if hasattr(user, 'current_moves'):
            # Find and decrement PP for this move
            pass
        
        # Handle status moves first (Protect, Detect, stat changes, etc.)
        if not move.get('causes_damage', False):
            # --- Ability: Magic Bounce reflects status moves ---
            if AbilityHandler and AbilityHandler.check_magic_bounce(target, move, self._log):
                self._log(f"(Ability: {target.name}'s Magic Bounce reflected {move.get('name')}!)")
                # Reflect the move back: swap user and target
                self._handle_status_move(target, user, move)
                return
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
        category = move.get('category', 'Physical')
        is_contact = category == 'Physical' and move_name not in CONTACT_OVERRIDE_NO
        
        if move.get('causes_damage', False):
            # Check if this is a multi-hit move
            num_hits = self._determine_num_hits(move, user)
            
            if num_hits > 1:
                # Multi-hit move - show each hit
                total_damage = 0
                any_crit = False
                for hit_num in range(num_hits):
                    hit_damage, hit_crit = self._calculate_damage(user, target, move)
                    
                    if hit_damage == 0:
                        # Immunity kicked in (handled by type immunity in calc)
                        break
                    
                    if hit_crit:
                        any_crit = True
                        self._log(f"Hit {hit_num + 1}! A critical hit!")
                    else:
                        self._log(f"Hit {hit_num + 1}!")
                    
                    # Check for substitute on each hit
                    if hasattr(target, 'substitute') and target.substitute and not move.get('bypasses_substitute', False):
                        result = target.damage_substitute(hit_damage)
                        if result['broke']:
                            self._log(f"The substitute broke!")
                    else:
                        target.take_damage(hit_damage)
                    
                    total_damage += hit_damage
                    
                    # Break if target fainted
                    if target.current_hp <= 0:
                        break
                
                if total_damage > 0:
                    self._log(f"Hit {min(hit_num + 1, num_hits)} time(s) for {total_damage} total damage!")
                damage = total_damage
                critical_hit = any_crit
                
                # Type effectiveness message after all hits
                effectiveness = self._get_type_effectiveness(move.get('type'), target)
                if effectiveness > 1.0:
                    self._log("It's super effective!")
                elif effectiveness < 1.0 and effectiveness > 0:
                    self._log("It's not very effective...")
            else:
                # Single-hit move
                damage, critical_hit = self._calculate_damage(user, target, move)
                
                if damage == 0:
                    # Type immunity (already logged by AbilityHandler)
                    return
                
                if critical_hit:
                    self._log("A critical hit!")
                
                # Type effectiveness messages
                effectiveness = self._get_type_effectiveness(move.get('type'), target)
                if effectiveness > 1.0:
                    self._log("It's super effective!")
                elif effectiveness < 1.0 and effectiveness > 0:
                    self._log("It's not very effective...")
                elif effectiveness == 0:
                    self._log(f"It doesn't affect {target.name}...")
                    return
                
                # Check for Substitute
                if hasattr(target, 'substitute') and target.substitute and not move.get('bypasses_substitute', False):
                    self._log(f"The substitute took damage for {target.name}!")
                    result = target.damage_substitute(damage)
                    if result['broke']:
                        self._log(f"The substitute broke!")
                else:
                    # Apply damage
                    target.take_damage(damage)
                    self._log(f"{target.name} took {damage} damage!")
        
        # --- Ability: Anger Point on critical hit received ---
        if critical_hit and AbilityHandler and target.current_hp > 0:
            if getattr(target, 'ability', None) == 'Anger Point':
                self._log(f"(Ability: {target.name}'s Anger Point activating from critical hit)")
            AbilityHandler.on_crit_received(target, self._log)
        
        # --- Ability: Contact abilities (Static, Flame Body, Rough Skin, etc.) ---
        if damage > 0 and is_contact and AbilityHandler and target.current_hp > 0:
            def_ability = getattr(target, 'ability', None)
            if def_ability:
                self._log(f"(Ability: Contact made â€” checking {target.name}'s {def_ability})")
            AbilityHandler.on_contact(user, target, move, self._log, self.battle_state)
        
        # --- Ability: After-attacking abilities (Stench, Poison Touch, etc.) ---
        if damage > 0 and AbilityHandler and target.current_hp > 0:
            atk_ability = getattr(user, 'ability', None)
            if atk_ability:
                self._log(f"(Ability: After-attack â€” checking {user.name}'s {atk_ability})")
            AbilityHandler.on_after_attacking(user, target, move, damage, self._log, self.battle_state)
        
        # Set user side context for field effect application
        if user == self.battle_state.get('player1_active') or user in self.battle_state.get('player1_team', []):
            self._current_user_side = 'player1_side_effects'
        else:
            self._current_user_side = 'player2_side_effects'
        
        # Apply move effects (including drain)
        self._apply_move_effects(user, target, move, damage, critical_hit)
        
        # --- Ability: Moxie etc. on KO ---
        if target.current_hp <= 0 and AbilityHandler:
            atk_ability = getattr(user, 'ability', None)
            if atk_ability:
                self._log(f"(Ability: KO detected â€” checking {user.name}'s {atk_ability})")
            AbilityHandler.on_ko(user, self._log)
        
        # Check for forced switch moves (U-turn, Volt Switch, Flip Turn, etc.)
        if damage > 0 and self._is_forced_switch_move(move):
            # Only switch if the target didn't faint and user is still alive
            if target.current_hp > 0 and user.current_hp > 0:
                self.forced_switches.append(user)
                self._log(f"{user.name} went back to its trainer!")
        
        # Recoil damage
        if move.get('recoil_percentage', 0) > 0:
            # --- Ability: Rock Head negates recoil ---
            if AbilityHandler and AbilityHandler.check_recoil_immunity(user):
                self._log(f"(Ability: {user.name}'s {user.ability} negates recoil damage)")
            else:
                recoil = (damage * move['recoil_percentage']) // 100
                user.take_damage(recoil)
                self._log(f"{user.name} took {recoil} recoil damage!")

    def _execute_switch(self, pokemon, switch_target):
        """Execute a Pokemon switch with ability integration"""
        # Handle switch-out effects (trapping moves, etc.)
        if pokemon.trapped and not self._can_switch(pokemon):
            self._log(f"{pokemon.name} can't switch out!")
            return
        
        # --- Ability: Check ability-based trapping (Shadow Tag, Arena Trap, Magnet Pull) ---
        if AbilityHandler:
            opponents = self._get_opponents(pokemon)
            for opp in opponents:
                if opp and opp.current_hp > 0:
                    if AbilityHandler.check_trapping(opp, pokemon, self.battle_state, self._log):
                        self._log(f"(Ability: {opp.name}'s {opp.ability} prevents {pokemon.name} from switching)")
                        self._log(f"{pokemon.name} can't switch out due to {opp.name}'s {opp.ability}!")
                        return
        
        # --- Ability: Switch-out triggers (Natural Cure, Regenerator) ---
        if AbilityHandler:
            ability = getattr(pokemon, 'ability', None)
            if ability:
                self._log(f"(Ability: Checking switch-out trigger for {pokemon.name}'s {ability})")
            AbilityHandler.on_switch_out(pokemon, self._log)
        
        # Reset volatile status on switch
        pokemon.reset_volatile_conditions()
        
        # Determine which trainer owns this Pokemon
        trainer_name = "Player" if pokemon in self.battle_state.get('player1_team', []) else "Opponent"
        
        # Perform the switch
        self._log(f"{trainer_name} withdrew {pokemon.name}!")
        
        # Reset turns_active for the incoming Pokemon
        if hasattr(switch_target, 'turns_active'):
            switch_target.turns_active = 0
        
        # Track that this Pokemon just switched in (don't increment turns_active this turn)
        self.just_switched_in.append(switch_target)
        
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
    # region Getters

    def _get_all_active_pokemon(self) -> List:
        """Get all currently active Pokemon"""
        active = []
        if self.battle_state.get('player1_active'):
            active.append(self.battle_state['player1_active'])
        if self.battle_state.get('player2_active'):
            active.append(self.battle_state['player2_active'])
        return active

    def _get_current_target(self, user):
        """Get the currently active opponent Pokemon (handles mid-turn switches)"""
        # Determine which side the user is on
        if user == self.battle_state.get('player1_active') or user in self.battle_state.get('player1_team', []):
            # User is player1, target is player2's active
            return self.battle_state.get('player2_active')
        else:
            # User is player2, target is player1's active
            return self.battle_state.get('player1_active')

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

    def _get_opponent_side_key(self):
        """Get the side effects key for the opponent"""
        user_side = getattr(self, '_current_user_side', 'player1_side_effects')
        if user_side == 'player1_side_effects':
            return 'player2_side_effects'
        return 'player1_side_effects'

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

    def _get_type_effectiveness(self, attack_type: str, defender) -> float:
        """Calculate type effectiveness multiplier (Gen 6 Standard)"""
        return _calc_type_eff(attack_type, defender.type1, defender.type2)

    # endregion Getters

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

    def _has_usable_pokemon(self, player: str) -> bool:
        """Check if player has any Pokemon that can battle"""
        team = self.battle_state.get(f'{player}_team', [])
        for pokemon in team:
            if pokemon.current_hp > 0:
                return True
        return False

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

    def _log(self, message: str):
        """Add message to turn log"""
        self.turn_log.append(message)
    # region Phases

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

    def _phase_handle_faints(self):
        """Handle Pokemon that fainted during the turn"""
        # Collect all fainted Pokemon
        for pokemon in self._get_all_active_pokemon():
            if pokemon.current_hp <= 0 and pokemon not in self.fainted_pokemon:
                self.fainted_pokemon.append(pokemon)
                self._log(f"{pokemon.name} fainted!")

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

    # endregion Phases
    # region Processing

    def _process_effect_endings(self):
        """Process effects that end at start of turn"""
        for pokemon in self._get_all_active_pokemon():
            # Roost: restore Flying type if used last turn
            if hasattr(pokemon, 'roosted') and pokemon.roosted:
                pokemon.roosted = False

    def _process_end_of_turn_abilities(self):
        """Process abilities that trigger at end of turn"""
        if not AbilityHandler:
            return
        for pokemon in self._get_all_active_pokemon():
            if pokemon.current_hp <= 0:
                continue
            ability = getattr(pokemon, 'ability', None)
            if ability:
                self._log(f"(Ability: Processing end-of-turn for {pokemon.name}'s {ability})")
            opponents = self._get_opponents(pokemon)
            AbilityHandler.end_of_turn(pokemon, self.battle_state, self._log, opponents)

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
        if not AbilityHandler:
            return
        for pokemon in self._get_all_active_pokemon():
            if pokemon.current_hp <= 0:
                continue
            ability = getattr(pokemon, 'ability', None)
            if ability:
                self._log(f"(Ability: Processing start-of-turn for {pokemon.name}'s {ability})")
            AbilityHandler.start_of_turn(pokemon, self.battle_state, self._log)

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
            elif held_item == 'Flame Orb' and not pokemon.status:
                if self.battle_state.get('turn_count', 1) > 1:  # Activates after first turn
                    pokemon.apply_status('burn')
                    self._log(f"{pokemon.name} was burned by its Flame Orb!")
            
            # Toxic Orb activation (if not already poisoned)
            elif held_item == 'Toxic Orb' and not pokemon.status:
                if self.battle_state.get('turn_count', 1) > 1:
                    pokemon.apply_status('badly_poison')
                    self._log(f"{pokemon.name} was badly poisoned by its Toxic Orb!")

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

    # endregion Processing

    def _set_user_side_effect(self, key, value):
        """Set a side effect for the current user's side"""
        # Try to determine which side is using the move
        # Default to player1 side if we can't tell
        for side_key in ['player1_side_effects', 'player2_side_effects']:
            if side_key not in self.battle_state:
                self.battle_state[side_key] = {}
        # Use a context flag if available, otherwise default to player1
        user_side = getattr(self, '_current_user_side', 'player1_side_effects')
        self.battle_state[user_side][key] = value

                # Restore flying type logic would go here
    
    
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

    def _trigger_switch_in_ability(self, pokemon):
        """Trigger ability when Pokemon switches in"""
        if not AbilityHandler:
            return
        ability = getattr(pokemon, 'ability', None)
        if ability:
            self._log(f"(Ability: {pokemon.name}'s {ability} \u2014 switch-in trigger)")
        opponents = self._get_opponents(pokemon)
        AbilityHandler.on_switch_in(pokemon, self.battle_state, self._log, opponents)



