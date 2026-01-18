"""
Pokemon CPU AI System
Implements Generation 4-style trainer AI with scoring system and behavior flags
Based on the trainer AI from Pokemon Platinum
"""
import random
import sys
import os
from typing import List, Dict, Optional, Tuple
from enum import Enum

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(__file__)), 'src'))

try:
    from repositories import PokemonRepository, MoveRepository
except ImportError:
    from src.repositories import PokemonRepository, MoveRepository


class AIFlag(Enum):
    """AI behavior flags that determine how the CPU chooses moves"""
    BASIC = "basic"  # Almost all trainers - avoid wasted moves
    EVALUATE_ATTACK = "evaluate_attack"  # Consider type effectiveness
    EXPERT = "expert"  # Advanced tactics
    SETUP_FIRST_TURN = "setup_first_turn"  # Use setup moves on turn 1
    RISKY = "risky"  # Use high-risk high-reward moves
    PRIORITIZE_DAMAGE = "prioritize_damage"  # Prefer damaging moves
    BATON_PASS = "baton_pass"  # Use Baton Pass strategically
    CHECK_HP = "check_hp"  # Consider HP thresholds
    WEATHER = "weather"  # Weather-based tactics
    HARASSMENT = "harassment"  # Status/disruption focus


class CPUTrainer:
    """
    CPU AI for Pokemon battles
    Scores moves and selects the best action based on assigned behavior flags
    """
    
    def __init__(self, flags: List[AIFlag] = None, difficulty: str = "normal"):
        """
        Initialize CPU trainer AI
        
        Args:
            flags: List of AI behavior flags (defaults to [BASIC, EVALUATE_ATTACK])
            difficulty: Difficulty level ("easy", "normal", "hard", "expert")
        """
        # Set default flags if none provided
        if flags is None:
            if difficulty == "easy":
                self.flags = [AIFlag.BASIC]
            elif difficulty == "normal":
                self.flags = [AIFlag.BASIC, AIFlag.EVALUATE_ATTACK]
            elif difficulty == "hard":
                self.flags = [AIFlag.BASIC, AIFlag.EVALUATE_ATTACK, AIFlag.CHECK_HP]
            else:  # expert
                self.flags = [AIFlag.BASIC, AIFlag.EVALUATE_ATTACK, AIFlag.EXPERT, 
                             AIFlag.CHECK_HP, AIFlag.PRIORITIZE_DAMAGE]
        else:
            self.flags = flags
        
        self.pokemon_repo = PokemonRepository()
        self.move_repo = MoveRepository()
    
    def choose_move(self, user_pokemon, target_pokemon, battle_state: Dict = None) -> Dict:
        """
        Choose the best move for the AI to use
        
        Args:
            user_pokemon: AI's Pokemon
            target_pokemon: Opponent's Pokemon
            battle_state: Current battle state (weather, field effects, etc.)
            
        Returns:
            Dictionary with 'move' and 'score' keys
        """
        if battle_state is None:
            battle_state = self._create_default_battle_state()
        
        # Get all available moves
        available_moves = []
        for move in user_pokemon.moves:
            if isinstance(move, dict):
                # Move is dictionary
                if move.get('pp', 1) > 0:
                    available_moves.append(move)
            else:
                # Move is Move object
                move_dict = {
                    'id': move.id,
                    'name': move.name,
                    'type': move.type,
                    'category': move.category,
                    'power': move.power,
                    'accuracy': move.accuracy,
                    'pp': move.pp_current,
                    'priority': move.priority,
                    'causes_damage': move.causes_damage,
                }
                if move.can_use():
                    available_moves.append(move_dict)
        
        if not available_moves:
            # No moves available (Struggle would be used in real game)
            return {'move': None, 'score': 0, 'reason': 'No PP remaining'}
        
        # Initialize all move scores to 100
        move_scores = {}
        for move in available_moves:
            move_scores[move['id']] = {
                'move': move,
                'score': 100,
                'modifiers': []
            }
        
        # Apply scoring based on active flags
        for flag in self.flags:
            if flag == AIFlag.BASIC:
                self._apply_basic_flag(move_scores, user_pokemon, target_pokemon, battle_state)
            elif flag == AIFlag.EVALUATE_ATTACK:
                self._apply_evaluate_attack_flag(move_scores, user_pokemon, target_pokemon)
            elif flag == AIFlag.EXPERT:
                self._apply_expert_flag(move_scores, user_pokemon, target_pokemon, battle_state)
            elif flag == AIFlag.CHECK_HP:
                self._apply_check_hp_flag(move_scores, user_pokemon, target_pokemon)
            elif flag == AIFlag.PRIORITIZE_DAMAGE:
                self._apply_prioritize_damage_flag(move_scores, user_pokemon, target_pokemon)
        
        # Find move(s) with highest score
        if not move_scores:
            return {'move': available_moves[0], 'score': 100, 'reason': 'Default choice'}
        
        max_score = max(data['score'] for data in move_scores.values())
        best_moves = [data for data in move_scores.values() if data['score'] == max_score]
        
        # Random selection if tied
        chosen = random.choice(best_moves)
        
        return {
            'move': chosen['move'],
            'score': chosen['score'],
            'modifiers': chosen['modifiers'],
            'reason': f"Score: {chosen['score']}, Modifiers: {', '.join(chosen['modifiers']) if chosen['modifiers'] else 'None'}"
        }
    
    # ========== BASIC FLAG ==========
    
    def _apply_basic_flag(self, move_scores: Dict, user: any, target: any, battle_state: Dict):
        """
        Apply Basic Flag scoring
        Philosophy: Discourage moves that would waste a turn or benefit opponent
        """
        user_data = self.pokemon_repo.get_by_id(user.id)
        target_data = self.pokemon_repo.get_by_id(target.id)
        
        for move_id, data in move_scores.items():
            move = data['move']
            
            # Step 1: Check for immunities
            immunity_penalty = self._check_immunities(move, user, target, user_data, target_data)
            if immunity_penalty < 0:
                data['score'] += immunity_penalty
                data['modifiers'].append(f"Immunity penalty: {immunity_penalty}")
            
            # Step 2: Score by effect
            effect_modifier = self._score_by_effect(move, user, target, battle_state)
            if effect_modifier != 0:
                data['score'] += effect_modifier
                if effect_modifier < 0:
                    data['modifiers'].append(f"Effect penalty: {effect_modifier}")
    
    def _check_immunities(self, move: Dict, user: any, target: any, 
                         user_data: Dict, target_data: Dict) -> int:
        """Check for type and ability immunities"""
        penalty = 0
        move_type = move.get('type', '')
        
        # Type immunities
        if self._is_immune_by_type(move_type, target_data):
            penalty = -10
        
        # Ability immunities (simplified - would need full ability system)
        target_ability = target_data.get('ability', '')
        if self._is_immune_by_ability(move, target_ability, move_type):
            penalty = -10
        
        return penalty
    
    def _is_immune_by_type(self, move_type: str, target_data: Dict) -> bool:
        """Check if target is immune to move type"""
        # Type chart immunities
        immunities = {
            'Normal': ['Ghost'],
            'Fighting': ['Ghost'],
            'Ground': ['Flying'],
            'Ghost': ['Normal'],
            'Electric': ['Ground'],
            'Psychic': ['Dark'],
            'Poison': ['Steel'],
        }
        
        target_types = [target_data.get('type1'), target_data.get('type2')]
        immune_types = immunities.get(move_type, [])
        
        for target_type in target_types:
            if target_type in immune_types:
                return True
        
        return False
    
    def _is_immune_by_ability(self, move: Dict, ability: str, move_type: str) -> bool:
        """Check if target's ability makes them immune"""
        # Simplified ability immunities
        ability_immunities = {
            'Volt Absorb': ['Electric'],
            'Motor Drive': ['Electric'],
            'Water Absorb': ['Water'],
            'Flash Fire': ['Fire'],
            'Levitate': ['Ground'],
        }
        
        immune_types = ability_immunities.get(ability, [])
        return move_type in immune_types
    
    def _score_by_effect(self, move: Dict, user: any, target: any, battle_state: Dict) -> int:
        """Score move based on its effect type"""
        modifier = 0
        move_name_lower = move.get('name', '').lower()
        
        # Status moves
        if not move.get('causes_damage', True):
            modifier = self._score_status_move(move, user, target, battle_state, move_name_lower)
        
        # Recovery moves - check for heal effects
        if move.get('effects'):
            has_heal = any(eff.get('effect_type') == 'HEAL' and eff.get('heal_percentage', 0) > 0 
                          for eff in move.get('effects', []))
            if has_heal and user.current_hp >= user.max_hp:
                modifier = -8
        
        # Charge turn moves - check for Charge Turn effect
        if move.get('effects'):
            has_charge = any(eff.get('effect_name') == 'Charge Turn' or eff.get('field_condition') == 'Charge'
                           for eff in move.get('effects', []))
            if has_charge:
                # Penalize charge moves unless weather helps (Solar Beam)
                if 'solar' in move_name_lower and battle_state.get('weather', {}).get('type') != 'Sun':
                    modifier = -5
                else:
                    modifier = -3  # General penalty for charge moves
        
        # Stat boosting moves - check for STAT_CHANGE effects
        if move.get('effects'):
            has_stat_boost = any(eff.get('effect_type') == 'STAT_CHANGE' and 
                               eff.get('stat_change_amount', 0) > 0 and
                               eff.get('effect_target') == 'User'
                               for eff in move.get('effects', []))
            if has_stat_boost:
                modifier = self._score_stat_boost(move, user, target, battle_state)
        
        # Self-destruct/Explosion - check for RECOIL effects that KO the user
        if move.get('effects'):
            has_ko_recoil = any(eff.get('effect_type') == 'RECOIL' and 
                              eff.get('recoil_percentage', 0) >= 100
                              for eff in move.get('effects', []))
            if has_ko_recoil:
                # Check if immune
                if self._is_immune_by_type(move.get('type', 'Normal'), self.pokemon_repo.get_by_id(target.id)):
                    modifier = -10
                # Check if on last Pokemon
                # Simplified: assume we don't want to explode easily
                elif user.current_hp < user.max_hp * 0.3:
                    modifier = -10
        
        return modifier
    
    def _score_status_move(self, move: Dict, user: any, target: any, 
                          battle_state: Dict, move_name_lower: str) -> int:
        """Score status-inflicting moves using database effects"""
        modifier = 0
        
        # Check what status conditions this move inflicts
        effects = move.get('effects', [])
        
        for effect in effects:
            if effect.get('effect_type') == 'STATUS':
                status_condition = effect.get('status_condition', 'None')
                
                # Sleep moves
                if status_condition == 'Sleep':
                    if target.status is not None or hasattr(target, 'safeguard'):
                        modifier = -10
                
                # Poison moves
                elif status_condition == 'Poison':
                    target_data = self.pokemon_repo.get_by_id(target.id)
                    target_types = [target_data.get('type1'), target_data.get('type2')]
                    if 'Poison' in target_types or 'Steel' in target_types:
                        modifier = -10
                    elif target.status is not None:
                        modifier = -10
                
                # Paralysis moves
                elif status_condition == 'Paralysis':
                    if target.status is not None:
                        modifier = -10
                
                # Burn moves
                elif status_condition == 'Burn':
                    target_data = self.pokemon_repo.get_by_id(target.id)
                    target_types = [target_data.get('type1'), target_data.get('type2')]
                    if 'Fire' in target_types:
                        modifier = -10
                    elif target.status is not None:
                        modifier = -10
                
                # Confusion
                elif status_condition == 'Confusion':
                    if hasattr(target, 'confused') and target.confused:
                        modifier = -5
        
        return modifier
    
    def _score_stat_boost(self, move: Dict, user: any, target: any, battle_state: Dict) -> int:
        """Score stat-boosting moves using database effects"""
        modifier = 0
        
        # Get stat change effects
        effects = move.get('effects', [])
        for effect in effects:
            if effect.get('effect_type') == 'STAT_CHANGE' and effect.get('effect_target') == 'User':
                stat = effect.get('stat_to_change', '')
                amount = effect.get('stat_change_amount', 0)
                
                if amount > 0:  # Stat boost (ignore stat drops)
                    # Check if already at max stage for this stat
                    if stat == 'attack' and user.stat_stages.get('attack', 0) >= 6:
                        modifier = -10
                    elif stat == 'sp_attack' and user.stat_stages.get('sp_attack', 0) >= 6:
                        modifier = -10
                    elif stat == 'speed':
                        if user.stat_stages.get('speed', 0) >= 6:
                            modifier = -10
                        # Check Trick Room
                        if battle_state.get('field_effects', {}).get('trick_room', False):
                            modifier = -10
                    elif stat == 'defense' and user.stat_stages.get('defense', 0) >= 6:
                        modifier = -10
                    elif stat == 'sp_defense' and user.stat_stages.get('sp_defense', 0) >= 6:
                        modifier = -10
        
        return modifier
    
    # ========== EVALUATE ATTACK FLAG ==========
    
    def _apply_evaluate_attack_flag(self, move_scores: Dict, user: any, target: any):
        """
        Apply Evaluate Attack Flag scoring
        Philosophy: Prefer super effective moves, avoid not very effective moves
        """
        target_data = self.pokemon_repo.get_by_id(target.id)
        
        for move_id, data in move_scores.items():
            move = data['move']
            
            # Only evaluate damaging moves
            if not move.get('causes_damage', False) or move.get('power', 0) == 0:
                continue
            
            effectiveness = self._calculate_type_effectiveness(move.get('type', ''), target_data)
            
            if effectiveness > 1.0:
                # Super effective
                bonus = 10 if effectiveness >= 2.0 else 5
                data['score'] += bonus
                data['modifiers'].append(f"Super effective: +{bonus}")
            elif effectiveness < 1.0:
                # Not very effective
                penalty = -10 if effectiveness <= 0.5 else -5
                data['score'] += penalty
                data['modifiers'].append(f"Not very effective: {penalty}")
    
    def _calculate_type_effectiveness(self, attack_type: str, defender_data: Dict) -> float:
        """Calculate type effectiveness multiplier"""
        # Simplified type chart
        super_effective = {
            'Fire': ['Grass', 'Ice', 'Bug', 'Steel'],
            'Water': ['Fire', 'Ground', 'Rock'],
            'Electric': ['Water', 'Flying'],
            'Grass': ['Water', 'Ground', 'Rock'],
            'Ice': ['Grass', 'Ground', 'Flying', 'Dragon'],
            'Fighting': ['Normal', 'Ice', 'Rock', 'Dark', 'Steel'],
            'Poison': ['Grass', 'Fairy'],
            'Ground': ['Fire', 'Electric', 'Poison', 'Rock', 'Steel'],
            'Flying': ['Grass', 'Fighting', 'Bug'],
            'Psychic': ['Fighting', 'Poison'],
            'Bug': ['Grass', 'Psychic', 'Dark'],
            'Rock': ['Fire', 'Ice', 'Flying', 'Bug'],
            'Ghost': ['Psychic', 'Ghost'],
            'Dragon': ['Dragon'],
            'Dark': ['Psychic', 'Ghost'],
            'Steel': ['Ice', 'Rock', 'Fairy'],
            'Fairy': ['Fighting', 'Dragon', 'Dark'],
        }
        
        not_very_effective = {
            'Fire': ['Fire', 'Water', 'Rock', 'Dragon'],
            'Water': ['Water', 'Grass', 'Dragon'],
            'Electric': ['Electric', 'Grass', 'Dragon'],
            'Grass': ['Fire', 'Grass', 'Poison', 'Flying', 'Bug', 'Dragon', 'Steel'],
            'Ice': ['Fire', 'Water', 'Ice', 'Steel'],
            'Fighting': ['Poison', 'Flying', 'Psychic', 'Bug', 'Fairy'],
            'Poison': ['Poison', 'Ground', 'Rock', 'Ghost'],
            'Ground': ['Grass', 'Bug'],
            'Flying': ['Electric', 'Rock', 'Steel'],
            'Psychic': ['Psychic', 'Steel'],
            'Bug': ['Fire', 'Fighting', 'Poison', 'Flying', 'Ghost', 'Steel', 'Fairy'],
            'Rock': ['Fighting', 'Ground', 'Steel'],
            'Ghost': ['Dark'],
            'Dragon': ['Steel'],
            'Dark': ['Fighting', 'Dark', 'Fairy'],
            'Steel': ['Fire', 'Water', 'Electric', 'Steel'],
            'Fairy': ['Fire', 'Poison', 'Steel'],
        }
        
        defender_types = [defender_data.get('type1'), defender_data.get('type2')]
        multiplier = 1.0
        
        for def_type in defender_types:
            if def_type is None:
                continue
            
            if attack_type in super_effective and def_type in super_effective[attack_type]:
                multiplier *= 2.0
            elif attack_type in not_very_effective and def_type in not_very_effective[attack_type]:
                multiplier *= 0.5
        
        return multiplier
    
    # ========== EXPERT FLAG ==========
    
    def _apply_expert_flag(self, move_scores: Dict, user: any, target: any, battle_state: Dict):
        """
        Apply Expert Flag scoring
        Philosophy: Advanced tactics and prediction
        """
        for move_id, data in move_scores.items():
            move = data['move']
            move_name_lower = move.get('name', '').lower()
            
            # Prefer setup if target is slower and we're healthy
            if user.current_hp > user.max_hp * 0.7:
                # Check for stat-boosting moves (setup moves)
                has_stat_boost = any(eff.get('effect_type') == 'STAT_CHANGE' and 
                                   eff.get('stat_change_amount', 0) > 0 and
                                   eff.get('effect_target') == 'User'
                                   for eff in move.get('effects', []))
                if has_stat_boost and user.speed > target.speed:
                    data['score'] += 5
                    data['modifiers'].append("Expert: Setup opportunity +5")
            
            # Avoid setting up if low HP
            if user.current_hp < user.max_hp * 0.4:
                if not move.get('causes_damage', True):
                    data['score'] -= 5
                    data['modifiers'].append("Expert: Low HP, prefer damage -5")
            
            # Prefer coverage moves if main attack is resisted
            if move.get('causes_damage', False):
                user_data = self.pokemon_repo.get_by_id(user.id)
                move_type = move.get('type', '')
                
                # STAB bonus consideration
                if move_type in [user_data.get('type1'), user_data.get('type2')]:
                    data['score'] += 3
                    data['modifiers'].append("Expert: STAB +3")
    
    # ========== CHECK HP FLAG ==========
    
    def _apply_check_hp_flag(self, move_scores: Dict, user: any, target: any):
        """
        Apply Check HP Flag scoring
        Philosophy: Make decisions based on HP thresholds
        """
        user_hp_percent = user.current_hp / user.max_hp
        target_hp_percent = target.current_hp / target.max_hp
        
        for move_id, data in move_scores.items():
            move = data['move']
            move_name_lower = move.get('name', '').lower()
            
            # Healing moves when low HP - check for HEAL effects
            has_heal = any(eff.get('effect_type') == 'HEAL' and eff.get('heal_percentage', 0) > 0 
                          for eff in move.get('effects', []))
            if has_heal:
                if user_hp_percent < 0.3:
                    data['score'] += 20
                    data['modifiers'].append("Check HP: Critical HP, heal +20")
                elif user_hp_percent < 0.5:
                    data['score'] += 10
                    data['modifiers'].append("Check HP: Low HP, heal +10")
            
            # Aggressive when target is low
            if move.get('causes_damage', False) and move.get('power', 0) > 0:
                if target_hp_percent < 0.25:
                    data['score'] += 10
                    data['modifiers'].append("Check HP: Target low, finish off +10")
            
            # Don't waste big moves on low HP targets
            power = move.get('power', 0)
            if power and power >= 100 and target_hp_percent < 0.15:
                data['score'] -= 5
                data['modifiers'].append("Check HP: Overkill -5")
    
    # ========== PRIORITIZE DAMAGE FLAG ==========
    
    def _apply_prioritize_damage_flag(self, move_scores: Dict, user: any, target: any):
        """
        Apply Prioritize Damage Flag scoring
        Philosophy: Prefer damaging moves over status moves
        """
        for move_id, data in move_scores.items():
            move = data['move']
            
            if move.get('causes_damage', False) and move.get('power', 0) > 0:
                power = move.get('power', 0)
                
                # Bonus for high power moves
                if power >= 100:
                    data['score'] += 10
                    data['modifiers'].append("Prioritize Damage: High power +10")
                elif power >= 80:
                    data['score'] += 5
                    data['modifiers'].append("Prioritize Damage: Good power +5")
            else:
                # Penalty for non-damaging moves
                data['score'] -= 5
                data['modifiers'].append("Prioritize Damage: Status move -5")
    
    # ========== UTILITY METHODS ==========
    
    def _create_default_battle_state(self) -> Dict:
        """Create a default battle state"""
        return {
            'weather': {'type': 'None', 'turns_remaining': 0},
            'field_effects': {
                'trick_room': False,
                'terrain': None,
                'reflect_p1': 0,
                'light_screen_p1': 0,
                'reflect_p2': 0,
                'light_screen_p2': 0,
            },
            'turn_count': 1
        }
    
    def get_difficulty_description(self) -> str:
        """Get description of AI difficulty"""
        flag_names = [flag.value for flag in self.flags]
        return f"Flags: {', '.join(flag_names)}"


# ========== EXAMPLE USAGE ==========

if __name__ == "__main__":
    from Pokemon import Pokemon
    
    print("="*70)
    print("CPU AI SYSTEM DEMONSTRATION")
    print("="*70)
    
    # Create test Pokemon
    print("\nCreating battle scenario...")
    pikachu = Pokemon(25, level=50, moveset=[85, 87, 92, 113])  # Thunder, Thunderbolt, Quick Attack, Thunder Wave
    charizard = Pokemon(6, level=50, moveset=[52, 53, 17, 99])  # Flamethrower, Fire Blast, Wing Attack, Rage
    
    print(f"AI Pokemon: {pikachu.name}")
    print(f"Opponent: {charizard.name}")
    
    # Test different difficulty levels
    difficulties = ["easy", "normal", "hard", "expert"]
    
    for difficulty in difficulties:
        print(f"\n{'='*70}")
        print(f"Testing {difficulty.upper()} AI")
        print(f"{'='*70}")
        
        ai = CPUTrainer(difficulty=difficulty)
        print(f"Active Flags: {', '.join(f.value for f in ai.flags)}")
        
        # Make 3 move choices to show consistency and randomness
        for i in range(3):
            result = ai.choose_move(pikachu, charizard)
            print(f"\nChoice #{i+1}:")
            print(f"  Selected Move: {result['move']['name']}")
            print(f"  Score: {result['score']}")
            print(f"  Reason: {result['reason']}")
    
    print("\n" + "="*70)
    print("[OK] CPU AI System ready!")
    print("="*70)
