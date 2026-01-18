"""
Comprehensive Testing System for Pokemon Evolution Logic
Verifies:
1. Standard level-up evolution (e.g., Charmander -> Charmeleon)
2. Retroactive evolution (e.g., Charmander Lvl 50 -> Charmeleon)
3. Branching evolution candidates (e.g., Gloom -> Vileplume/Bellossom)
4. Evolution state transitions (Stat updates, name changes)
5. Sequential evolution gating (One stage per trigger)

Run this file directly: python tests/test_evolution_system.py
"""
import unittest
import sys
import os
import sqlite3

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'models')))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))

from models.Pokemon import Pokemon

class TestEvolutionSystem(unittest.TestCase):
    
    @classmethod
    def setUpClass(cls):
        """Verify DB existence before starting"""
        cls.db_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'pokemon_battle.db')
        if not os.path.exists(cls.db_path):
            raise unittest.SkipTest("Database not found. Please run update_evolution_data.py first.")

    def test_01_standard_evolution_check(self):
        """Test standard evolution eligibility (Charmander at Level 16)"""
        # Charmander (ID 4) evolves at Level 16
        charmander = Pokemon(4, level=16)
        
        can_evolve, evo_ids = charmander.can_evolve()
        self.assertTrue(can_evolve, "Charmander should be able to evolve at level 16")
        self.assertIn(5, evo_ids, "Evolution targets should include Charmeleon (ID 5)")
        
        # Test below level
        baby_charmander = Pokemon(4, level=15)
        can_evolve_baby, _ = baby_charmander.can_evolve()
        self.assertFalse(can_evolve_baby, "Charmander should NOT evolve at level 15")

    def test_02_retroactive_evolution_check(self):
        """Test retroactive evolution eligibility (Charmander at Level 50)"""
        # Charmander evolves at 16, but current level is 50
        charmander = Pokemon(4, level=50)
        
        can_evolve, evo_ids = charmander.can_evolve()
        self.assertTrue(can_evolve, "Level 50 Charmander should still be able to evolve")
        self.assertEqual(evo_ids, [5], "Should only target Charmeleon (ID 5)")

    def test_03_branching_evolution_candidates(self):
        """Test detection of multiple evolution paths (Gloom/Eevee)"""
        # Gloom (ID 44) -> Vileplume (45) or Bellossom (182)
        # Using level 50 to guarantee eligibility
        gloom = Pokemon(44, level=50)
        
        can_evolve, evo_ids = gloom.can_evolve()
        self.assertTrue(can_evolve, "Gloom should be able to evolve")
        self.assertGreater(len(evo_ids), 1, "Gloom should have more than 1 evolution option")
        
        self.assertIn(45, evo_ids, "Gloom should be able to evolve into Vileplume")
        self.assertIn(182, evo_ids, "Gloom should be able to evolve into Bellossom")
        print(f"\n[Branching Test] Gloom Candidates: {evo_ids}")

    def test_04_sequential_gating(self):
        """Test that evolutions happen one stage at a time"""
        # Create super-leveled Charmander
        pkmn = Pokemon(4, level=50) # Charmander
        
        # Phase 1: Charmander -> Charmeleon
        can_1, ids_1 = pkmn.can_evolve()
        self.assertTrue(can_1)
        self.assertEqual(ids_1[0], 5) # Charmeleon
        
        # Execute first evolution
        pkmn.evolve(ids_1[0])
        self.assertEqual(pkmn.name, "Charmeleon", "Name should update to Charmeleon")
        self.assertEqual(pkmn.id, 5, "ID should update to 5")
        
        # Phase 2: Verify it is now Charmeleon, ready for NEXT evolution logic
        # Ideally, in a single game tick, this wouldn't trigger again, 
        # but the object state must reflect readiness for the next call.
        
        # The object should NOW identify as Charmeleon lvl 50.
        # It should NOW be eligible for Charizard (ID 6).
        can_2, ids_2 = pkmn.can_evolve()
        self.assertTrue(can_2, "Charmeleon should now be eligible for Charizard")
        self.assertEqual(ids_2[0], 6, "Target should be Charizard")
        
        # This proves the logic handles stages sequentially:
        # One call to evolve() only advanced it one ID.

    def test_05_evolution_state_integrity(self):
        """Verify state (stats, HP) is preserved/updated correctly"""
        # Charmander evolving
        pkmn = Pokemon(4, level=20)
        initial_hp_pct = pkmn.current_hp / pkmn.max_hp
        old_attack = pkmn.attack
        
        # Evolve
        _, ids = pkmn.can_evolve()
        evo_info = pkmn.evolve(ids[0])
        
        # Verify stats increased (Charmeleon > Charmander)
        self.assertGreater(pkmn.attack, old_attack, "Attack should increase after evolution")
        self.assertGreater(pkmn.max_hp, 0, "Max HP should be valid")
        
        # Verify HP percentage preservation (approximate)
        new_hp_pct = pkmn.current_hp / pkmn.max_hp
        self.assertAlmostEqual(initial_hp_pct, new_hp_pct, delta=0.1, msg="HP percentage should be preserved")

    def test_06_no_evolution(self):
        """Test Pokemon that do not evolve"""
        # Charizard (ID 6) or Tauros (ID 128) - usually don't evolve further in Gen 1-4 logic context
        # Let's use Tauros (128)
        tauros = Pokemon(128, level=50)
        can, ids = tauros.can_evolve()
        self.assertFalse(can, "Tauros should not evolve")
        self.assertIsNone(ids, "Evolution IDs should be None")

if __name__ == '__main__':
    unittest.main()
