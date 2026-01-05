"""
Pokemon Battle Simulator - Main Game Loop
Roguelike console-based Pokemon battle game
"""
import sys
import os
import random

# Add paths for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'models'))

from models.Pokemon import Pokemon
from models.team_generation import TeamGenerator, TeamComposition, Archetype
from models.cpu import CPUTrainer, AIFlag
from models.turn_logic import TurnManager, BattleAction, ActionType


class PokemonGame:
    """Main game class for the Pokemon Battle Simulator"""
    
    def __init__(self):
        self.generator = TeamGenerator()
        self.player_team = []
        self.current_round = 1
        self.wins = 0
        self.losses = 0
        self.game_over = False
    
    def start(self):
        """Start the game"""
        self.show_welcome_screen()
        self.starter_selection()
        
        # Main game loop
        while not self.game_over:
            self.show_round_info()
            
            # Generate opponent
            opponent_team = self.generate_opponent()
            
            # Battle
            result = self.battle(opponent_team)
            
            if result == 'win':
                self.wins += 1
                self.current_round += 1
                
                # Offer rewards
                if not self.offer_rewards():
                    break
            else:
                self.losses += 1
                self.game_over = True
                self.show_game_over()
                break
        
        print("\n" + "="*70)
        print("Thanks for playing!")
        print(f"Final Stats: {self.wins} Wins, {self.losses} Losses")
        print("="*70)
    
    def show_welcome_screen(self):
        """Display welcome screen"""
        print("\n" + "="*70)
        print(" "*15 + "POKEMON BATTLE SIMULATOR")
        print(" "*20 + "Roguelike Edition")
        print("="*70)
        print("\nWelcome, Trainer!")
        print("\nIn this roguelike adventure, you'll:")
        print("  - Choose a team of 3 starter Pokemon")
        print("  - Battle increasingly difficult opponents")
        print("  - Earn rewards and strengthen your team")
        print("  - Try to defeat as many trainers as possible!")
        print("\nThe challenge increases with each victory.")
        print("One loss and your run is over. Good luck!")
        print("="*70)
        input("\nPress Enter to begin...")
    
    def starter_selection(self):
        """Let player choose their starter team"""
        print("\n" + "="*70)
        print("STARTER SELECTION")
        print("="*70)
        print("\nChoose ONE Pokemon from each of the 3 groups below.")
        print("These will form your starting team.\n")
        
        starter_choices = self.generator.generate_starter_choices()
        
        for set_num, choice_set in enumerate(starter_choices, 1):
            print(f"\n{'='*70}")
            print(f"GROUP {set_num} - Choose ONE:")
            print("="*70)
            
            for i, pokemon in enumerate(choice_set, 1):
                tsb = self.generator.calculate_tsb(self.generator._pokemon_to_data(pokemon))
                pokemon_data = self.generator.pokemon_repo.get_by_id(pokemon.id)
                archetypes = self.generator._determine_archetypes(pokemon_data)
                archetype_str = ', '.join(a.value.replace('_', ' ').title() for a in archetypes[:2])
                
                print(f"\n{i}. {pokemon.name}")
                print(f"   Level: {pokemon.level} | TSB: {tsb} | Type: {self._get_type_name(pokemon_data['type1'])}", end="")
                if pokemon_data.get('type2'):
                    print(f"/{self._get_type_name(pokemon_data['type2'])}", end="")
                print(f"\n   Role: {archetype_str}")
                print(f"   HP: {pokemon.max_hp} | Atk: {pokemon.attack} | Def: {pokemon.defense}")
                print(f"   SpA: {pokemon.sp_attack} | SpD: {pokemon.sp_defense} | Spe: {pokemon.speed}")
                print(f"   Moves: {', '.join(m['name'] for m in pokemon.moves[:4])}")
            
            while True:
                try:
                    choice = input(f"\nSelect Pokemon (1-{len(choice_set)}): ").strip()
                    choice_idx = int(choice) - 1
                    if 0 <= choice_idx < len(choice_set):
                        chosen = choice_set[choice_idx]
                        self.player_team.append(chosen)
                        print(f"\nYou chose {chosen.name}!")
                        break
                    else:
                        print("Invalid choice. Try again.")
                except (ValueError, KeyboardInterrupt):
                    print("Invalid input. Try again.")
        
        print("\n" + "="*70)
        print("YOUR STARTING TEAM")
        print("="*70)
        self.display_team(self.player_team)
        input("\nPress Enter to begin your journey...")
    
    def show_round_info(self):
        """Display current round information"""
        print("\n" + "="*70)
        print(f"ROUND {self.current_round}")
        print("="*70)
        print(f"Wins: {self.wins} | Current Streak: {self.wins}")
        
        # Show team status
        print("\nYour Team:")
        for i, pokemon in enumerate(self.player_team, 1):
            status = "OK" if pokemon.current_hp > pokemon.max_hp * 0.5 else "Injured" if pokemon.current_hp > 0 else "Fainted"
            print(f"  {i}. {pokemon.name} (Lv.{pokemon.level}) - HP: {pokemon.current_hp}/{pokemon.max_hp} ({status})")
        
        input("\nPress Enter to face your opponent...")
    
    def generate_opponent(self):
        """Generate opponent team for current round"""
        print("\n" + "="*70)
        print("OPPONENT APPROACHING...")
        print("="*70)
        
        # Determine team size based on round
        team_size = min(3 + (self.current_round // 3), 6)
        
        # Generate opponent team
        opponent_team = self.generator.generate_opponent_team(
            round_number=self.current_round,
            team_size=team_size,
            composition=random.choice(list(TeamComposition))
        )
        
        # Display opponent team
        summary = self.generator.get_team_summary(opponent_team)
        print(f"\nOpponent has {len(opponent_team)} Pokemon!")
        print(f"Average Level: {summary['avg_level']} | Average TSB: {summary['avg_tsb']}")
        print("\nOpponent's Team:")
        for i, pokemon in enumerate(opponent_team, 1):
            pokemon_data = self.generator.pokemon_repo.get_by_id(pokemon.id)
            print(f"  {i}. {pokemon.name} (Lv.{pokemon.level}) - ???")
        
        return opponent_team
    
    def battle(self, opponent_team):
        """Execute a battle between player and opponent"""
        print("\n" + "="*70)
        print("BATTLE START!")
        print("="*70)
        
        # Initialize battle state
        player_active = self.player_team[0]
        opponent_active = opponent_team[0]
        
        # Create CPU AI
        difficulty = "easy" if self.current_round <= 2 else "normal" if self.current_round <= 5 else "hard"
        cpu = CPUTrainer(difficulty=difficulty)
        
        # Initialize battle state for TurnManager
        battle_state = {
            'player1_active': player_active,
            'player2_active': opponent_active,
            'player1_team': self.player_team,
            'player2_team': opponent_team,
            'weather': {'type': 'None', 'turns_remaining': 0},
            'field_effects': {},
            'turn_count': 0
        }
        
        turn_manager = TurnManager(battle_state)
        
        # Battle loop
        while True:
            battle_state['turn_count'] += 1
            turn_count = battle_state['turn_count']
            
            print(f"\n{'='*70}")
            print(f"Turn {turn_count}")
            print("="*70)
            
            # Show battle status with stat changes
            player_stats = player_active.get_stat_changes_display()
            player_stats_str = f" [{player_stats}]" if player_stats else ""
            print(f"\nYour {player_active.name} (Lv.{player_active.level}): {player_active.current_hp}/{player_active.max_hp} HP{player_stats_str}")
            
            opponent_stats = opponent_active.get_stat_changes_display()
            opponent_stats_str = f" [{opponent_stats}]" if opponent_stats else ""
            print(f"Opponent's {opponent_active.name} (Lv.{opponent_active.level}): {opponent_active.current_hp}/{opponent_active.max_hp} HP{opponent_stats_str}")
            
            # Player chooses action
            player_action = self.get_player_action(player_active, opponent_active)
            
            if player_action is None:
                print("\nYou forfeit the battle!")
                return 'loss'
            
            # CPU chooses move
            cpu_result = cpu.choose_move(opponent_active, player_active)
            cpu_move = cpu_result['move']
            
            print(f"\nOpponent's {opponent_active.name} will use {cpu_move['name']}!")
            
            # Create battle actions
            if isinstance(player_action, dict) and player_action.get('action') == 'switch':
                # Handle switch
                player_battle_action = BattleAction(player_active, ActionType.SWITCH, switch_target=self.player_team[0])
            else:
                # Handle move
                player_battle_action = BattleAction(player_active, ActionType.FIGHT, move=player_action, target=opponent_active)
            
            cpu_battle_action = BattleAction(opponent_active, ActionType.FIGHT, move=cpu_move, target=player_active)
            
            # Execute turn with full turn logic
            turn_result = turn_manager.execute_turn([player_battle_action, cpu_battle_action])
            
            # Display turn log
            for log_entry in turn_result['turn_log']:
                print(log_entry)
            
            # Update active Pokemon references after switches
            player_active = battle_state['player1_active']
            opponent_active = battle_state['player2_active']
            
            # Check for fainted Pokemon
            if opponent_active.current_hp <= 0:
                print(f"\nOpponent's {opponent_active.name} fainted!")
                battle_state['player2_team'].remove(opponent_active)
                
                if not battle_state['player2_team']:
                    print("\n" + "="*70)
                    print("VICTORY!")
                    print("="*70)
                    return 'win'
                
                # Switch to next opponent Pokemon
                opponent_active = battle_state['player2_team'][0]
                battle_state['player2_active'] = opponent_active
                print(f"\nOpponent sends out {opponent_active.name}!")
            
            if player_active.current_hp <= 0:
                print(f"\nYour {player_active.name} fainted!")
                player_active.fainted = True
                
                # Check if all Pokemon fainted
                alive_pokemon = [p for p in battle_state['player1_team'] if p.current_hp > 0]
                if not alive_pokemon:
                    print("\n" + "="*70)
                    print("DEFEAT!")
                    print("="*70)
                    return 'loss'
                
                # Player must switch to alive Pokemon
                player_active = self.force_switch()
                battle_state['player1_active'] = player_active
                print(f"\nYou send out {player_active.name}!")
            
            input("\nPress Enter to continue...")
    
    def get_player_action(self, player_pokemon, opponent_pokemon):
        """Get player's chosen action"""
        while True:
            print("\n" + "-"*70)
            print("What will you do?")
            print("-"*70)
            print("1. Fight")
            print("2. Switch Pokemon")
            print("3. Forfeit")
            
            try:
                choice = input("\nChoice (1-3): ").strip()
                
                if choice == '1':
                    # Choose move
                    return self.choose_move(player_pokemon)
                elif choice == '2':
                    # Switch Pokemon
                    return self.choose_switch()
                elif choice == '3':
                    return None
                else:
                    print("Invalid choice. Try again.")
            except (ValueError, KeyboardInterrupt):
                print("Invalid input. Try again.")
    
    def choose_move(self, pokemon):
        """Let player choose a move"""
        print("\n" + "-"*70)
        print("Choose a move:")
        print("-"*70)
        
        for i, move in enumerate(pokemon.moves, 1):
            power_str = f"Power: {move['power']}" if move.get('power') else "Status"
            print(f"{i}. {move['name']} - {move['type']} ({move['category']}) - {power_str}")
        
        while True:
            try:
                choice = input(f"\nSelect move (1-{len(pokemon.moves)}) or 'b' to go back: ").strip()
                
                if choice.lower() == 'b':
                    return None
                
                move_idx = int(choice) - 1
                if 0 <= move_idx < len(pokemon.moves):
                    return pokemon.moves[move_idx]
                else:
                    print("Invalid choice. Try again.")
            except (ValueError, KeyboardInterrupt):
                print("Invalid input. Try again.")
    
    def choose_switch(self):
        """Let player choose which Pokemon to switch to"""
        if len(self.player_team) <= 1:
            print("\nNo other Pokemon available!")
            return None
        
        print("\n" + "-"*70)
        print("Switch to which Pokemon?")
        print("-"*70)
        
        for i, pokemon in enumerate(self.player_team[1:], 1):
            print(f"{i}. {pokemon.name} - HP: {pokemon.current_hp}/{pokemon.max_hp}")
        
        while True:
            try:
                choice = input(f"\nSelect Pokemon (1-{len(self.player_team)-1}) or 'b' to go back: ").strip()
                
                if choice.lower() == 'b':
                    return None
                
                pokemon_idx = int(choice)
                if 1 <= pokemon_idx < len(self.player_team):
                    # Swap positions
                    self.player_team[0], self.player_team[pokemon_idx] = self.player_team[pokemon_idx], self.player_team[0]
                    return {'action': 'switch'}
                else:
                    print("Invalid choice. Try again.")
            except (ValueError, KeyboardInterrupt):
                print("Invalid input. Try again.")
    
    def force_switch(self):
        """Force player to switch after a faint"""
        # Get only alive Pokemon
        alive_pokemon = [p for p in self.player_team if p.current_hp > 0]
        
        if len(alive_pokemon) == 1:
            # Move the only alive Pokemon to front
            chosen = alive_pokemon[0]
            self.player_team.remove(chosen)
            self.player_team.insert(0, chosen)
            return chosen
        
        print("\n" + "-"*70)
        print("Choose your next Pokemon:")
        print("-"*70)
        
        for i, pokemon in enumerate(self.player_team, 1):
            if pokemon.current_hp > 0:
                print(f"{i}. {pokemon.name} - HP: {pokemon.current_hp}/{pokemon.max_hp}")
            else:
                print(f"{i}. {pokemon.name} - FAINTED")
        
        while True:
            try:
                choice = input(f"\nSelect Pokemon (1-{len(self.player_team)}): ").strip()
                pokemon_idx = int(choice) - 1
                
                if 0 <= pokemon_idx < len(self.player_team):
                    chosen = self.player_team[pokemon_idx]
                    
                    # Check if chosen Pokemon is alive
                    if chosen.current_hp <= 0:
                        print("That Pokemon has fainted! Choose another.")
                        continue
                    
                    # Move chosen Pokemon to front
                    self.player_team.remove(chosen)
                    self.player_team.insert(0, chosen)
                    return chosen
                else:
                    print("Invalid choice. Try again.")
            except (ValueError, KeyboardInterrupt):
                print("Invalid input. Try again.")
    
    def execute_simple_turn(self, player_pokemon, opponent_pokemon, player_move, cpu_move):
        """Execute a simplified turn (direct damage calculation)
        Returns the current active player Pokemon (may change after switch)"""
        
        # Check for switch
        if isinstance(player_move, dict) and player_move.get('action') == 'switch':
            print(f"\nYou switched to {self.player_team[0].name}!")
            # Opponent attacks the newly switched Pokemon
            self.execute_move(opponent_pokemon, self.player_team[0], cpu_move)
            return self.player_team[0]  # Return new active Pokemon
        
        # Determine order based on priority, then speed
        player_priority = player_move.get('priority', 0)
        cpu_priority = cpu_move.get('priority', 0)
        
        # First check priority
        if player_priority > cpu_priority:
            player_goes_first = True
        elif cpu_priority > player_priority:
            player_goes_first = False
        else:
            # Same priority, check speed
            player_goes_first = player_pokemon.speed >= opponent_pokemon.speed
        
        if player_goes_first:
            print(f"\n{player_pokemon.name} uses {player_move['name']}!")
            self.execute_move(player_pokemon, opponent_pokemon, player_move)
            
            if opponent_pokemon.current_hp > 0:
                print(f"\nOpponent's {opponent_pokemon.name} uses {cpu_move['name']}!")
                self.execute_move(opponent_pokemon, player_pokemon, cpu_move)
        else:
            print(f"\nOpponent's {opponent_pokemon.name} uses {cpu_move['name']}!")
            self.execute_move(opponent_pokemon, player_pokemon, cpu_move)
            
            if player_pokemon.current_hp > 0:
                print(f"\n{player_pokemon.name} uses {player_move['name']}!")
                self.execute_move(player_pokemon, opponent_pokemon, player_move)
        
        return player_pokemon  # Return unchanged player Pokemon
    
    def execute_move(self, attacker, defender, move):
        """Execute a move and calculate damage/effects"""
        # Handle status/healing moves
        if not move.get('causes_damage', False) or not move.get('power'):
            print(f"  {move['name']} was used!")
            self._apply_status_move(attacker, defender, move)
            return
        
        # Simplified damage calculation
        level = attacker.level
        power = move['power']
        
        if move['category'] == 'Physical':
            attack = attacker.attack
            defense = defender.defense
        else:
            attack = attacker.sp_attack
            defense = defender.sp_defense
        
        # Basic damage formula
        damage = ((2 * level / 5 + 2) * power * attack / defense / 50 + 2)
        
        # Random factor
        damage = int(damage * random.uniform(0.85, 1.0))
        
        # Type effectiveness (simplified)
        attacker_data = self.generator.pokemon_repo.get_by_id(attacker.id)
        defender_data = self.generator.pokemon_repo.get_by_id(defender.id)
        
        # STAB
        if move['type'] in [attacker_data.get('type1'), attacker_data.get('type2')]:
            damage = int(damage * 1.5)
        
        # Apply damage
        defender.current_hp = max(0, defender.current_hp - damage)
        
        print(f"  It dealt {damage} damage!")
        
        # Show effectiveness message (simplified)
        if damage > power * 1.5:
            print("  It's super effective!")
        elif damage < power * 0.75:
            print("  It's not very effective...")
        
        # Apply secondary effects (like paralysis from Nuzzle)
        self._apply_secondary_effects(attacker, defender, move, damage)
        
        # Apply secondary effects (like paralysis from Nuzzle)
        self._apply_secondary_effects(attacker, defender, move, damage)
    
    def _apply_status_move(self, user, target, move):
        """Apply effects of status moves like healing, stat changes, etc."""
        move_name = move['name'].lower()
        
        # Healing moves
        if move_name in ['synthesis', 'moonlight', 'morning sun']:
            heal_amount = user.max_hp // 2
            user.current_hp = min(user.max_hp, user.current_hp + heal_amount)
            print(f"  {user.name} restored {heal_amount} HP!")
        elif move_name in ['recover', 'roost', 'slack off', 'soft-boiled']:
            heal_amount = user.max_hp // 2
            user.current_hp = min(user.max_hp, user.current_hp + heal_amount)
            print(f"  {user.name} restored {heal_amount} HP!")
        elif move_name == 'rest':
            user.current_hp = user.max_hp
            user.status = 'sleep'
            user.sleep_turns = 2
            print(f"  {user.name} went to sleep and restored all HP!")
        
        # Stat-boosting moves
        elif move_name in ['swords dance', 'nasty plot']:
            # +2 to Attack or Sp. Attack
            stat = 'attack' if move_name == 'swords dance' else 'sp_attack'
            user.modify_stat_stage(stat, 2)
            stat_display = 'Attack' if stat == 'attack' else 'Special Attack'
            print(f"  {user.name}'s {stat_display} sharply rose!")
        elif move_name == 'dragon dance':
            # +1 Attack, +1 Speed
            user.modify_stat_stage('attack', 1)
            user.modify_stat_stage('speed', 1)
            print(f"  {user.name}'s Attack and Speed rose!")
        elif move_name == 'quiver dance':
            # +1 Sp. Attack, +1 Sp. Defense, +1 Speed
            user.modify_stat_stage('sp_attack', 1)
            user.modify_stat_stage('sp_defense', 1)
            user.modify_stat_stage('speed', 1)
            print(f"  {user.name}'s Special Attack, Special Defense, and Speed rose!")
        elif move_name == 'calm mind':
            # +1 Sp. Attack, +1 Sp. Defense
            user.modify_stat_stage('sp_attack', 1)
            user.modify_stat_stage('sp_defense', 1)
            print(f"  {user.name}'s Special Attack and Special Defense rose!")
        elif move_name == 'bulk up':
            # +1 Attack, +1 Defense
            user.modify_stat_stage('attack', 1)
            user.modify_stat_stage('defense', 1)
            print(f"  {user.name}'s Attack and Defense rose!")
        elif move_name == 'coil':
            # +1 Attack, +1 Defense, +1 Accuracy
            user.modify_stat_stage('attack', 1)
            user.modify_stat_stage('defense', 1)
            user.modify_stat_stage('accuracy', 1)
            print(f"  {user.name}'s Attack, Defense, and Accuracy rose!")
        elif move_name in ['agility', 'rock polish']:
            # +2 Speed
            user.modify_stat_stage('speed', 2)
            print(f"  {user.name}'s Speed sharply rose!")
        elif move_name in ['iron defense', 'acid armor']:
            # +2 Defense
            user.modify_stat_stage('defense', 2)
            print(f"  {user.name}'s Defense sharply rose!")
        elif move_name == 'amnesia':
            # +2 Sp. Defense
            user.modify_stat_stage('sp_defense', 2)
            print(f"  {user.name}'s Special Defense sharply rose!")
        elif move_name == 'shell smash':
            # -1 Defense, -1 Sp. Defense, +2 Attack, +2 Sp. Attack, +2 Speed
            user.modify_stat_stage('defense', -1)
            user.modify_stat_stage('sp_defense', -1)
            user.modify_stat_stage('attack', 2)
            user.modify_stat_stage('sp_attack', 2)
            user.modify_stat_stage('speed', 2)
            print(f"  {user.name}'s defenses fell, but offensive stats sharply rose!")
        
        # Status-inflicting moves
        elif move_name == 'thunder wave':
            if target.status is None or target.status == '':
                target.status = 'paralysis'
                print(f"  {target.name} was paralyzed!")
            else:
                print(f"  But it failed!")
        elif move_name == 'toxic':
            if target.status is None or target.status == '':
                target.status = 'badly poisoned'
                print(f"  {target.name} was badly poisoned!")
            else:
                print(f"  But it failed!")
        elif move_name in ['will-o-wisp', 'fire fang']:
            if target.status is None or target.status == '':
                target.status = 'burn'
                print(f"  {target.name} was burned!")
            else:
                print(f"  But it failed!")
        elif move_name in ['sleep powder', 'spore', 'hypnosis']:
            if target.status is None or target.status == '':
                target.status = 'sleep'
                target.sleep_turns = random.randint(1, 3)
                print(f"  {target.name} fell asleep!")
            else:
                print(f"  But it failed!")
        
        # Hazards and field effects
        elif 'spikes' in move_name or 'stealth rock' in move_name:
            print(f"  {move['name']} was set up!")
        elif 'screen' in move_name or 'veil' in move_name:
            print(f"  {move['name']} was set up!")
        else:
            print(f"  (Status effect applied)")
    
    def _apply_secondary_effects(self, attacker, defender, move, damage):
        """Apply secondary effects from damaging moves (like paralysis, flinch, etc.)"""
        move_name = move['name'].lower()
        
        # Moves with paralysis chance
        if move_name == 'nuzzle':
            if defender.status is None or defender.status == '':
                defender.status = 'paralysis'
                print(f"  {defender.name} was paralyzed!")
        elif move_name in ['thunder fang', 'thunder punch', 'thunderbolt', 'discharge']:
            if (defender.status is None or defender.status == '') and random.random() < 0.1:
                defender.status = 'paralysis'
                print(f"  {defender.name} was paralyzed!")
        
        # Moves with burn chance
        elif move_name in ['fire fang', 'fire punch', 'flamethrower', 'lava plume']:
            if (defender.status is None or defender.status == '') and random.random() < 0.1:
                defender.status = 'burn'
                print(f"  {defender.name} was burned!")
        
        # Moves with freeze chance
        elif move_name in ['ice fang', 'ice punch', 'ice beam', 'blizzard']:
            if (defender.status is None or defender.status == '') and random.random() < 0.1:
                defender.status = 'freeze'
                print(f"  {defender.name} was frozen solid!")
        
        # Moves with poison chance
        elif move_name in ['poison fang', 'poison jab', 'sludge bomb']:
            if (defender.status is None or defender.status == '') and random.random() < 0.3:
                defender.status = 'poison'
                print(f"  {defender.name} was poisoned!")
        
        # Flinch moves (high-priority moves)
        elif move_name in ['fake out', 'iron head']:
            if random.random() < 0.3:
                print(f"  {defender.name} flinched!")
    
    def offer_rewards(self):
        """Offer rewards after winning a battle"""
        print("\n" + "="*70)
        print("VICTORY REWARDS")
        print("="*70)
        
        # Level up team (ALL Pokemon that participated, including fainted ones)
        print("\nYour Pokemon gained experience!")
        # Match opponent level progression: they gain 2+(round//3) per round
        # So player should gain similar amounts to stay competitive
        # Note: current_round has already been incremented when this is called
        # Round 1 complete (current_round=2): gain 4 levels (5->9), etc.
        if self.wins == 1:  # Just completed first battle
            levels_gained = 4  # Start at 5, need to reach 9 for Round 2
        else:
            levels_gained = 2 + (self.wins - 1) // 3  # Match opponent scaling
        
        evolutions_available = []
        for pokemon in self.player_team:
            # All Pokemon gain levels, not just survivors
            level_info = pokemon.level_up(levels_gained)
            print(f"\n{pokemon.name} grew to level {level_info['new_level']}!")
            
            # Show stat gains
            gains = level_info['stat_gains']
            print(f"  HP +{gains['hp']}, Atk +{gains['attack']}, Def +{gains['defense']}")
            print(f"  SpA +{gains['sp_attack']}, SpD +{gains['sp_defense']}, Spe +{gains['speed']}")
            
            # Check for evolution
            can_evolve, evo_id = pokemon.can_evolve()
            if can_evolve:
                evolutions_available.append((pokemon, evo_id))
        
        # Handle evolutions
        if evolutions_available:
            print("\n" + "="*70)
            print("EVOLUTION TIME!")
            print("="*70)
            
            for pokemon, evo_id in evolutions_available:
                # Get evolution name
                evo_data = self.generator.pokemon_repo.get_by_id(evo_id)
                evo_name = evo_data['name'] if evo_data else "???"
                
                print(f"\n{pokemon.name} wants to evolve into {evo_name}!")
                choice = input("Allow evolution? (y/n): ").strip().lower()
                
                if choice == 'y':
                    evo_info = pokemon.evolve(evo_id)
                    print(f"\nCongratulations! {evo_info['old_name']} evolved into {evo_info['new_name']}!")
                    
                    # Show stat changes
                    changes = evo_info['stat_changes']
                    print(f"  HP +{changes['hp']}, Atk +{changes['attack']}, Def +{changes['defense']}")
                    print(f"  SpA +{changes['sp_attack']}, SpD +{changes['sp_defense']}, Spe +{changes['speed']}")
                else:
                    print(f"\n{pokemon.name} did not evolve.")
        
        # Heal team (including previously fainted Pokemon)
        for pokemon in self.player_team:
            pokemon.current_hp = pokemon.max_hp
            pokemon.fainted = False  # Revive fainted Pokemon
            pokemon.status = None  # Clear status conditions
        
        print("\n" + "="*70)
        print("Your team has been fully healed!")
        print("="*70)
        
        # Generate rewards
        rewards = self.generator.generate_reward_options(self.player_team)
        
        print("\nChoose your reward:")
        print("-"*70)
        
        reward_options = []
        
        # Option 1: New Pokemon
        if rewards['new_pokemon'] and rewards['can_add']:
            reward_options.append('new_pokemon')
            new_poke = rewards['new_pokemon']
            tsb = self.generator.calculate_tsb(self.generator._pokemon_to_data(new_poke))
            print(f"1. Add {new_poke.name} to your team (Lv.{new_poke.level}, TSB: {tsb})")
        
        # Option 2: Continue
        reward_options.append('continue')
        print(f"{len(reward_options)}. Continue to next round")
        
        # Option 3: Quit
        reward_options.append('quit')
        print(f"{len(reward_options)}. End run (save your record)")
        
        while True:
            try:
                choice = input(f"\nChoice (1-{len(reward_options)}): ").strip()
                choice_idx = int(choice) - 1
                
                if 0 <= choice_idx < len(reward_options):
                    selected = reward_options[choice_idx]
                    
                    if selected == 'new_pokemon':
                        self.player_team.append(rewards['new_pokemon'])
                        print(f"\n{rewards['new_pokemon'].name} joined your team!")
                        return True
                    elif selected == 'continue':
                        print("\nOnward to the next challenge!")
                        return True
                    elif selected == 'quit':
                        print("\nYou chose to end your run.")
                        self.game_over = True
                        return False
                else:
                    print("Invalid choice. Try again.")
            except (ValueError, KeyboardInterrupt):
                print("Invalid input. Try again.")
    
    def show_game_over(self):
        """Show game over screen"""
        print("\n" + "="*70)
        print(" "*25 + "GAME OVER")
        print("="*70)
        print(f"\nYou defeated {self.wins} trainer(s) before falling in battle.")
        print("\nYour final team:")
        self.display_team(self.player_team)
    
    def display_team(self, team):
        """Display team information"""
        for i, pokemon in enumerate(team, 1):
            status = "Fainted" if pokemon.current_hp <= 0 else f"{pokemon.current_hp}/{pokemon.max_hp} HP"
            print(f"  {i}. {pokemon.name} (Lv.{pokemon.level}) - {status}")
    
    def _get_type_name(self, type_id):
        """Convert type ID to name"""
        type_map = {
            1: 'Normal', 2: 'Fire', 3: 'Water', 4: 'Electric', 5: 'Grass',
            6: 'Ice', 7: 'Fighting', 8: 'Poison', 9: 'Ground', 10: 'Flying',
            11: 'Psychic', 12: 'Bug', 13: 'Rock', 14: 'Ghost', 15: 'Dragon',
            16: 'Dark', 17: 'Steel', 18: 'Fairy'
        }
        return type_map.get(type_id, 'Unknown')


def main():
    """Main entry point"""
    try:
        game = PokemonGame()
        game.start()
    except KeyboardInterrupt:
        print("\n\nGame interrupted. Thanks for playing!")
    except Exception as e:
        print(f"\n\nAn error occurred: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
