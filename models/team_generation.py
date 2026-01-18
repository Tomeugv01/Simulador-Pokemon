"""
Roguelike Pokémon Team & Move Generation System
Implements stat budget-based team generation for progressive difficulty
"""
import random
import sys
import os
from typing import List, Dict, Optional, Tuple
from enum import Enum

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(__file__)), 'src'))

try:
    from repositories import PokemonRepository, MoveRepository
    from Pokemon import Pokemon
    from experience import ExperienceCurve
    from database import get_available_moves_for_level
except ImportError:
    from src.repositories import PokemonRepository, MoveRepository
    from models.Pokemon import Pokemon
    from models.experience import ExperienceCurve
    from src.database import get_available_moves_for_level


class TeamComposition(Enum):
    """AI team composition patterns"""
    BALANCED = "balanced"  # All budgets near middle
    GLASS_CANNON = "glass_cannon"  # 1 strong, 2 medium, 3 weak
    SWARM = "swarm"  # All weak
    ACE_TEAM = "ace_team"  # 1-2 very strong, rest medium
    MIXED = "mixed"  # Random distribution


class RewardChoice(Enum):
    """Post-battle reward choices"""
    ADD_POKEMON = "add_pokemon"
    REPLACE_POKEMON = "replace_pokemon"
    LEARN_MOVE = "learn_move"


class Archetype(Enum):
    """Pokemon archetypes based on stat distribution"""
    PHYSICAL_ATTACKER = "physical_attacker"
    SPECIAL_ATTACKER = "special_attacker"
    TANK = "tank"
    GLASS_CANNON = "glass_cannon"
    SPEEDSTER = "speedster"
    MIXED_ATTACKER = "mixed_attacker"
    WALL = "wall"


class TeamGenerator:
    """Handles team generation for roguelike progression"""
    
    def __init__(self, db_path="data/pokemon_battle.db"):
        """
        Initialize the team generator
        
        Args:
            db_path: Path to the Pokemon database
        """
        self.pokemon_repo = PokemonRepository(db_path)
        self.move_repo = MoveRepository(db_path)
        self.all_pokemon = self.pokemon_repo.get_all()
        
        # Cache Pokemon by TSB ranges for faster lookup
        self._build_tsb_cache()
    
    def _build_tsb_cache(self):
        """Build a cache of Pokemon grouped by TSB ranges"""
        self.tsb_cache = {}
        
        for pokemon in self.all_pokemon:
            tsb = pokemon['total_stats']
            # Group by 50-point ranges
            range_key = (tsb // 50) * 50
            
            if range_key not in self.tsb_cache:
                self.tsb_cache[range_key] = []
            
            self.tsb_cache[range_key].append(pokemon)
    
    def calculate_tsb(self, pokemon_data: Dict) -> int:
        """
        Calculate Total Stat Budget for a Pokemon
        
        Args:
            pokemon_data: Dictionary with base stats
            
        Returns:
            Total stat budget (TSB)
        """
        return pokemon_data.get('total_stats', 0)
    
    def _get_type_name(self, type_id: int) -> str:
        """
        Convert type ID to type name
        
        Args:
            type_id: Type ID (1-18)
            
        Returns:
            Type name string
        """
        type_map = {
            1: 'Normal', 2: 'Fire', 3: 'Water', 4: 'Electric', 5: 'Grass',
            6: 'Ice', 7: 'Fighting', 8: 'Poison', 9: 'Ground', 10: 'Flying',
            11: 'Psychic', 12: 'Bug', 13: 'Rock', 14: 'Ghost', 15: 'Dragon',
            16: 'Dark', 17: 'Steel', 18: 'Fairy'
        }
        return type_map.get(type_id, 'Normal')
    
    # ========== OPPONENT TEAM GENERATION ==========
    
    def generate_opponent_team(self, round_number: int, team_size: int = 6,
                              composition: Optional[TeamComposition] = None) -> List[Pokemon]:
        """
        Generate an opponent team for a specific round
        
        Args:
            round_number: Current round/encounter number (1-indexed)
            team_size: Number of Pokemon in the team (default 6)
            composition: Team composition pattern (random if None)
            
        Returns:
            List of Pokemon objects for the opponent team
        """
        # Step 1: Determine TSB range for this round
        tsb_min, tsb_max = self._calculate_round_tsb_range(round_number)
        
        # Step 2: Choose composition pattern
        if composition is None:
            composition = random.choice(list(TeamComposition))
        
        # Step 3: Assign individual Pokemon budgets
        budgets = self._assign_team_budgets(team_size, tsb_min, tsb_max, composition)
        
        # Step 4: Generate Pokemon from budgets
        team = []
        for budget in budgets:
            pokemon_data = self._select_pokemon_by_budget(budget, tolerance=10)
            if pokemon_data:
                # Create Pokemon instance with random moves
                pokemon = self._create_pokemon_instance(pokemon_data, round_number)
                team.append(pokemon)
        
        return team
    
    def _calculate_round_tsb_range(self, round_number: int) -> Tuple[int, int]:
        """
        Calculate TSB range for a given round
        
        Args:
            round_number: Current round (1-indexed)
            
        Returns:
            Tuple of (min_tsb, max_tsb)
        """
        # Base formula: increases with round number
        # Early rounds: tight range, low power
        # Late rounds: wider range, high power
        
        base_tsb = 250 + (round_number - 1) * 30  # Starts at 250, +30 per round
        variance_percent = 10 + round_number * 2  # Variance grows with rounds
        
        variance = int(base_tsb * variance_percent / 100)
        
        tsb_min = max(200, base_tsb - variance)  # Floor at 200
        tsb_max = min(600, base_tsb + variance)  # Cap at 600
        
        return tsb_min, tsb_max
    
    def _assign_team_budgets(self, team_size: int, tsb_min: int, tsb_max: int,
                            composition: TeamComposition) -> List[int]:
        """
        Assign individual TSB values to each team slot
        
        Args:
            team_size: Number of Pokemon
            tsb_min: Minimum TSB for this round
            tsb_max: Maximum TSB for this round
            composition: Team composition pattern
            
        Returns:
            List of TSB values for each team member
        """
        budgets = []
        mid_point = (tsb_min + tsb_max) // 2
        
        if composition == TeamComposition.BALANCED:
            # All budgets near the middle with small variance
            for _ in range(team_size):
                budgets.append(random.randint(mid_point - 20, mid_point + 20))
        
        elif composition == TeamComposition.GLASS_CANNON:
            # 1 at max, 2 at mid, 3 at min
            budgets.append(random.randint(tsb_max - 20, tsb_max))  # 1 strong
            budgets.extend([random.randint(mid_point - 15, mid_point + 15) for _ in range(2)])  # 2 medium
            budgets.extend([random.randint(tsb_min, tsb_min + 30) for _ in range(3)])  # 3 weak
        
        elif composition == TeamComposition.SWARM:
            # All at low end
            for _ in range(team_size):
                budgets.append(random.randint(tsb_min, tsb_min + 40))
        
        elif composition == TeamComposition.ACE_TEAM:
            # 1-2 very strong, rest medium
            num_aces = random.randint(1, 2)
            for _ in range(num_aces):
                budgets.append(random.randint(tsb_max - 30, tsb_max))
            for _ in range(team_size - num_aces):
                budgets.append(random.randint(mid_point - 25, mid_point + 25))
        
        else:  # MIXED
            # Random distribution across the range
            for _ in range(team_size):
                budgets.append(random.randint(tsb_min, tsb_max))
        
        # Shuffle to randomize positions
        random.shuffle(budgets)
        
        return budgets[:team_size]
    
    def _select_pokemon_by_budget(self, target_tsb: int, tolerance: int = 10) -> Optional[Dict]:
        """
        Select a random Pokemon within TSB tolerance
        
        Args:
            target_tsb: Target total stat budget
            tolerance: Acceptable deviation from target
            
        Returns:
            Pokemon data dictionary or None
        """
        # Find candidates within tolerance
        candidates = []
        
        # Check nearby TSB ranges in cache
        range_key = (target_tsb // 50) * 50
        for offset in [0, -50, 50]:
            check_key = range_key + offset
            if check_key in self.tsb_cache:
                for pokemon in self.tsb_cache[check_key]:
                    if abs(pokemon['total_stats'] - target_tsb) <= tolerance:
                        candidates.append(pokemon)
        
        # If no exact matches, expand tolerance
        if not candidates:
            for pokemon in self.all_pokemon:
                if abs(pokemon['total_stats'] - target_tsb) <= tolerance * 2:
                    candidates.append(pokemon)
        
        # Select random from candidates
        if candidates:
            return random.choice(candidates)
        
        # Fallback: closest match
        return min(self.all_pokemon, key=lambda p: abs(p['total_stats'] - target_tsb))
    
    def _create_pokemon_instance(self, pokemon_data: Dict, round_number: int,
                                level: Optional[int] = None) -> Pokemon:
        """
        Create a Pokemon instance with moves
        
        Args:
            pokemon_data: Pokemon base data
            round_number: Current round for level scaling
            level: Override level (default: scaled by round and growth curve)
            
        Returns:
            Pokemon instance
        """
        # Calculate level based on round
        if level is None:
            # Progressive level scaling: Round 1 matches player (5), then increases
            # Round 1: 5, Round 2: 7, Round 3: 9, Round 5: 15, Round 10: 35
            base_level = 5
            if round_number == 1:
                base_level = base_level  # Same as player in Round 1
            else:
                level_per_round = 2 + (round_number // 3)  # Accelerating growth
                base_level = min(100, base_level + round_number * level_per_round)
            
            # Adjust level based on Pokemon's growth curve
            # Fast-growing Pokemon get higher levels, slow-growing get lower levels
            # This balances difficulty so all Pokemon are competitive
            exp_curve = pokemon_data.get('exp_curve', 'medium-fast')
            level = ExperienceCurve.scale_level_for_curve(base_level, exp_curve)
        
        # Create Pokemon instance
        pokemon = Pokemon(
            pokemon_id=pokemon_data['id'],
            level=level,
            ivs={'hp': 31, 'attack': 31, 'defense': 31, 
                 'sp_attack': 31, 'sp_defense': 31, 'speed': 31},
            evs={'hp': 85, 'attack': 85, 'defense': 85,
                 'sp_attack': 85, 'sp_defense': 85, 'speed': 85}
        )
        
        # Determine number of moves based on Pokemon strength (TSB)
        tsb = self.calculate_tsb(pokemon_data)
        num_moves = self._determine_move_count(tsb, level, round_number)
        
        # Get moves from learnset based on Pokemon's level
        learnset_moves = get_available_moves_for_level(
            pokemon_id=pokemon_data['id'],
            current_level=level,
            count=num_moves
        )
        
        # Convert move IDs to move data dictionaries
        if learnset_moves:
            moves = [self.move_repo.get_by_id(move['id']) for move in learnset_moves]
        else:
            # Fallback: If no learnset data, use archetype-based system
            moves = self._select_moves_for_pokemon(pokemon_data, round_number, num_moves)
        
        pokemon.moves = moves
        
        return pokemon
    
    # ========== ARCHETYPE SYSTEM ==========
    
    def _determine_move_count(self, tsb: int, level: int, round_number: int) -> int:
        """
        Determine how many moves a Pokemon should have based on its strength.
        Weaker Pokemon have 2-3 moves, stronger ones have 4.
        
        Args:
            tsb: Total Stat Budget
            level: Pokemon level
            round_number: Current round
            
        Returns:
            Number of moves (2-4)
        """
        # Weak Pokemon (TSB < 300): 2-3 moves
        if tsb < 300:
            # Very early game: 2 moves
            if round_number <= 2:
                return 2
            # Early game: 2-3 moves
            elif round_number <= 5:
                return random.choice([2, 3])
            # Later they catch up
            else:
                return random.choice([3, 4])
        
        # Medium Pokemon (300-450): 3-4 moves
        elif tsb < 450:
            if round_number <= 3:
                return 3
            else:
                return 4
        
        # Strong Pokemon (450+): Always 4 moves
        else:
            return 4
    
    def _calculate_max_move_power(self, pokemon_data: Dict, level: int) -> int:
        """
        Calculate maximum allowed move power based on Pokemon level and TSB
        Prevents low-level/weak Pokemon from having overpowered moves
        
        Args:
            pokemon_data: Pokemon base data
            level: Pokemon's current level
            
        Returns:
            Maximum move power allowed
        """
        tsb = pokemon_data['total_stats']
        
        # Base power cap scales with level
        # Level 1-10: 60-80 power (increased to allow basic damage moves)
        # Level 11-20: 70-90 power
        # Level 21-40: 80-110 power
        # Level 41-60: 90-130 power
        # Level 61+: No cap (or 150)
        
        if level <= 10:
            level_cap = 60 + (level * 2)  # 60-80
        elif level <= 20:
            level_cap = 70 + ((level - 10) * 2)  # 70-90
        elif level <= 40:
            level_cap = 80 + ((level - 20) * 1.5)  # 80-110
        elif level <= 60:
            level_cap = 90 + ((level - 40) * 2)  # 90-130
        else:
            level_cap = 150  # Max power moves allowed
        
        # TSB also affects cap (stronger Pokemon get stronger moves)
        # TSB < 300: no penalty (allow basic moves)
        # TSB 300-400: +5 power
        # TSB 400-500: +15 power
        # TSB 500+: +25 power
        
        if tsb < 300:
            tsb_modifier = 0  # Changed: don't penalize weak Pokemon
        elif tsb < 400:
            tsb_modifier = 5
        elif tsb < 500:
            tsb_modifier = 15
        else:
            tsb_modifier = 25
        
        max_power = int(level_cap + tsb_modifier)
        
        # Minimum cap of 70 (allow basic damage moves like Bug Bite 60, etc.)
        return max(70, max_power)
    
    def _calculate_stat_percentages(self, pokemon_data: Dict) -> Dict[str, float]:
        """
        Calculate the percentage each stat contributes to TSB
        
        Args:
            pokemon_data: Pokemon base data
            
        Returns:
            Dictionary with stat percentages
        """
        tsb = pokemon_data['total_stats']
        
        if tsb == 0:
            return {
                'hp': 0, 'attack': 0, 'defense': 0,
                'sp_attack': 0, 'sp_defense': 0, 'speed': 0
            }
        
        return {
            'hp': (pokemon_data['hp'] / tsb) * 100,
            'attack': (pokemon_data['attack'] / tsb) * 100,
            'defense': (pokemon_data['defense'] / tsb) * 100,
            'sp_attack': (pokemon_data['special_attack'] / tsb) * 100,
            'sp_defense': (pokemon_data['special_defense'] / tsb) * 100,
            'speed': (pokemon_data['speed'] / tsb) * 100
        }
    
    def _determine_archetypes(self, pokemon_data: Dict) -> List[Archetype]:
        """
        Determine which archetypes a Pokemon qualifies for
        
        Args:
            pokemon_data: Pokemon base data
            
        Returns:
            List of qualifying archetypes
        """
        stats = self._calculate_stat_percentages(pokemon_data)
        archetypes = []
        
        # Physical Attacker: %Atk > 25% AND %Atk > %SpA
        if stats['attack'] > 25 and stats['attack'] > stats['sp_attack']:
            archetypes.append(Archetype.PHYSICAL_ATTACKER)
        
        # Special Attacker: %SpA > 25% AND %SpA > %Atk
        if stats['sp_attack'] > 25 and stats['sp_attack'] > stats['attack']:
            archetypes.append(Archetype.SPECIAL_ATTACKER)
        
        # Tank: (%HP + %Def + %SpD) > 50%
        if (stats['hp'] + stats['defense'] + stats['sp_defense']) > 50:
            archetypes.append(Archetype.TANK)
        
        # Glass Cannon: (%Atk + %SpA) > 45% AND (%Def + %SpD) < 25%
        if ((stats['attack'] + stats['sp_attack']) > 45 and
            (stats['defense'] + stats['sp_defense']) < 25):
            archetypes.append(Archetype.GLASS_CANNON)
        
        # Speedster: %Spe > 22%
        if stats['speed'] > 22:
            archetypes.append(Archetype.SPEEDSTER)
        
        # Mixed Attacker: Both Atk and SpA > 20%
        if stats['attack'] > 20 and stats['sp_attack'] > 20:
            archetypes.append(Archetype.MIXED_ATTACKER)
        
        # Wall: (%HP + %Def + %SpD) > 55% (stronger defensive requirement)
        if (stats['hp'] + stats['defense'] + stats['sp_defense']) > 55:
            archetypes.append(Archetype.WALL)
        
        # Default: If no archetype, assign based on highest offensive stat
        if not archetypes:
            if stats['attack'] >= stats['sp_attack']:
                archetypes.append(Archetype.PHYSICAL_ATTACKER)
            else:
                archetypes.append(Archetype.SPECIAL_ATTACKER)
        
        return archetypes
    
    def _get_archetype_move_pools(self, archetypes: List[Archetype], 
                                  pokemon_data: Dict) -> Dict[str, List[Dict]]:
        """
        Get move pools for each archetype
        
        Args:
            archetypes: List of Pokemon's archetypes
            pokemon_data: Pokemon base data
            
        Returns:
            Dictionary categorizing moves by type
        """
        all_moves = self.move_repo.get_all()
        type1 = pokemon_data['type1']
        type2 = pokemon_data.get('type2')
        
        # Categorize all moves
        physical_moves = [m for m in all_moves if m['category'] == 'physical' and m['causes_damage']]
        special_moves = [m for m in all_moves if m['category'] == 'special' and m['causes_damage']]
        status_moves = [m for m in all_moves if not m['causes_damage']]
        
        # STAB moves
        stab_physical = [m for m in physical_moves if m['type'] in [type1, type2]]
        stab_special = [m for m in special_moves if m['type'] in [type1, type2]]
        
        # Coverage moves (non-STAB)
        coverage_physical = [m for m in physical_moves if m['type'] not in [type1, type2]]
        coverage_special = [m for m in special_moves if m['type'] not in [type1, type2]]
        
        # Defensive/utility moves
        recovery_moves = [m for m in status_moves if any(keyword in m['name'].lower()
                         for keyword in ['recover', 'roost', 'rest', 'moonlight', 'morning sun',
                                       'synthesis', 'wish', 'heal', 'slack off', 'shore up'])]
        
        setup_moves = [m for m in status_moves if any(keyword in m['name'].lower()
                      for keyword in ['swords dance', 'dragon dance', 'nasty plot', 'calm mind',
                                    'quiver dance', 'shell smash', 'bulk up', 'coil', 'curse',
                                    'amnesia', 'iron defense', 'agility', 'rock polish'])]
        
        disruption_moves = [m for m in status_moves if any(keyword in m['name'].lower()
                           for keyword in ['will-o-wisp', 'thunder wave', 'toxic', 'spore',
                                         'sleep powder', 'stun spore', 'taunt', 'encore',
                                         'disable', 'torment'])]
        
        protection_moves = [m for m in status_moves if any(keyword in m['name'].lower()
                           for keyword in ['protect', 'detect', 'substitute', 'reflect',
                                         'light screen', 'aurora veil'])]
        
        utility_moves = [m for m in status_moves if any(keyword in m['name'].lower()
                        for keyword in ['stealth rock', 'spikes', 'toxic spikes', 'rapid spin',
                                      'defog', 'trick', 'switcheroo', 'baton pass', 'u-turn',
                                      'volt switch', 'flip turn', 'teleport'])]
        
        # Build move pool based on archetypes
        move_pool = {
            'reliable_physical': [],
            'reliable_special': [],
            'coverage_physical': [],
            'coverage_special': [],
            'status': []
        }
        
        for archetype in archetypes:
            if archetype == Archetype.PHYSICAL_ATTACKER:
                move_pool['reliable_physical'].extend(stab_physical)
                move_pool['coverage_physical'].extend(coverage_physical)
                move_pool['status'].extend(setup_moves + protection_moves)
            
            elif archetype == Archetype.SPECIAL_ATTACKER:
                move_pool['reliable_special'].extend(stab_special)
                move_pool['coverage_special'].extend(coverage_special)
                move_pool['status'].extend(setup_moves + protection_moves)
            
            elif archetype == Archetype.TANK:
                move_pool['status'].extend(recovery_moves + disruption_moves + protection_moves)
                # Tanks can still have STAB moves
                move_pool['reliable_physical'].extend(stab_physical)
                move_pool['reliable_special'].extend(stab_special)
            
            elif archetype == Archetype.GLASS_CANNON:
                move_pool['reliable_physical'].extend(stab_physical)
                move_pool['reliable_special'].extend(stab_special)
                move_pool['coverage_physical'].extend(coverage_physical)
                move_pool['coverage_special'].extend(coverage_special)
                move_pool['status'].extend(setup_moves)
            
            elif archetype == Archetype.SPEEDSTER:
                move_pool['reliable_physical'].extend(stab_physical)
                move_pool['reliable_special'].extend(stab_special)
                move_pool['coverage_physical'].extend(coverage_physical)
                move_pool['coverage_special'].extend(coverage_special)
                move_pool['status'].extend(utility_moves + disruption_moves)
            
            elif archetype == Archetype.MIXED_ATTACKER:
                move_pool['reliable_physical'].extend(stab_physical)
                move_pool['reliable_special'].extend(stab_special)
                move_pool['coverage_physical'].extend(coverage_physical)
                move_pool['coverage_special'].extend(coverage_special)
            
            elif archetype == Archetype.WALL:
                move_pool['status'].extend(recovery_moves + protection_moves + disruption_moves)
                move_pool['reliable_physical'].extend(stab_physical)
                move_pool['reliable_special'].extend(stab_special)
        
        # Remove duplicates
        for key in move_pool:
            move_pool[key] = list({m['id']: m for m in move_pool[key]}.values())
        
        return move_pool
    
    def _select_moves_for_pokemon(self, pokemon_data: Dict, round_number: int,
                                 num_moves: int = 4) -> List[Dict]:
        """
        Select appropriate moves for a Pokemon using archetype system.
        Weaker Pokemon get type-matching moves for predictability.
        
        Args:
            pokemon_data: Pokemon base data
            round_number: Current round
            num_moves: Number of moves to select (2-4)
            
        Returns:
            List of move dictionaries
        """
        # Determine archetypes
        archetypes = self._determine_archetypes(pokemon_data)
        
        # Get move pools based on archetypes
        move_pool = self._get_archetype_move_pools(archetypes, pokemon_data)
        
        # Calculate maximum allowed move power for this Pokemon
        max_power = self._calculate_max_move_power(pokemon_data, round_number * 3 + 2)
        
        # Filter moves by power cap
        for category in move_pool:
            move_pool[category] = [m for m in move_pool[category] 
                                  if not m.get('power') or m['power'] <= max_power]
        
        # Check if this is a weak Pokemon (for type-matching priority)
        tsb = self.calculate_tsb(pokemon_data)
        is_weak_pokemon = tsb < 300
        
        # Get Pokemon types for type-matching
        pokemon_types = [self._get_type_name(pokemon_data['type1'])]
        if pokemon_data.get('type2'):
            pokemon_types.append(self._get_type_name(pokemon_data['type2']))
        
        # Calculate stat percentages to determine offensive preference
        stats = self._calculate_stat_percentages(pokemon_data)
        prefers_physical = stats['attack'] >= stats['sp_attack']
        
        selected_moves = []
        
        # WEAK POKEMON: Prioritize type-matching DAMAGE moves for predictability
        if is_weak_pokemon:
            # Get ALL damage moves of the Pokemon's type (bypass archetype restrictions)
            all_moves = self.move_repo.get_all()
            type1_name = self._get_type_name(pokemon_data['type1'])
            type2_name = self._get_type_name(pokemon_data['type2']) if pokemon_data.get('type2') else None
            
            # Get type-matching damage moves
            type_matching_damage = [
                m for m in all_moves 
                if m['causes_damage'] and m['type'] in pokemon_types
                and (not m.get('power') or m['power'] <= max_power)
            ]
            
            # Separate by category
            type_matching_physical = [m for m in type_matching_damage if m['category'] == 'Physical']
            type_matching_special = [m for m in type_matching_damage if m['category'] == 'Special']
            
            # Select first move: type-matching damage move
            if prefers_physical and type_matching_physical:
                selected_moves.append(random.choice(type_matching_physical))
            elif type_matching_special:
                selected_moves.append(random.choice(type_matching_special))
            elif type_matching_physical:
                # Fallback to physical even if not preferred
                selected_moves.append(random.choice(type_matching_physical))
            
            # If 2+ moves, add another type-matching damage move (different if possible)
            if num_moves >= 2 and len(selected_moves) < num_moves:
                remaining_type_damage = [m for m in type_matching_damage if m not in selected_moves]
                if remaining_type_damage:
                    selected_moves.append(random.choice(remaining_type_damage))
            
            # Fill remaining slots with any type-matching moves
            if len(selected_moves) < num_moves:
                all_type_moves = [
                    m for m in all_moves
                    if m['type'] in pokemon_types 
                    and m not in selected_moves
                    and (not m.get('power') or m['power'] <= max_power)
                ]
                random.shuffle(all_type_moves)
                for move in all_type_moves:
                    if len(selected_moves) >= num_moves:
                        break
                    selected_moves.append(move)
        
        # NORMAL POKEMON: Standard selection
        else:
            # CRITICAL RULE: Ensure at least ONE reliable damaging move
            # Try archetype pools first
            if prefers_physical and move_pool['reliable_physical']:
                selected_moves.append(random.choice(move_pool['reliable_physical']))
            elif move_pool['reliable_special']:
                selected_moves.append(random.choice(move_pool['reliable_special']))
            elif move_pool['reliable_physical']:
                selected_moves.append(random.choice(move_pool['reliable_physical']))
            
            # If archetype pools are empty, forcibly add STAB damage move
            if not selected_moves:
                all_moves = self.move_repo.get_all()
                type1_name = self._get_type_name(pokemon_data['type1'])
                type2_name = self._get_type_name(pokemon_data['type2']) if pokemon_data.get('type2') else None
                pokemon_types = [type1_name]
                if type2_name:
                    pokemon_types.append(type2_name)
                
                # Get STAB damage moves within power cap
                stab_damage = [
                    m for m in all_moves 
                    if m['causes_damage'] and m['type'] in pokemon_types
                    and (not m.get('power') or m['power'] <= max_power)
                ]
                
                if stab_damage:
                    if prefers_physical:
                        physical_stab = [m for m in stab_damage if m['category'] == 'Physical']
                        if physical_stab:
                            selected_moves.append(random.choice(physical_stab))
                        else:
                            selected_moves.append(random.choice(stab_damage))
                    else:
                        special_stab = [m for m in stab_damage if m['category'] == 'Special']
                        if special_stab:
                            selected_moves.append(random.choice(special_stab))
                        else:
                            selected_moves.append(random.choice(stab_damage))
        
        # Build combined potential move list from all categories
        potential_moves = []
        
        # Add remaining reliable moves
        if prefers_physical:
            potential_moves.extend([m for m in move_pool['reliable_physical'] if m not in selected_moves])
            potential_moves.extend([m for m in move_pool['coverage_physical'] if m not in selected_moves])
        else:
            potential_moves.extend([m for m in move_pool['reliable_special'] if m not in selected_moves])
            potential_moves.extend([m for m in move_pool['coverage_special'] if m not in selected_moves])
        
        # Add opposite category coverage (for mixed attackers)
        if Archetype.MIXED_ATTACKER in archetypes:
            if prefers_physical:
                potential_moves.extend([m for m in move_pool['reliable_special'] if m not in selected_moves])
                potential_moves.extend([m for m in move_pool['coverage_special'] if m not in selected_moves])
            else:
                potential_moves.extend([m for m in move_pool['reliable_physical'] if m not in selected_moves])
                potential_moves.extend([m for m in move_pool['coverage_physical'] if m not in selected_moves])
        
        # Add status moves
        potential_moves.extend([m for m in move_pool['status'] if m not in selected_moves])
        
        # Randomly select remaining moves
        random.shuffle(potential_moves)
        
        for move in potential_moves:
            if len(selected_moves) >= num_moves:
                break
            if move not in selected_moves:
                selected_moves.append(move)
        
        # Final fallback: Add any damaging moves within power cap
        while len(selected_moves) < num_moves:
            all_moves = self.move_repo.get_all()
            remaining = [m for m in all_moves 
                        if m not in selected_moves 
                        and m['causes_damage']
                        and (not m.get('power') or m['power'] <= max_power)]
            if not remaining:
                # If still no moves, relax power cap
                remaining = [m for m in all_moves if m not in selected_moves and m['causes_damage']]
            if not remaining:
                break
            selected_moves.append(random.choice(remaining))
        
        return selected_moves[:num_moves]
    
    # ========== PLAYER MOVE LEARNING SYSTEM ==========
    
    def get_pokemon_archetypes(self, pokemon: Pokemon) -> List[Archetype]:
        """
        Get archetypes for a Pokemon instance
        
        Args:
            pokemon: Pokemon instance
            
        Returns:
            List of archetypes
        """
        # Convert Pokemon instance to data dict
        pokemon_data = self.pokemon_repo.get_by_id(pokemon.id)
        return self._determine_archetypes(pokemon_data)
    
    def get_filtered_moves_for_learning(self, pokemon: Pokemon,
                                       archetype_filter: Optional[Archetype] = None,
                                       type_filter: Optional[str] = None,
                                       damage_class_filter: Optional[str] = None,
                                       respect_power_cap: bool = True) -> List[Dict]:
        """
        Get filtered list of moves for player to learn
        
        Args:
            pokemon: Pokemon that will learn the move
            archetype_filter: Filter by archetype (optional)
            type_filter: Filter by type (e.g., "Fire", "Water") (optional)
            damage_class_filter: Filter by damage class ("physical", "special", "status") (optional)
            respect_power_cap: Apply power cap based on level/TSB (default True)
            
        Returns:
            List of move dictionaries matching filters
        """
        all_moves = self.move_repo.get_all()
        pokemon_data = self.pokemon_repo.get_by_id(pokemon.id)
        
        # Start with all moves
        filtered_moves = all_moves.copy()
        
        # Apply power cap if requested
        if respect_power_cap:
            max_power = self._calculate_max_move_power(pokemon_data, pokemon.level)
            filtered_moves = [m for m in filtered_moves 
                            if not m.get('power') or m['power'] <= max_power]
        
        # Apply archetype filter
        if archetype_filter:
            archetypes = [archetype_filter]
            move_pool = self._get_archetype_move_pools(archetypes, pokemon_data)
            
            # Combine all moves from archetype pools
            archetype_moves = []
            for category in move_pool.values():
                archetype_moves.extend(category)
            
            # Remove duplicates by ID
            archetype_move_ids = {m['id'] for m in archetype_moves}
            filtered_moves = [m for m in filtered_moves if m['id'] in archetype_move_ids]
        
        # Apply type filter
        if type_filter:
            # Convert type filter to string if it's an integer (type ID)
            if isinstance(type_filter, int):
                # Type IDs map to type names - we need to handle this
                # For now, skip filtering by ID since moves store type names
                pass
            else:
                filtered_moves = [m for m in filtered_moves if m['type'].lower() == type_filter.lower()]
        
        # Apply damage class filter
        if damage_class_filter:
            if damage_class_filter.lower() == 'status':
                filtered_moves = [m for m in filtered_moves if not m['causes_damage']]
            else:
                filtered_moves = [m for m in filtered_moves if 
                                m['category'].lower() == damage_class_filter.lower()]
        
        return filtered_moves
    
    def display_move_learning_interface(self, pokemon: Pokemon):
        """
        Display interactive move learning interface
        
        Args:
            pokemon: Pokemon that will learn a move
        """
        print("\n" + "="*60)
        print(f"MOVE LEARNING - {pokemon.name}")
        print("="*60)
        
        # Show power cap
        pokemon_data = self.pokemon_repo.get_by_id(pokemon.id)
        max_power = self._calculate_max_move_power(pokemon_data, pokemon.level)
        print(f"\nMax Move Power (Level {pokemon.level}): {max_power}")
        
        # Show Pokemon's archetypes
        archetypes = self.get_pokemon_archetypes(pokemon)
        print(f"Pokemon Archetypes: {', '.join(a.value.replace('_', ' ').title() for a in archetypes)}")
        
        # Show current moves
        print("\nCurrent Moves:")
        for i, move in enumerate(pokemon.moves, 1):
            damage_type = move['damage_class'] if move['causes_damage'] else 'Status'
            power_str = f"Power: {move['power']}" if move.get('power') else "Status"
            print(f"  {i}. {move['name']} ({move['type']}, {damage_type}) - {power_str}")
        
        print("\nAvailable Filters:")
        print("  1. Filter by Archetype")
        print("  2. Filter by Type")
        print("  3. Filter by Damage Class (Physical/Special/Status)")
        print("  4. Show All Moves")
        
        print("\nExample usage:")
        print("  filter_by_archetype = Archetype.PHYSICAL_ATTACKER")
        print("  moves = generator.get_filtered_moves_for_learning(pokemon, archetype_filter=filter_by_archetype)")
        print("  or")
        print("  moves = generator.get_filtered_moves_for_learning(pokemon, type_filter='Water')")
        print("  or")
        print("  moves = generator.get_filtered_moves_for_learning(pokemon, damage_class_filter='physical')")
        print("="*60 + "\n")
    
    # ========== PLAYER TEAM GENERATION ==========
    
    def generate_starter_choices(self) -> List[List[Pokemon]]:
        """
        Generate 3 sets of starter choices (each set has 3 Pokemon)
        Player picks 1 from each set to form their starting 3-Pokemon team
        
        Returns:
            List of 3 lists, each containing 3 Pokemon choices
        """
        starter_tsb_min = 280
        starter_tsb_max = 330
        
        all_choices = []
        global_used_species = set()  # Track species across ALL groups to prevent any duplicates
        
        for choice_set in range(3):
            choices = []
            
            attempts = 0
            while len(choices) < 3 and attempts < 50:
                attempts += 1
                
                # Generate a Pokemon within starter range
                target_tsb = random.randint(starter_tsb_min, starter_tsb_max)
                pokemon_data = self._select_pokemon_by_budget(target_tsb, tolerance=15)
                
                if pokemon_data and pokemon_data['id'] not in global_used_species:
                    global_used_species.add(pokemon_data['id'])
                    
                    # Calculate starter level based on growth curve
                    # All starters start at effective power level 5, but actual level varies
                    base_level = 5
                    exp_curve = pokemon_data.get('exp_curve', 'medium-fast')
                    scaled_level = ExperienceCurve.scale_level_for_curve(base_level, exp_curve)
                    
                    pokemon = self._create_pokemon_instance(pokemon_data, round_number=1, level=scaled_level)
                    choices.append(pokemon)
            
            all_choices.append(choices)
        
        return all_choices
    
    def generate_reward_options(self, current_team: List[Pokemon]) -> Dict:
        """
        Generate post-victory reward options
        
        Args:
            current_team: Player's current team
            
        Returns:
            Dictionary with reward options:
            {
                'new_pokemon': Pokemon instance (10-20% stronger than team average),
                'can_add': bool (team size < 6),
                'move_choices': List of available moves for learning
            }
        """
        # Calculate team average TSB
        if not current_team:
            avg_tsb = 300
        else:
            team_tsbs = [self.calculate_tsb(self._pokemon_to_data(p)) for p in current_team]
            avg_tsb = sum(team_tsbs) // len(team_tsbs)
        
        # New Pokemon should be 10-20% stronger
        growth_factor = random.uniform(1.10, 1.20)
        target_tsb = int(avg_tsb * growth_factor)
        
        # Generate the offered Pokemon
        pokemon_data = self._select_pokemon_by_budget(target_tsb, tolerance=20)
        
        if pokemon_data:
            # Calculate appropriate level (slightly higher than team average)
            if current_team:
                avg_level = sum(p.level for p in current_team) // len(current_team)
                new_level = avg_level + random.randint(1, 3)
            else:
                new_level = 5
            
            new_pokemon = self._create_pokemon_instance(pokemon_data, 
                                                       round_number=new_level // 3,
                                                       level=new_level)
        else:
            new_pokemon = None
        
        # Get interesting moves for learning - now using archetype system
        all_moves = self.move_repo.get_all()
        # Filter for good moves (either strong attacks or useful utility)
        good_moves = [m for m in all_moves if 
                     (m['causes_damage'] and m.get('power') is not None and m['power'] >= 70) or
                     (not m['causes_damage'] and any(keyword in m['name'].lower()
                      for keyword in ['protect', 'substitute', 'recover', 'setup',
                                     'will-o-wisp', 'thunder wave', 'toxic', 'stealth rock']))]
        
        move_choices = random.sample(good_moves, min(5, len(good_moves))) if good_moves else []
        
        return {
            'new_pokemon': new_pokemon,
            'can_add': len(current_team) < 6,
            'move_choices': move_choices
        }
    
    def _pokemon_to_data(self, pokemon: Pokemon) -> Dict:
        """Convert Pokemon instance back to data dict for TSB calculation"""
        return {
            'total_stats': pokemon.max_hp + pokemon.attack + 
                          pokemon.defense + pokemon.sp_attack +
                          pokemon.sp_defense + pokemon.speed
        }
    
    # ========== TEAM MANAGEMENT ==========
    
    def add_pokemon_to_team(self, team: List[Pokemon], new_pokemon: Pokemon) -> List[Pokemon]:
        """
        Add a Pokemon to the team (max 6)
        
        Args:
            team: Current team
            new_pokemon: Pokemon to add
            
        Returns:
            Updated team
        """
        if len(team) < 6:
            team.append(new_pokemon)
        return team
    
    def replace_pokemon_in_team(self, team: List[Pokemon], old_index: int, 
                               new_pokemon: Pokemon) -> List[Pokemon]:
        """
        Replace a Pokemon in the team
        
        Args:
            team: Current team
            old_index: Index of Pokemon to replace
            new_pokemon: Pokemon to add
            
        Returns:
            Updated team
        """
        if 0 <= old_index < len(team):
            team[old_index] = new_pokemon
        return team
    
    def teach_move_to_pokemon(self, pokemon: Pokemon, new_move: Dict, 
                             replace_index: int) -> Pokemon:
        """
        Teach a new move to a Pokemon, replacing an existing one
        
        Args:
            pokemon: Pokemon to teach
            new_move: Move data to teach
            replace_index: Index of move to replace (0-3)
            
        Returns:
            Updated Pokemon
        """
        if 0 <= replace_index < len(pokemon.moves):
            pokemon.moves[replace_index] = new_move
        return pokemon
    
    # ========== UTILITY METHODS ==========
    
    def get_team_summary(self, team: List[Pokemon]) -> Dict:
        """
        Get summary statistics for a team
        
        Args:
            team: List of Pokemon
            
        Returns:
            Dictionary with team stats
        """
        if not team:
            return {
                'size': 0,
                'avg_tsb': 0,
                'avg_level': 0,
                'total_tsb': 0,
                'types': []
            }
        
        tsbs = [self.calculate_tsb(self._pokemon_to_data(p)) for p in team]
        levels = [p.level for p in team]
        types = []
        
        for p in team:
            types.append(p.type1)
            if p.type2:
                types.append(p.type2)
        
        return {
            'size': len(team),
            'avg_tsb': sum(tsbs) // len(tsbs),
            'avg_level': sum(levels) // len(levels),
            'total_tsb': sum(tsbs),
            'min_tsb': min(tsbs),
            'max_tsb': max(tsbs),
            'types': list(set(types))
        }
    
    def display_team(self, team: List[Pokemon], title: str = "Team"):
        """
        Display team information
        
        Args:
            team: List of Pokemon
            title: Title to display
        """
        print(f"\n{'='*60}")
        print(f"{title}")
        print(f"{'='*60}")
        
        for i, pokemon in enumerate(team, 1):
            tsb = self.calculate_tsb(self._pokemon_to_data(pokemon))
            print(f"{i}. {pokemon.name} (Lv.{pokemon.level}) - TSB: {tsb}")
            print(f"   Type: {pokemon.type1}" + (f"/{pokemon.type2}" if pokemon.type2 else ""))
            print(f"   HP: {pokemon.current_hp}/{pokemon.max_hp}")
            print(f"   Moves: {', '.join(m['name'] for m in pokemon.moves)}")
            print()
        
        summary = self.get_team_summary(team)
        print(f"Team Average TSB: {summary['avg_tsb']}")
        print(f"Team Average Level: {summary['avg_level']}")
        print(f"{'='*60}\n")
    
    def _generate_pokemon(self, pokemon_data: Dict, level: int) -> Pokemon:
        """Generate a Pokemon with learnset-based moves (for starter generation)"""
        # Create Pokemon instance
        pokemon = Pokemon(
            pokemon_id=pokemon_data['id'],
            level=level,
            ivs={'hp': 31, 'attack': 31, 'defense': 31, 
                 'sp_attack': 31, 'sp_defense': 31, 'speed': 31},
            evs={'hp': 0, 'attack': 0, 'defense': 0,
                 'sp_attack': 0, 'sp_defense': 0, 'speed': 0}
        )
        
        # Get 4 moves from learnset
        learnset_moves = get_available_moves_for_level(
            pokemon_id=pokemon_data['id'],
            current_level=level,
            count=4
        )
        
        if learnset_moves:
            moves = [self.move_repo.get_by_id(move['id']) for move in learnset_moves]
        else:
            # Fallback: use archetype-based system
            moves = self._select_moves_for_pokemon(pokemon_data, round_number=1, num_moves=4)
        
        pokemon.moves = moves
        return pokemon
    
    def _get_pokemon_near_tsb(self, target_tsb: int, level: int, 
                             exclude_species: set) -> Pokemon:
        """Get a Pokemon near the target TSB for rewards"""
        candidates = [
            p for p in self.all_pokemon
            if abs(p['total_stats'] - target_tsb) <= 50
            and p['species_id'] not in exclude_species
        ]
        
        if not candidates:
            candidates = [p for p in self.all_pokemon 
                         if p['species_id'] not in exclude_species]
        
        pokemon_data = random.choice(candidates)
        return self._generate_pokemon(pokemon_data, level)


# ========== EXAMPLE USAGE ==========

def safe_print_name(name):
    """Safely print Pokemon names handling Unicode characters"""
    try:
        return name
    except:
        # Replace problematic Unicode characters
        return name.replace('♀', '(F)').replace('♂', '(M)').replace('é', 'e')

def example_usage():
    """Demonstrate the team generation system"""
    generator = TeamGenerator()
    
    print("="*60)
    print("ROGUELIKE POKÉMON TEAM GENERATION DEMO")
    print("="*60)
    
    # Example 1: Generate starter choices
    print("\n1. STARTER SELECTION (Choose 1 from each set)")
    print("-"*60)
    
    starter_choices = generator.generate_starter_choices()
    for set_num, choice_set in enumerate(starter_choices, 1):
        print(f"\nChoice Set {set_num}:")
        for i, pokemon in enumerate(choice_set, 1):
            tsb = generator.calculate_tsb(generator._pokemon_to_data(pokemon))
            archetypes = generator.get_pokemon_archetypes(pokemon)
            archetype_str = ', '.join(a.value.replace('_', ' ').title() for a in archetypes)
            name = safe_print_name(pokemon.name)
            
            # Show power cap for this Pokemon
            pokemon_data = generator.pokemon_repo.get_by_id(pokemon.id)
            max_power = generator._calculate_max_move_power(pokemon_data, pokemon.level)
            
            print(f"  {i}. {name} (TSB: {tsb}, Max Power: {max_power}) - {pokemon.type1}" + 
                  (f"/{pokemon.type2}" if pokemon.type2 else ""))
            print(f"      Archetypes: {archetype_str}")
            print(f"      Moves: {', '.join(safe_print_name(m['name']) for m in pokemon.moves)}")
    
    # Simulate player choosing first option from each set
    player_team = [starter_choices[0][0], starter_choices[1][0], starter_choices[2][0]]
    
    print("\n" + "="*60)
    print("PLAYER'S STARTING TEAM")
    print("="*60)
    generator.display_team(player_team, "Starting Team")
    
    # Example 2: Demonstrate archetype-based move generation
    print("\n2. ARCHETYPE-BASED MOVE GENERATION")
    print("-"*60)
    
    test_pokemon = player_team[0]
    pokemon_data = generator.pokemon_repo.get_by_id(test_pokemon.id)
    
    print(f"\nAnalyzing: {safe_print_name(test_pokemon.name)}")
    
    # Show stat percentages
    stats = generator._calculate_stat_percentages(pokemon_data)
    print("\nStat Distribution:")
    for stat_name, percentage in stats.items():
        print(f"  {stat_name.upper()}: {percentage:.1f}%")
    
    # Show archetypes
    archetypes = generator._determine_archetypes(pokemon_data)
    print(f"\nQualifying Archetypes:")
    for archetype in archetypes:
        print(f"  - {archetype.value.replace('_', ' ').title()}")
    
    # Show generated moves
    print(f"\nGenerated Moves:")
    for i, move in enumerate(test_pokemon.moves, 1):
        damage_info = f"Power: {move['power']}" if move.get('power') else "Status"
        print(f"  {i}. {safe_print_name(move['name'])} ({move['type']}, {move['category']}) - {damage_info}")
    
    for round_num in [1, 5, 10]:
        print(f"\n=== ROUND {round_num} ===")
        opponent_team = generator.generate_opponent_team(round_num, team_size=3)
        
        summary = generator.get_team_summary(opponent_team)
        print(f"TSB Range: {summary['min_tsb']} - {summary['max_tsb']}")
        print(f"Average TSB: {summary['avg_tsb']}")
        print(f"Average Level: {summary['avg_level']}")
        print(f"\nTeam Composition:")
        for i, pokemon in enumerate(opponent_team, 1):
            tsb = generator.calculate_tsb(generator._pokemon_to_data(pokemon))
            archetypes = generator.get_pokemon_archetypes(pokemon)
            archetype_str = ', '.join(a.value.replace('_', ' ').title() for a in archetypes[:2])
            name = safe_print_name(pokemon.name)
            print(f"  {i}. {name} (Lv.{pokemon.level}, TSB: {tsb})")
            print(f"      Archetypes: {archetype_str}")
            print(f"      Moves: {', '.join(safe_print_name(m['name']) for m in pokemon.moves)}")
    
    # Example 4: Post-battle rewards with move learning
    print("\n" + "="*60)
    print("4. MOVE LEARNING SYSTEM")
    print("="*60)
    
    # Demonstrate move filtering
    test_pokemon = player_team[0]
    print(f"\nLearning moves for: {safe_print_name(test_pokemon.name)}")
    
    # Filter by archetype
    archetypes = generator.get_pokemon_archetypes(test_pokemon)
    if archetypes:
        archetype_moves = generator.get_filtered_moves_for_learning(
            test_pokemon, 
            archetype_filter=archetypes[0]
        )
        print(f"\nMoves matching '{archetypes[0].value.replace('_', ' ').title()}' archetype: {len(archetype_moves)} moves")
        print("Sample moves:")
        for move in archetype_moves[:5]:
            damage_info = f"Power: {move['power']}" if move.get('power') else "Status"
            print(f"  - {move['name']} ({move['type']}, {move['category']}) - {damage_info}")
    
    # Filter by type
    # For demonstration, filter by "Water" type moves
    type_moves = generator.get_filtered_moves_for_learning(
        test_pokemon,
        type_filter="Water"
    )
    print(f"\nWater-type moves: {len(type_moves)} moves")
    print("Sample moves:")
    for move in type_moves[:5]:
        damage_info = f"Power: {move['power']}" if move.get('power') else "Status"
        print(f"  - {move['name']} ({move['category']}) - {damage_info}")
    
    # Filter by damage class
    physical_moves = generator.get_filtered_moves_for_learning(
        test_pokemon,
        damage_class_filter='physical'
    )
    print(f"\nPhysical moves: {len(physical_moves)} moves")
    
    # Combined filters
    combined_moves = generator.get_filtered_moves_for_learning(
        test_pokemon,
        type_filter="Fire",
        damage_class_filter='special'
    )
    print(f"\nSpecial Fire-type moves: {len(combined_moves)} moves")
    if combined_moves:
        print("Sample moves:")
        for move in combined_moves[:5]:
            print(f"  - {move['name']} (Power: {move.get('power', 'N/A')})")


    def generate_starter_choices(self) -> List[List[Pokemon]]:
        """
        Generate 3 sets of starter Pokemon choices for the player
        
        Returns:
            List of 3 lists, each containing 3 Pokemon options
        """
        starter_sets = []
        
        # Different TSB ranges for variety
        tsb_ranges = [
            (250, 320),  # Weak starters
            (300, 380),  # Medium starters
            (320, 400)   # Strong starters
        ]
        
        for tsb_min, tsb_max in tsb_ranges:
            choice_set = []
            used_species = set()
            
            # Generate 3 options in this TSB range
            attempts = 0
            while len(choice_set) < 3 and attempts < 100:
                attempts += 1
                
                # Get Pokemon in TSB range
                candidates = [
                    p for p in self.all_pokemon
                    if tsb_min <= p['total_stats'] <= tsb_max
                    and p['species_id'] not in used_species
                ]
                
                if not candidates:
                    break
                
                pokemon_data = random.choice(candidates)
                used_species.add(pokemon_data['species_id'])
                
                # Generate Pokemon at level 5-10
                level = random.randint(5, 10)
                pokemon = self._generate_pokemon(pokemon_data, level)
                choice_set.append(pokemon)
            
            starter_sets.append(choice_set)
        
        return starter_sets
    
    def generate_reward_options(self, player_team: List[Pokemon]) -> Dict:
        """
        Generate reward options after a battle victory
        
        Args:
            player_team: Current player team
            
        Returns:
            Dictionary with reward options
        """
        # Calculate average TSB of player team
        avg_tsb = sum(self.calculate_tsb(self._pokemon_to_data(p)) for p in player_team) / len(player_team)
        
        # Generate a new Pokemon option (slightly stronger than average)
        target_tsb = int(avg_tsb * 1.1)
        level = max(p.level for p in player_team)
        
        new_pokemon = self._get_pokemon_near_tsb(target_tsb, level, set(p.id for p in player_team))
        
        return {
            'new_pokemon': new_pokemon,
            'can_add': len(player_team) < 6
        }
    
    def get_team_summary(self, team: List[Pokemon]) -> Dict:
        """
        Get summary statistics for a team
        
        Args:
            team: List of Pokemon
            
        Returns:
            Dictionary with team statistics
        """
        if not team:
            return {'avg_level': 0, 'avg_tsb': 0, 'total': 0}
        
        total_level = sum(p.level for p in team)
        total_tsb = sum(self.calculate_tsb(self._pokemon_to_data(p)) for p in team)
        
        return {
            'avg_level': total_level // len(team),
            'avg_tsb': total_tsb // len(team),
            'total': len(team)
        }
    
    def _pokemon_to_data(self, pokemon: Pokemon) -> Dict:
        """Convert a Pokemon object back to data dictionary"""
        return self.pokemon_repo.get_by_id(pokemon.id)


if __name__ == "__main__":
    example_usage()
