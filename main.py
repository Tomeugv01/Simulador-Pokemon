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
from models.experience import ExperienceCurve
from models.constants import get_type_name as _get_type_name_shared


class PokemonGame:
    """Main game class for the Pokemon Battle Simulator"""

    def __init__(self):
        self.generator = TeamGenerator()
        self.player_team = []
        self.current_round = 1
        self.wins = 0
        self.losses = 0
        self.game_over = False
        self.defeated_opponents = []  # Track defeated Pokemon for EXP calculation

    # *** PUBLIC ***

    def battle(self, opponent_team):
        """Execute a battle between player and opponent"""
        print("\n" + "="*70)
        print("BATTLE START!")
        print("="*70)
        
        # Track defeated opponents for EXP calculation
        defeated_opponents = []
        
        # Initialize battle state
        player_active = self.player_team[0]
        opponent_active = opponent_team[0]
        
        # Initialize turns_active for starting Pokemon
        if hasattr(player_active, 'turns_active'):
            player_active.turns_active = 0
        if hasattr(opponent_active, 'turns_active'):
            opponent_active.turns_active = 0
        
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
            
            # Show current HP with stat changes
            player_stats = player_active.get_stat_changes_display()
            player_stats_str = f" ({player_stats})" if player_stats else ""
            print(f"\n{player_active.name}: {player_active.current_hp}/{player_active.max_hp} HP{player_stats_str}")
            
            opponent_stats = opponent_active.get_stat_changes_display()
            opponent_stats_str = f" ({opponent_stats})" if opponent_stats else ""
            print(f"{opponent_active.name}: {opponent_active.current_hp}/{opponent_active.max_hp} HP{opponent_stats_str}")
            
            # Get player action
            player_choice = self.get_player_action(player_active, opponent_active)
            
            # Create BattleAction for player
            if player_choice.get('action') == 'switch':
                player_action = BattleAction(
                    pokemon=player_active,
                    action_type=ActionType.SWITCH,
                    target=player_choice['pokemon']
                )
            else:
                player_action = BattleAction(
                    pokemon=player_active,
                    action_type=ActionType.FIGHT,
                    move=player_choice,
                    target=opponent_active
                )
            
            # Get CPU action
            cpu_choice = cpu.choose_move(
                opponent_active,
                player_active,
                battle_state
            )
            cpu_move = cpu_choice['move']
            
            cpu_action = BattleAction(
                pokemon=opponent_active,
                action_type=ActionType.FIGHT,
                move=cpu_move,
                target=player_active
            )
            
            # Execute turn using TurnManager
            player_alive, opponent_alive = self.execute_turn(
                turn_manager,
                battle_state,
                player_action,
                cpu_action
            )
            
            # Update active Pokemon references from battle state
            player_active = battle_state['player1_active']
            opponent_active = battle_state['player2_active']
            
            # Check for faints and handle switches
            if not opponent_alive:
                print(f"\n{opponent_active.name} fainted!")
                defeated_opponents.append(opponent_active)
                
                # Remove from opponent team
                opponent_team = [p for p in opponent_team if p.current_hp > 0]
                
                if not opponent_team:
                    print("\nYou won the battle!")
                    return ('win', defeated_opponents)
                
                # Opponent switches
                opponent_active = opponent_team[0]
                battle_state['player2_active'] = opponent_active
                print(f"\nOpponent sends out {opponent_active.name}!")
            
            if not player_alive:
                print(f"\n{player_active.name} fainted!")
                
                # Get alive Pokemon
                alive_team = [p for p in self.player_team if p.current_hp > 0]
                
                if not alive_team:
                    print("\nYou lost the battle!")
                    self.show_game_over()
                    return ('loss', [])
                
                # Force player to switch
                player_active = self.force_switch(exclude=[player_active])
                battle_state['player1_active'] = player_active
            
            input("\nPress Enter to continue...")

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
                    # Get the Pokemon to switch to
                    switch_to = self.player_team[pokemon_idx]
                    # Swap positions
                    self.player_team[0], self.player_team[pokemon_idx] = self.player_team[pokemon_idx], self.player_team[0]
                    return {'action': 'switch', 'pokemon': switch_to}
                else:
                    print("Invalid choice. Try again.")
            except (ValueError, KeyboardInterrupt):
                print("Invalid input. Try again.")

    def display_team(self, team):
        """Display team information"""
        for i, pokemon in enumerate(team, 1):
            status = "Fainted" if pokemon.current_hp <= 0 else f"{pokemon.current_hp}/{pokemon.max_hp} HP"
            print(f"  {i}. {pokemon.name} (Lv.{pokemon.level}) - {status}")

    def execute_turn(self, turn_manager, battle_state, player_action, cpu_action):
        """Execute a turn using TurnManager (database-driven)
        Returns tuple: (player_still_active, opponent_still_active)"""
        
        # Handle player switch
        if player_action.action_type == ActionType.SWITCH:
            old_pokemon = battle_state['player1_active']
            new_pokemon = player_action.target
            print(f"\nYou switched to {new_pokemon.name}!")
            # Reset turns_active for incoming Pokemon
            if hasattr(new_pokemon, 'turns_active'):
                new_pokemon.turns_active = 0
            battle_state['player1_active'] = new_pokemon
            # Update player_team order
            self.player_team.remove(new_pokemon)
            self.player_team.insert(0, new_pokemon)
            return (new_pokemon.current_hp > 0, battle_state['player2_active'].current_hp > 0)
        
        # Execute turn through TurnManager (handles all move logic via database)
        turn_result = turn_manager.execute_turn([player_action, cpu_action])
        
        # Display turn results from turn log
        for message in turn_result['turn_log']:
            # Skip empty messages
            if message.strip():
                print(f"  {message}")
        
        player_alive = battle_state['player1_active'].current_hp > 0
        opponent_alive = battle_state['player2_active'].current_hp > 0
        
        return (player_alive, opponent_alive)

    def force_switch(self, exclude=None):
        """Force player to switch after a faint or forced switch move
        
        Args:
            exclude: List of Pokemon that cannot be switched to (e.g., the one switching out)
        """
        exclude = exclude or []
        # Get only alive Pokemon that aren't excluded
        alive_pokemon = [p for p in self.player_team if p.current_hp > 0 and p not in exclude]
        
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
            if pokemon.current_hp > 0 and pokemon not in exclude:
                print(f"{i}. {pokemon.name} - HP: {pokemon.current_hp}/{pokemon.max_hp}")
            elif pokemon in exclude:
                print(f"{i}. {pokemon.name} - (Can't switch to this Pokemon)")
            else:
                print(f"{i}. {pokemon.name} - FAINTED")
        
        while True:
            try:
                choice = input(f"\nSelect Pokemon (1-{len(self.player_team)}): ").strip()
                pokemon_idx = int(choice) - 1
                
                if 0 <= pokemon_idx < len(self.player_team):
                    chosen = self.player_team[pokemon_idx]
                    
                    if chosen in exclude:
                        print("You can't switch to that Pokemon right now!")
                        continue
                    
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

    def generate_opponent(self):
        """Generate opponent team for current round"""
        print("\n" + "="*70)
        print("OPPONENT APPROACHING...")
        print("="*70)
        
        # Determine team size based on round
        team_size = min(3 + (self.current_round // 3), 6)
        
        # Calculate player average level
        total_levels = sum(p.level for p in self.player_team)
        avg_level = max(5, total_levels // max(1, len(self.player_team)))
        
        # Generate opponent team
        opponent_team = self.generator.generate_opponent_team(
            round_number=self.current_round,
            team_size=team_size,
            composition=random.choice(list(TeamComposition)),
            player_average_level=avg_level
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
                    move = self.choose_move(player_pokemon)
                    if move is not None:
                        return move
                    # If move is None (pressed 'b'), loop back to main menu
                elif choice == '2':
                    # Switch Pokemon
                    switch_result = self.choose_switch()
                    if switch_result is not None:
                        return switch_result
                    # If switch_result is None (pressed 'b'), loop back to main menu
                elif choice == '3':
                    return None
                else:
                    print("Invalid choice. Try again.")
            except (ValueError, KeyboardInterrupt):
                print("Invalid input. Try again.")

    def offer_rewards(self, defeated_opponents):
        """Offer rewards after winning a battle"""
        print("\n" + "="*70)
        print("VICTORY REWARDS")
        print("="*70)
        
        # Award EXP to all Pokemon (including fainted ones)
        print("\nYour Pokemon gained experience!")
        
        evolutions_available = []
        for pokemon in self.player_team:
            # Calculate total EXP from all defeated opponents
            total_exp = 0
            for defeated in defeated_opponents:
                exp_gain = ExperienceCurve.calculate_exp_gain(
                    defeated_pokemon=defeated,
                    winner_level=pokemon.level,
                    is_wild=False,
                    is_trainer=True,
                    participated=True
                )
                total_exp += exp_gain
            
            # Award EXP (this handles automatic level-ups)
            exp_result = pokemon.gain_exp(total_exp)
            
            if exp_result['leveled_up']:
                levels_gained = exp_result['new_level'] - exp_result['old_level']
                print(f"\n{pokemon.name} gained {total_exp:,} EXP!")
                print(f"{pokemon.name} grew to level {exp_result['new_level']}!")
                
                # Show stat gains
                gains = exp_result['stat_gains']
                print(f"  HP +{gains['hp']}, Atk +{gains['attack']}, Def +{gains['defense']}")
                print(f"  SpA +{gains['sp_attack']}, SpD +{gains['sp_defense']}, Spe +{gains['speed']}")
                
                # Check for new moves learned at each level
                for level in range(exp_result['old_level'] + 1, exp_result['new_level'] + 1):
                    new_moves = pokemon.check_moves_learned_at_level(level)
                    
                    for new_move in new_moves:
                        # Check if Pokemon already knows this move
                        already_knows = any(m.get('id') == new_move['id'] for m in pokemon.moves)
                        if already_knows:
                            continue  # Skip moves already known
                        
                        print(f"\n{pokemon.name} wants to learn {new_move['name']}!")
                        
                        # If already has 4 moves, prompt for replacement
                        if len(pokemon.moves) >= 4:
                            print(f"\nBut {pokemon.name} already knows 4 moves!")
                            print(f"Current moves:")
                            for i, move in enumerate(pokemon.moves):
                                move_info = f"{move['name']} (PP: {move.get('pp', '?')}/{move.get('pp', '?')})"
                                print(f"  {i+1}. {move_info}")
                            
                            while True:
                                choice = input(f"\nReplace a move with {new_move['name']}? (1-4 to replace, 0 to skip): ").strip()
                                
                                if choice == '0':
                                    print(f"{pokemon.name} did not learn {new_move['name']}.")
                                    break
                                elif choice in ['1', '2', '3', '4']:
                                    replace_idx = int(choice) - 1
                                    result = pokemon.learn_move(new_move['id'], replace_index=replace_idx)
                                    
                                    if result['success']:
                                        old_move_name = result['replaced_move']['name']
                                        print(f"\n{pokemon.name} forgot {old_move_name}...")
                                        print(f"And learned {new_move['name']}!")
                                    break
                                else:
                                    print("Invalid choice. Please enter 0-4.")
                        else:
                            # Has less than 4 moves, learn it automatically
                            result = pokemon.learn_move(new_move['id'])
                            if result['success']:
                                print(f"{pokemon.name} learned {new_move['name']}!")
            else:
                print(f"\n{pokemon.name} gained {total_exp:,} EXP (Level {pokemon.level})")
            
            # Check for evolution
            can_evolve, evo_ids = pokemon.can_evolve()
            if can_evolve:
                evolutions_available.append((pokemon, evo_ids))
        
        # Handle evolutions
        if evolutions_available:
            print("\n" + "="*70)
            print("EVOLUTION TIME!")
            print("="*70)
            
            for pokemon, evo_ids in evolutions_available:
                # Handle multiple evolution paths (e.g., Eevee)
                import random
                
                # If multiple evolutions, randomly choose one (equal odds)
                if len(evo_ids) > 1:
                    # Get names of all possible evolutions
                    evo_options = []
                    for evo_id in evo_ids:
                        evo_data = self.generator.pokemon_repo.get_by_id(evo_id)
                        if evo_data:
                            evo_options.append((evo_id, evo_data['name']))
                    
                    if evo_options:
                        # Randomly select one with equal probability
                        chosen_evo_id, chosen_evo_name = random.choice(evo_options)
                        print(f"\n{pokemon.name} wants to evolve!")
                        print(f"Possible evolutions: {', '.join([name for _, name in evo_options])}")
                        print(f"Evolution selected: {chosen_evo_name}")
                        evo_id = chosen_evo_id
                        evo_name = chosen_evo_name
                    else:
                        continue
                else:
                    # Single evolution path
                    evo_id = evo_ids[0]
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
        
        # Option 2: Teach a move
        reward_options.append('learn_move')
        print(f"{len(reward_options)}. Teach a new move to one of your Pokemon")
        
        # Option 3: Continue
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
                    elif selected == 'learn_move':
                        self.teach_move_to_team()
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
    # region Display

    def show_game_over(self):
        """Show game over screen"""
        print("\n" + "="*70)
        print(" "*25 + "GAME OVER")
        print("="*70)
        print(f"\nYou defeated {self.wins} trainer(s) before falling in battle.")
        print("\nYour final team:")
        self.display_team(self.player_team)

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

    # endregion Display

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
            result_tuple = self.battle(opponent_team)
            result = result_tuple[0]
            defeated_opponents = result_tuple[1] if len(result_tuple) > 1 else []
            
            if result == 'win':
                self.wins += 1
                self.current_round += 1
                
                # Offer rewards (this will award EXP)
                if not self.offer_rewards(defeated_opponents):
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

    def teach_move_to_team(self):
        """Allow player to teach a new move to one of their Pokemon"""
        print("\n" + "="*70)
        print("MOVE TUTOR")
        print("="*70)
        print("\nSelect a Pokemon to teach a new move:")
        
        # Show team
        for i, pokemon in enumerate(self.player_team, 1):
            print(f"{i}. {pokemon.name} (Lv.{pokemon.level})")
        
        print(f"{len(self.player_team) + 1}. Cancel")
        
        while True:
            try:
                choice = input(f"\nChoice (1-{len(self.player_team) + 1}): ").strip()
                choice_idx = int(choice) - 1
                
                if choice_idx == len(self.player_team):
                    print("Cancelled move learning.")
                    return
                
                if 0 <= choice_idx < len(self.player_team):
                    selected_pokemon = self.player_team[choice_idx]
                    break
                else:
                    print("Invalid choice. Try again.")
            except (ValueError, KeyboardInterrupt):
                print("Invalid input. Try again.")
        
        # Get filtered moves for this Pokemon
        print(f"\n{selected_pokemon.name}'s current moves:")
        for i, move in enumerate(selected_pokemon.moves, 1):
            print(f"  {i}. {move.name} ({move.type}, {move.category}) - Power: {move.power or 'N/A'}")
        
        # Get available moves
        available_moves = self.generator.get_filtered_moves_for_learning(
            selected_pokemon,
            respect_power_cap=True
        )
        
        if not available_moves:
            print(f"\nNo new moves available for {selected_pokemon.name} at this level!")
            return
        
        print(f"\nAvailable moves for {selected_pokemon.name}:")
        print("-"*70)
        
        # Show up to 10 moves
        display_moves = available_moves[:10]
        for i, move in enumerate(display_moves, 1):
            power_str = f"Power: {move['power']}" if move['power'] else "Status"
            print(f"{i}. {move['name']} ({move['type']}, {move['category']}) - {power_str}")
        
        print(f"{len(display_moves) + 1}. Cancel")
        
        while True:
            try:
                choice = input(f"\nSelect move to learn (1-{len(display_moves) + 1}): ").strip()
                move_idx = int(choice) - 1
                
                if move_idx == len(display_moves):
                    print("Cancelled move learning.")
                    return
                
                if 0 <= move_idx < len(display_moves):
                    new_move = display_moves[move_idx]
                    break
                else:
                    print("Invalid choice. Try again.")
            except (ValueError, KeyboardInterrupt):
                print("Invalid input. Try again.")
        
        # If Pokemon has 4 moves, ask which to replace
        if len(selected_pokemon.moves) >= 4:
            print(f"\n{selected_pokemon.name} already knows 4 moves. Which move should be forgotten?")
            for i, move in enumerate(selected_pokemon.moves, 1):
                print(f"{i}. {move.name}")
            print(f"{len(selected_pokemon.moves) + 1}. Cancel")
            
            while True:
                try:
                    choice = input(f"\nReplace which move? (1-{len(selected_pokemon.moves) + 1}): ").strip()
                    replace_idx = int(choice) - 1
                    
                    if replace_idx == len(selected_pokemon.moves):
                        print(f"{selected_pokemon.name} did not learn {new_move['name']}.")
                        return
                    
                    if 0 <= replace_idx < len(selected_pokemon.moves):
                        break
                    else:
                        print("Invalid choice. Try again.")
                except (ValueError, KeyboardInterrupt):
                    print("Invalid input. Try again.")
        else:
            replace_idx = len(selected_pokemon.moves)  # Add to end
        
        # Teach the move
        self.generator.teach_move_to_pokemon(selected_pokemon, new_move, replace_idx)
        print(f"\n{selected_pokemon.name} learned {new_move['name']}!")

    # *** PRIVATE ***

    def _get_type_name(self, type_id):
        """Convert type ID to name"""
        return _get_type_name_shared(type_id)


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
