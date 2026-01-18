#!/usr/bin/env python3
"""
Comprehensive Move System Testing Suite
Tests all 425 move effects to identify working, broken, and bugged moves
"""

import sys
import os
from typing import Dict, List, Set, Tuple
from collections import defaultdict
import traceback

# Add paths for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'models'))

from models.Pokemon import Pokemon
from models.team_generation import TeamGenerator
from models.turn_logic import TurnManager, BattleAction, ActionType
from src.database import DatabaseManager


class MoveSystemTester:
    """Automated testing system for move effects"""
    
    def __init__(self):
        self.generator = TeamGenerator()
        self.db_manager = DatabaseManager()
        self.conn = self.db_manager.get_connection()
        
        # Test results tracking
        self.test_results = {
            'passed': [],
            'failed': [],
            'errors': [],
            'warnings': []
        }
        
        self.moves_tested = set()
        self.effects_tested = defaultdict(int)
        
    def run_all_tests(self):
        """Run complete test suite"""
        print("="*80)
        print(" "*20 + "MOVE SYSTEM TESTING SUITE")
        print("="*80)
        print("\nInitializing tests...")
        
        # Get all moves from database
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT m.id, m.name, m.category, m.power, m.type,
                   GROUP_CONCAT(me.effect_type || ':' || me.name) as effects
            FROM moves m
            LEFT JOIN move_effect_instances mei ON m.id = mei.move_id
            LEFT JOIN move_effects me ON mei.effect_id = me.id
            GROUP BY m.id
            ORDER BY m.category, m.name
        """)
        all_moves = cursor.fetchall()
        
        print(f"Found {len(all_moves)} moves in database")
        print(f"Testing move effects across multiple scenarios...\n")
        
        # Test by category
        self.test_damaging_moves(all_moves)
        self.test_status_moves(all_moves)
        self.test_stat_change_moves(all_moves)
        self.test_healing_moves(all_moves)
        self.test_complex_moves(all_moves)
        self.test_priority_moves(all_moves)
        self.test_weather_moves(all_moves)
        self.test_field_effect_moves(all_moves)
        self.test_recoil_moves(all_moves)
        self.test_secondary_effects(all_moves)
        
        # Generate report
        self.generate_report()
        
    def test_damaging_moves(self, all_moves):
        """Test physical and special damaging moves"""
        print("\n" + "="*80)
        print("TEST CATEGORY: DAMAGING MOVES (Physical & Special)")
        print("="*80)
        
        # Filter damaging moves
        damaging_moves = [m for m in all_moves if m[2] in ('Physical', 'Special') and m[3]]
        
        print(f"Testing {len(damaging_moves)} damaging moves...")
        
        for move_id, move_name, category, power, move_type, effects in damaging_moves:  # Test ALL
            try:
                result = self._test_single_move(move_id, move_name, category)
                if result['success']:
                    self.test_results['passed'].append({
                        'move': move_name,
                        'category': 'Damaging',
                        'details': f"Dealt {result.get('damage', 0)} damage"
                    })
                else:
                    self.test_results['failed'].append({
                        'move': move_name,
                        'category': 'Damaging',
                        'reason': result.get('reason', 'Unknown failure')
                    })
                    
                self.moves_tested.add(move_name)
                
            except Exception as e:
                self.test_results['errors'].append({
                    'move': move_name,
                    'category': 'Damaging',
                    'error': str(e)
                })
        
        print(f"[OK] Completed damaging moves test")
        
    def test_status_moves(self, all_moves):
        """Test status-inflicting moves"""
        print("\n" + "="*80)
        print("TEST CATEGORY: STATUS MOVES (Paralysis, Burn, Freeze, Poison, Sleep)")
        print("="*80)
        
        status_move_names = [
            'Thunder Wave', 'Toxic', 'Will-O-Wisp', 'Spore', 'Sleep Powder',
            'Hypnosis', 'Stun Spore', 'Poison Powder', 'Glare'
        ]
        
        for move_name in status_move_names:
            try:
                # Get move from database
                cursor = self.conn.cursor()
                cursor.execute("SELECT id, name, category FROM moves WHERE name = ?", (move_name,))
                move_data = cursor.fetchone()
                
                if not move_data:
                    continue
                    
                move_id, name, category = move_data
                result = self._test_status_move(move_id, name)
                
                if result['success']:
                    self.test_results['passed'].append({
                        'move': name,
                        'category': 'Status',
                        'details': f"Applied {result.get('status', 'unknown')} status"
                    })
                else:
                    self.test_results['failed'].append({
                        'move': name,
                        'category': 'Status',
                        'reason': result.get('reason', 'Unknown failure')
                    })
                    
                self.moves_tested.add(name)
                
            except Exception as e:
                self.test_results['errors'].append({
                    'move': move_name,
                    'category': 'Status',
                    'error': str(e)
                })
        
        print(f"[OK] Completed status moves test")
        
    def test_stat_change_moves(self, all_moves):
        """Test stat-changing moves"""
        print("\n" + "="*80)
        print("TEST CATEGORY: STAT CHANGE MOVES (Swords Dance, Dragon Dance, etc.)")
        print("="*80)
        
        stat_move_names = [
            'Swords Dance', 'Dragon Dance', 'Nasty Plot', 'Calm Mind',
            'Bulk Up', 'Coil', 'Quiver Dance', 'Agility', 'Rock Polish',
            'Iron Defense', 'Amnesia', 'Shell Smash', 'Growth'
        ]
        
        for move_name in stat_move_names:
            try:
                cursor = self.conn.cursor()
                cursor.execute("SELECT id, name, category FROM moves WHERE name = ?", (move_name,))
                move_data = cursor.fetchone()
                
                if not move_data:
                    continue
                    
                move_id, name, category = move_data
                result = self._test_stat_change_move(move_id, name)
                
                if result['success']:
                    self.test_results['passed'].append({
                        'move': name,
                        'category': 'Stat Change',
                        'details': f"Modified stats: {result.get('stat_changes', 'unknown')}"
                    })
                else:
                    self.test_results['failed'].append({
                        'move': name,
                        'category': 'Stat Change',
                        'reason': result.get('reason', 'Unknown failure')
                    })
                    
                self.moves_tested.add(name)
                
            except Exception as e:
                self.test_results['errors'].append({
                    'move': move_name,
                    'category': 'Stat Change',
                    'error': str(e)
                })
        
        print(f"[OK] Completed stat change moves test")
        
    def test_healing_moves(self, all_moves):
        """Test healing moves"""
        print("\n" + "="*80)
        print("TEST CATEGORY: HEALING MOVES (Recover, Synthesis, etc.)")
        print("="*80)
        
        healing_move_names = [
            'Recover', 'Roost', 'Rest', 'Synthesis', 'Moonlight',
            'Morning Sun', 'Slack Off', 'Soft-Boiled', 'Wish'
        ]
        
        for move_name in healing_move_names:
            try:
                cursor = self.conn.cursor()
                cursor.execute("SELECT id, name, category FROM moves WHERE name = ?", (move_name,))
                move_data = cursor.fetchone()
                
                if not move_data:
                    continue
                    
                move_id, name, category = move_data
                result = self._test_healing_move(move_id, name)
                
                if result['success']:
                    self.test_results['passed'].append({
                        'move': name,
                        'category': 'Healing',
                        'details': f"Healed {result.get('hp_healed', 0)} HP"
                    })
                else:
                    self.test_results['failed'].append({
                        'move': name,
                        'category': 'Healing',
                        'reason': result.get('reason', 'Unknown failure')
                    })
                    
                self.moves_tested.add(name)
                
            except Exception as e:
                self.test_results['errors'].append({
                    'move': move_name,
                    'category': 'Healing',
                    'error': str(e)
                })
        
        print(f"[OK] Completed healing moves test")
        
    def test_complex_moves(self, all_moves):
        """Test complex moves (charge, invulnerability, counters, etc.)"""
        print("\n" + "="*80)
        print("TEST CATEGORY: COMPLEX MOVES (Charge turns, Invulnerability, Counters)")
        print("="*80)
        
        complex_move_names = [
            'Solar Beam', 'Dig', 'Fly', 'Dive', 'Bounce', 'Sky Attack',
            'Counter', 'Mirror Coat', 'Metal Burst', 'Bide',
            'Super Fang', 'Psywave', 'Endeavor', 'Final Gambit'
        ]
        
        for move_name in complex_move_names:
            try:
                cursor = self.conn.cursor()
                cursor.execute("SELECT id, name, category FROM moves WHERE name = ?", (move_name,))
                move_data = cursor.fetchone()
                
                if not move_data:
                    self.test_results['warnings'].append({
                        'move': move_name,
                        'category': 'Complex',
                        'message': 'Move not found in database'
                    })
                    continue
                    
                move_id, name, category = move_data
                result = self._test_complex_move(move_id, name)
                
                if result['success']:
                    self.test_results['passed'].append({
                        'move': name,
                        'category': 'Complex',
                        'details': result.get('details', 'Executed successfully')
                    })
                else:
                    self.test_results['failed'].append({
                        'move': name,
                        'category': 'Complex',
                        'reason': result.get('reason', 'Unknown failure')
                    })
                    
                self.moves_tested.add(name)
                
            except Exception as e:
                self.test_results['errors'].append({
                    'move': move_name,
                    'category': 'Complex',
                    'error': str(e),
                    'traceback': traceback.format_exc()
                })
        
        print(f"[OK] Completed complex moves test")
        
    def test_priority_moves(self, all_moves):
        """Test priority moves"""
        print("\n" + "="*80)
        print("TEST CATEGORY: PRIORITY MOVES (Quick Attack, Extreme Speed, etc.)")
        print("="*80)
        
        priority_move_names = [
            'Quick Attack', 'Extreme Speed', 'Aqua Jet', 'Mach Punch',
            'Ice Shard', 'Shadow Sneak', 'Bullet Punch', 'Sucker Punch',
            'Fake Out', 'First Impression'
        ]
        
        for move_name in priority_move_names:
            try:
                cursor = self.conn.cursor()
                cursor.execute("SELECT id, name, category, priority FROM moves WHERE name = ?", (move_name,))
                move_data = cursor.fetchone()
                
                if not move_data:
                    continue
                    
                move_id, name, category, priority = move_data
                result = self._test_single_move(move_id, name, category)
                
                if result['success']:
                    self.test_results['passed'].append({
                        'move': name,
                        'category': 'Priority',
                        'details': f"Priority {priority}, dealt {result.get('damage', 0)} damage"
                    })
                    self.moves_tested.add(name)
                    
            except Exception as e:
                self.test_results['errors'].append({
                    'move': move_name,
                    'category': 'Priority',
                    'error': str(e)
                })
        
        print(f"[OK] Completed priority moves test")
        
    def test_weather_moves(self, all_moves):
        """Test weather-setting moves"""
        print("\n" + "="*80)
        print("TEST CATEGORY: WEATHER MOVES (Rain Dance, Sunny Day, etc.)")
        print("="*80)
        
        weather_move_names = ['Rain Dance', 'Sunny Day', 'Sandstorm', 'Hail']
        
        for move_name in weather_move_names:
            try:
                cursor = self.conn.cursor()
                cursor.execute("SELECT id, name, category FROM moves WHERE name = ?", (move_name,))
                move_data = cursor.fetchone()
                
                if not move_data:
                    continue
                    
                move_id, name, category = move_data
                result = self._test_weather_move(move_id, name)
                
                if result['success']:
                    self.test_results['passed'].append({
                        'move': name,
                        'category': 'Weather',
                        'details': f"Set weather: {result.get('weather', 'unknown')}"
                    })
                    self.moves_tested.add(name)
                    
            except Exception as e:
                self.test_results['errors'].append({
                    'move': move_name,
                    'category': 'Weather',
                    'error': str(e)
                })
        
        print(f"[OK] Completed weather moves test")
        
    def test_field_effect_moves(self, all_moves):
        """Test field effect moves (screens, hazards)"""
        print("\n" + "="*80)
        print("TEST CATEGORY: FIELD EFFECTS (Reflect, Light Screen, Stealth Rock, etc.)")
        print("="*80)
        
        field_move_names = [
            'Reflect', 'Light Screen', 'Stealth Rock', 'Spikes',
            'Toxic Spikes', 'Sticky Web'
        ]
        
        for move_name in field_move_names:
            try:
                cursor = self.conn.cursor()
                cursor.execute("SELECT id, name, category FROM moves WHERE name = ?", (move_name,))
                move_data = cursor.fetchone()
                
                if not move_data:
                    self.test_results['warnings'].append({
                        'move': move_name,
                        'category': 'Field Effect',
                        'message': 'Move not found in database'
                    })
                    continue
                    
                move_id, name, category = move_data
                result = self._test_field_effect_move(move_id, name)
                
                if result['success']:
                    self.test_results['passed'].append({
                        'move': name,
                        'category': 'Field Effect',
                        'details': result.get('details', 'Set field effect')
                    })
                    self.moves_tested.add(name)
                else:
                    self.test_results['failed'].append({
                        'move': name,
                        'category': 'Field Effect',
                        'reason': result.get('reason', 'Unknown failure')
                    })
                    
            except Exception as e:
                self.test_results['errors'].append({
                    'move': move_name,
                    'category': 'Field Effect',
                    'error': str(e)
                })
        
        print(f"[OK] Completed field effect moves test")
        
    def test_recoil_moves(self, all_moves):
        """Test recoil moves"""
        print("\n" + "="*80)
        print("TEST CATEGORY: RECOIL MOVES (Take Down, Flare Blitz, etc.)")
        print("="*80)
        
        recoil_move_names = [
            'Take Down', 'Double-Edge', 'Flare Blitz', 'Brave Bird',
            'Wood Hammer', 'Head Smash', 'Wild Charge'
        ]
        
        for move_name in recoil_move_names:
            try:
                cursor = self.conn.cursor()
                cursor.execute("SELECT id, name, category FROM moves WHERE name = ?", (move_name,))
                move_data = cursor.fetchone()
                
                if not move_data:
                    continue
                    
                move_id, name, category = move_data
                result = self._test_recoil_move(move_id, name)
                
                if result['success']:
                    self.test_results['passed'].append({
                        'move': name,
                        'category': 'Recoil',
                        'details': f"Dealt {result.get('damage', 0)} damage, took {result.get('recoil', 0)} recoil"
                    })
                    self.moves_tested.add(name)
                    
            except Exception as e:
                self.test_results['errors'].append({
                    'move': move_name,
                    'category': 'Recoil',
                    'error': str(e)
                })
        
        print(f"[OK] Completed recoil moves test")
        
    def test_secondary_effects(self, all_moves):
        """Test moves with secondary effects - run multiple times to verify probability"""
        print("\n" + "="*80)
        print("TEST CATEGORY: SECONDARY EFFECTS (All moves with secondary effects)")
        print("="*80)
        
        # Query database for ALL moves that have secondary effects
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT DISTINCT m.id, m.name, m.category, m.power,
                   mei.probability,
                   me.effect_type, me.status_condition, me.name as effect_name
            FROM moves m
            JOIN move_effect_instances mei ON m.id = mei.move_id
            JOIN move_effects me ON mei.effect_id = me.id
            WHERE mei.probability < 100 
               OR (me.effect_type = 'STATUS' AND m.causes_damage = 1)
               OR me.name LIKE '%Flinch%'
            ORDER BY m.name
        """)
        
        secondary_effect_moves = cursor.fetchall()
        print(f"Found {len(secondary_effect_moves)} moves with secondary effects to test\n")
        
        tested_moves = set()  # Track which moves we've already tested
        
        for move_id, move_name, category, power, probability, effect_type, status_condition, effect_name in secondary_effect_moves:
            # Skip if already tested this move
            if move_name in tested_moves:
                continue
            tested_moves.add(move_name)
            
            try:
                # Determine expected effect
                expected = {
                    'probability': probability,
                    'effect_type': effect_type,
                    'status': status_condition
                }
                
                # Determine what effect we're looking for
                if 'flinch' in effect_name.lower():
                    expected['effect'] = 'flinch'
                elif status_condition and status_condition != 'None':
                    expected['effect'] = status_condition.lower()
                elif effect_type == 'STAT_CHANGE':
                    expected['effect'] = 'stat_change'
                else:
                    expected['effect'] = 'other'
                
                # Run multiple times to test probability-based effects
                result = self._test_secondary_effect_probability(move_id, move_name, expected)
                
                if result['success']:
                    self.test_results['passed'].append({
                        'move': move_name,
                        'category': 'Secondary Effect',
                        'details': f"{result.get('effect_triggered', 0)}/{result.get('total_runs', 0)} triggers ({result.get('trigger_rate', 0):.1f}%), expected {probability}% - Effect: {expected['effect']}"
                    })
                else:
                    self.test_results['failed'].append({
                        'move': move_name,
                        'category': 'Secondary Effect',
                        'reason': result.get('reason', f"Expected {probability}% but got {result.get('trigger_rate', 0):.1f}%")
                    })
                    
                self.moves_tested.add(move_name)
                    
            except Exception as e:
                self.test_results['errors'].append({
                    'move': move_name,
                    'category': 'Secondary Effect',
                    'error': str(e),
                    'traceback': traceback.format_exc()
                })
        
        print(f"[OK] Completed secondary effects test - tested {len(tested_moves)} unique moves")

        
    # ========== INDIVIDUAL TEST METHODS ==========
    
    def _test_single_move(self, move_id: int, move_name: str, category: str) -> Dict:
        """Test a single move execution"""
        try:
            # Create test Pokemon with specific moves
            attacker = self._create_test_pokemon(100, [move_id])
            defender = self._create_test_pokemon(100, [1])  # Tackle
            
            # Convert Move objects to dicts for BattleAction
            attacker_move = self._move_obj_to_dict(attacker.moves[0])
            defender_move = self._move_obj_to_dict(defender.moves[0])
            
            # Create battle state
            battle_state = self._create_test_battle_state(attacker, defender)
            turn_manager = TurnManager(battle_state)
            
            # Record initial HP
            defender_initial_hp = defender.current_hp
            
            # Create and execute action
            action = BattleAction(
                pokemon=attacker,
                action_type=ActionType.FIGHT,
                move=attacker_move,
                target=defender
            )
            
            dummy_action = BattleAction(
                pokemon=defender,
                action_type=ActionType.FIGHT,
                move=defender_move,
                target=attacker
            )
            
            result = turn_manager.execute_turn([action, dummy_action])
            
            # Calculate damage dealt
            damage = defender_initial_hp - defender.current_hp
            
            return {
                'success': True,
                'damage': damage,
                'log': result['turn_log']
            }
            
        except Exception as e:
            return {
                'success': False,
                'reason': f"Exception: {str(e)}",
                'traceback': traceback.format_exc()
            }
            
    def _test_status_move(self, move_id: int, move_name: str) -> Dict:
        """Test a status-inflicting move"""
        try:
            attacker = self._create_test_pokemon(100, [move_id])
            defender = self._create_test_pokemon(100, [1])
            
            attacker_move = self._move_obj_to_dict(attacker.moves[0])
            defender_move = self._move_obj_to_dict(defender.moves[0])
            
            battle_state = self._create_test_battle_state(attacker, defender)
            turn_manager = TurnManager(battle_state)
            
            initial_status = defender.status
            
            action = BattleAction(
                pokemon=attacker,
                action_type=ActionType.FIGHT,
                move=attacker_move,
                target=defender
            )
            
            dummy_action = BattleAction(
                pokemon=defender,
                action_type=ActionType.FIGHT,
                move=defender_move,
                target=attacker
            )
            
            result = turn_manager.execute_turn([action, dummy_action])
            
            status_applied = defender.status != initial_status
            
            return {
                'success': status_applied or 'already' in ' '.join(result['turn_log']).lower(),
                'status': defender.status,
                'log': result['turn_log']
            }
            
        except Exception as e:
            return {
                'success': False,
                'reason': f"Exception: {str(e)}"
            }
            
    def _test_stat_change_move(self, move_id: int, move_name: str) -> Dict:
        """Test a stat-changing move"""
        try:
            attacker = self._create_test_pokemon(100, [move_id])
            defender = self._create_test_pokemon(100, [1])
            
            attacker_move = self._move_obj_to_dict(attacker.moves[0])
            defender_move = self._move_obj_to_dict(defender.moves[0])
            
            battle_state = self._create_test_battle_state(attacker, defender)
            turn_manager = TurnManager(battle_state)
            
            # Record initial stat stages
            initial_stages = attacker.stat_stages.copy()
            
            action = BattleAction(
                pokemon=attacker,
                action_type=ActionType.FIGHT,
                move=attacker_move,
                target=defender
            )
            
            dummy_action = BattleAction(
                pokemon=defender,
                action_type=ActionType.FIGHT,
                move=defender_move,
                target=attacker
            )
            
            result = turn_manager.execute_turn([action, dummy_action])
            
            # Check if any stat changed
            stats_changed = any(
                attacker.stat_stages[stat] != initial_stages[stat]
                for stat in initial_stages
            )
            
            return {
                'success': stats_changed,
                'stat_changes': {k: attacker.stat_stages[k] - initial_stages[k] 
                                for k in initial_stages if attacker.stat_stages[k] != initial_stages[k]},
                'log': result['turn_log']
            }
            
        except Exception as e:
            return {
                'success': False,
                'reason': f"Exception: {str(e)}"
            }
            
    def _test_healing_move(self, move_id: int, move_name: str) -> Dict:
        """Test a healing move"""
        try:
            attacker = self._create_test_pokemon(100, [move_id])
            defender = self._create_test_pokemon(100, [1])
            
            # Damage attacker first
            attacker.current_hp = attacker.max_hp // 2
            
            attacker_move = self._move_obj_to_dict(attacker.moves[0])
            defender_move = self._move_obj_to_dict(defender.moves[0])
            
            battle_state = self._create_test_battle_state(attacker, defender)
            turn_manager = TurnManager(battle_state)
            
            initial_hp = attacker.current_hp
            
            action = BattleAction(
                pokemon=attacker,
                action_type=ActionType.FIGHT,
                move=attacker_move,
                target=defender
            )
            
            dummy_action = BattleAction(
                pokemon=defender,
                action_type=ActionType.FIGHT,
                move=defender_move,
                target=attacker
            )
            
            result = turn_manager.execute_turn([action, dummy_action])
            
            hp_healed = attacker.current_hp - initial_hp
            
            return {
                'success': hp_healed > 0,
                'hp_healed': hp_healed,
                'log': result['turn_log']
            }
            
        except Exception as e:
            return {
                'success': False,
                'reason': f"Exception: {str(e)}"
            }
            
    def _test_complex_move(self, move_id: int, move_name: str) -> Dict:
        """Test complex moves (charge, counter, etc.)"""
        try:
            attacker = self._create_test_pokemon(100, [move_id])
            defender = self._create_test_pokemon(100, [1])
            
            move_dict = self._get_move_dict(move_id)
            battle_state = self._create_test_battle_state(attacker, defender)
            turn_manager = TurnManager(battle_state)
            
            action = BattleAction(
                pokemon=attacker,
                action_type=ActionType.FIGHT,
                move=move_dict,
                target=defender
            )
            
            dummy_action = BattleAction(
                pokemon=defender,
                action_type=ActionType.FIGHT,
                move=self._get_move_dict(1),
                target=attacker
            )
            
            result = turn_manager.execute_turn([action, dummy_action])
            
            # Check if move executed (look for move name in log)
            move_executed = any(move_name in log for log in result['turn_log'])
            
            return {
                'success': move_executed,
                'details': f"Move appears in turn log: {move_executed}",
                'log': result['turn_log']
            }
            
        except Exception as e:
            return {
                'success': False,
                'reason': f"Exception: {str(e)}",
                'traceback': traceback.format_exc()
            }
            
    def _test_weather_move(self, move_id: int, move_name: str) -> Dict:
        """Test weather-setting moves"""
        try:
            attacker = self._create_test_pokemon(100, [move_id])
            defender = self._create_test_pokemon(100, [1])
            
            attacker_move = self._move_obj_to_dict(attacker.moves[0])
            defender_move = self._move_obj_to_dict(defender.moves[0])
            
            battle_state = self._create_test_battle_state(attacker, defender)
            turn_manager = TurnManager(battle_state)
            
            initial_weather = battle_state['weather']['type']
            
            action = BattleAction(
                pokemon=attacker,
                action_type=ActionType.FIGHT,
                move=attacker_move,
                target=defender
            )
            
            dummy_action = BattleAction(
                pokemon=defender,
                action_type=ActionType.FIGHT,
                move=defender_move,
                target=attacker
            )
            
            result = turn_manager.execute_turn([action, dummy_action])
            
            weather_changed = battle_state['weather']['type'] != initial_weather
            
            return {
                'success': weather_changed,
                'weather': battle_state['weather']['type'],
                'log': result['turn_log']
            }
            
        except Exception as e:
            return {
                'success': False,
                'reason': f"Exception: {str(e)}"
            }
            
    def _test_field_effect_move(self, move_id: int, move_name: str) -> Dict:
        """Test field effect moves"""
        try:
            attacker = self._create_test_pokemon(100, [move_id])
            defender = self._create_test_pokemon(100, [1])
            
            attacker_move = self._move_obj_to_dict(attacker.moves[0])
            defender_move = self._move_obj_to_dict(defender.moves[0])
            
            battle_state = self._create_test_battle_state(attacker, defender)
            turn_manager = TurnManager(battle_state)
            
            action = BattleAction(
                pokemon=attacker,
                action_type=ActionType.FIGHT,
                move=attacker_move,
                target=defender
            )
            
            dummy_action = BattleAction(
                pokemon=defender,
                action_type=ActionType.FIGHT,
                move=defender_move,
                target=attacker
            )
            
            result = turn_manager.execute_turn([action, dummy_action])
            
            # Check if field effect was mentioned in log
            field_set = any(move_name in log or 'set up' in log.lower() for log in result['turn_log'])
            
            return {
                'success': field_set,
                'details': f"Field effect appears to be set: {field_set}",
                'log': result['turn_log']
            }
            
        except Exception as e:
            return {
                'success': False,
                'reason': f"Exception: {str(e)}"
            }
            
    def _test_recoil_move(self, move_id: int, move_name: str) -> Dict:
        """Test recoil damage moves"""
        try:
            attacker = self._create_test_pokemon(100, [move_id])
            defender = self._create_test_pokemon(100, [1])
            
            attacker_move = self._move_obj_to_dict(attacker.moves[0])
            defender_move = self._move_obj_to_dict(defender.moves[0])
            
            battle_state = self._create_test_battle_state(attacker, defender)
            turn_manager = TurnManager(battle_state)
            
            attacker_initial_hp = attacker.current_hp
            defender_initial_hp = defender.current_hp
            
            action = BattleAction(
                pokemon=attacker,
                action_type=ActionType.FIGHT,
                move=attacker_move,
                target=defender
            )
            
            dummy_action = BattleAction(
                pokemon=defender,
                action_type=ActionType.FIGHT,
                move=defender_move,
                target=attacker
            )
            
            result = turn_manager.execute_turn([action, dummy_action])
            
            damage = defender_initial_hp - defender.current_hp
            recoil = attacker_initial_hp - attacker.current_hp
            
            return {
                'success': damage > 0,
                'damage': damage,
                'recoil': recoil,
                'log': result['turn_log']
            }
            
        except Exception as e:
            return {
                'success': False,
                'reason': f"Exception: {str(e)}"
            }
    
    def _test_secondary_effect_probability(self, move_id: int, move_name: str, expected: Dict) -> Dict:
        """Test secondary effects by running move multiple times to verify probability"""
        try:
            effect_triggered = 0
            total_runs = 30  # Run 30 times for better probability testing
            
            for run in range(total_runs):
                # Create fresh Pokemon for each run
                attacker = self._create_test_pokemon(100, [move_id])
                defender = self._create_test_pokemon(100, [1])
                
                attacker_move = self._move_obj_to_dict(attacker.moves[0])
                defender_move = self._move_obj_to_dict(defender.moves[0])
                
                battle_state = self._create_test_battle_state(attacker, defender)
                turn_manager = TurnManager(battle_state)
                
                # Check initial status
                initial_status = defender.status
                initial_flinch = getattr(defender, 'flinched', False)
                initial_stat_stages = defender.stat_stages.copy()
                
                action = BattleAction(
                    pokemon=attacker,
                    action_type=ActionType.FIGHT,
                    move=attacker_move,
                    target=defender
                )
                
                dummy_action = BattleAction(
                    pokemon=defender,
                    action_type=ActionType.FIGHT,
                    move=defender_move,
                    target=attacker
                )
                
                result = turn_manager.execute_turn([action, dummy_action])
                
                # Check if secondary effect triggered based on effect type
                effect_type = expected.get('effect', 'unknown')
                
                if effect_type == 'flinch':
                    # Check turn log for flinch message
                    if any('flinch' in log.lower() for log in result['turn_log']):
                        effect_triggered += 1
                elif effect_type == 'stat_change':
                    # Check if any stat changed
                    if any(defender.stat_stages[stat] != initial_stat_stages[stat] for stat in initial_stat_stages):
                        effect_triggered += 1
                elif effect_type in ['paralysis', 'burn', 'freeze', 'poison', 'sleep']:
                    # Check status condition
                    if defender.status and defender.status != initial_status:
                        if effect_type in defender.status.lower():
                            effect_triggered += 1
                elif effect_type == 'other':
                    # Check turn log for any indication of effect
                    effect_keywords = ['effect', 'applied', 'triggered', 'activated']
                    if any(keyword in ' '.join(result['turn_log']).lower() for keyword in effect_keywords):
                        effect_triggered += 1
            
            # Calculate trigger rate
            trigger_rate = (effect_triggered / total_runs) * 100
            expected_rate = expected.get('probability', 50)
            
            # Determine success based on probability
            # For 100% probability moves, expect high trigger rate
            if expected_rate >= 90:
                success = effect_triggered >= (total_runs * 0.8)  # At least 80% of runs
            # For high probability moves (50-90%)
            elif expected_rate >= 50:
                success = effect_triggered >= (total_runs * 0.3)  # At least 30% of runs
            # For medium probability moves (30-50%)
            elif expected_rate >= 30:
                success = effect_triggered >= (total_runs * 0.15)  # At least 15% of runs
            # For low probability moves (10-30%)
            elif expected_rate >= 10:
                success = effect_triggered >= 2  # At least 2 triggers in 30 runs
            else:  # Very low probability (<10%)
                success = effect_triggered >= 1  # At least 1 trigger in 30 runs
            
            return {
                'success': success,
                'effect_triggered': effect_triggered,
                'total_runs': total_runs,
                'trigger_rate': trigger_rate,
                'log': result['turn_log'] if 'result' in locals() else []
            }
            
        except Exception as e:
            return {
                'success': False,
                'reason': f"Exception: {str(e)}",
                'traceback': traceback.format_exc()
            }
    
    # ========== HELPER METHODS ==========
    
    def _create_test_pokemon(self, level: int, move_ids: List[int]) -> Pokemon:
        """Create a Pokemon for testing"""
        # Use Pikachu as base (ID 25)
        pokemon = Pokemon(pokemon_id=25, level=level, moveset=move_ids[:4])
        
        return pokemon
    
    def _move_obj_to_dict(self, move_obj) -> Dict:
        """Convert Move object to dictionary format"""
        if isinstance(move_obj, dict):
            return move_obj
        
        return {
            'id': move_obj.id,
            'name': move_obj.name,
            'type': move_obj.type,
            'category': move_obj.category,
            'power': move_obj.power,
            'accuracy': move_obj.accuracy,
            'pp': move_obj.pp_current,
            'priority': move_obj.priority,
            'causes_damage': move_obj.causes_damage
        }
        
        
    def _get_move_dict(self, move_id: int) -> Dict:
        """Get move as dictionary from database"""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT id, name, type, category, power, accuracy, pp, priority, causes_damage
            FROM moves WHERE id = ?
        """, (move_id,))
        
        result = cursor.fetchone()
        if not result:
            return None
            
        return {
            'id': result[0],
            'name': result[1],
            'type': result[2],
            'category': result[3],
            'power': result[4],
            'accuracy': result[5],
            'pp': result[6],
            'priority': result[7],
            'causes_damage': bool(result[8])
        }
        
    def _create_test_battle_state(self, pokemon1: Pokemon, pokemon2: Pokemon) -> Dict:
        """Create a test battle state"""
        return {
            'player1_active': pokemon1,
            'player2_active': pokemon2,
            'player1_team': [pokemon1],
            'player2_team': [pokemon2],
            'weather': {'type': 'None', 'turns_remaining': 0},
            'field_effects': {},
            'turn_count': 0
        }
        
    def generate_report(self):
        """Generate comprehensive test report"""
        print("\n" + "="*80)
        print(" "*25 + "TEST RESULTS SUMMARY")
        print("="*80)
        
        total_tests = (len(self.test_results['passed']) + 
                      len(self.test_results['failed']) + 
                      len(self.test_results['errors']))
        
        print(f"\nTotal Tests Run: {total_tests}")
        print(f"Moves Tested: {len(self.moves_tested)}")
        print(f"\n[PASS] PASSED: {len(self.test_results['passed'])}")
        print(f"[FAIL] FAILED: {len(self.test_results['failed'])}")
        print(f"[ERROR] ERRORS: {len(self.test_results['errors'])}")
        print(f"[WARN]  WARNINGS: {len(self.test_results['warnings'])}")
        
        # Show failed tests
        if self.test_results['failed']:
            print("\n" + "="*80)
            print("FAILED TESTS (moves that didn't work as expected)")
            print("="*80)
            for test in self.test_results['failed'][:20]:  # Show first 20
                print(f"\n[FAIL] {test['move']} ({test['category']})")
                print(f"   Reason: {test['reason']}")
        
        # Show errors
        if self.test_results['errors']:
            print("\n" + "="*80)
            print("ERRORS (moves that caused exceptions)")
            print("="*80)
            for test in self.test_results['errors'][:20]:  # Show first 20
                print(f"\n[ERROR] {test['move']} ({test['category']})")
                print(f"   Error: {test['error']}")
                if 'traceback' in test:
                    print(f"   Traceback: {test['traceback'][:200]}...")
        
        # Show warnings
        if self.test_results['warnings']:
            print("\n" + "="*80)
            print("WARNINGS (moves with issues)")
            print("="*80)
            for test in self.test_results['warnings']:
                print(f"\n[WARN]  {test['move']} ({test['category']})")
                print(f"   Message: {test['message']}")
        
        # Sample passed tests
        if self.test_results['passed']:
            print("\n" + "="*80)
            print("PASSED TESTS (sample - first 20)")
            print("="*80)
            for test in self.test_results['passed'][:20]:
                print(f"[PASS] {test['move']} ({test['category']}) - {test['details']}")
        
        # Save detailed report to file
        self._save_detailed_report()
        
    def _save_detailed_report(self):
        """Save detailed report to file"""
        filename = "test_results_detailed.txt"
        
        with open(filename, 'w', encoding='utf-8') as f:
            f.write("="*80 + "\n")
            f.write(" "*20 + "DETAILED TEST RESULTS REPORT\n")
            f.write("="*80 + "\n\n")
            
            # Summary
            total = (len(self.test_results['passed']) + 
                    len(self.test_results['failed']) + 
                    len(self.test_results['errors']))
            
            f.write(f"Total Tests: {total}\n")
            f.write(f"Passed: {len(self.test_results['passed'])}\n")
            f.write(f"Failed: {len(self.test_results['failed'])}\n")
            f.write(f"Errors: {len(self.test_results['errors'])}\n")
            f.write(f"Warnings: {len(self.test_results['warnings'])}\n\n")
            
            # All passed tests
            f.write("="*80 + "\n")
            f.write("PASSED TESTS\n")
            f.write("="*80 + "\n")
            for test in self.test_results['passed']:
                f.write(f"\n[PASS] {test['move']} ({test['category']})\n")
                f.write(f"   Details: {test['details']}\n")
                if 'log' in test:
                    f.write(f"   Log: {test['log'][:500]}\n")
            
            # All failed tests
            f.write("\n" + "="*80 + "\n")
            f.write("FAILED TESTS\n")
            f.write("="*80 + "\n")
            for test in self.test_results['failed']:
                f.write(f"\n[FAIL] {test['move']} ({test['category']})\n")
                f.write(f"   Reason: {test['reason']}\n")
            
            # All errors
            f.write("\n" + "="*80 + "\n")
            f.write("ERRORS\n")
            f.write("="*80 + "\n")
            for test in self.test_results['errors']:
                f.write(f"\n[ERROR] {test['move']} ({test['category']})\n")
                f.write(f"   Error: {test['error']}\n")
                if 'traceback' in test:
                    f.write(f"   Traceback:\n{test['traceback']}\n")
            
            # All warnings
            f.write("\n" + "="*80 + "\n")
            f.write("WARNINGS\n")
            f.write("="*80 + "\n")
            for test in self.test_results['warnings']:
                f.write(f"\n[WARN]  {test['move']} ({test['category']})\n")
                f.write(f"   Message: {test['message']}\n")
        
        print(f"\n[FILE] Detailed report saved to: {filename}")


def main():
    """Run the test suite"""
    try:
        tester = MoveSystemTester()
        tester.run_all_tests()
        
    except KeyboardInterrupt:
        print("\n\nTesting interrupted by user.")
    except Exception as e:
        print(f"\n\nFatal error during testing: {e}")
        traceback.print_exc()


if __name__ == "__main__":
    main()
