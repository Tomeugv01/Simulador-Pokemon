"""
Pokemon Experience System
Implements Gen 1-5 experience formulas for all growth curves
"""
import math


class ExperienceCurve:
    """
    Pokemon experience growth curves.
    Each curve determines how much EXP is needed to reach each level.
    """
    
    @staticmethod
    def exp_for_level(level: int, curve: str) -> int:
        """
        Calculate total EXP required to reach a given level.
        
        Args:
            level: Target level (1-100)
            curve: Growth curve name ('fast', 'medium-fast', 'medium-slow', 'slow', 'fluctuating')
            
        Returns:
            Total EXP required to reach that level
        """
        if level <= 1:
            return 0
        
        n = level
        
        if curve == 'fast':
            # Fast: 0.8 * n^3
            return int(0.8 * (n ** 3))
        
        elif curve == 'medium-fast':
            # Medium Fast: n^3
            return n ** 3
        
        elif curve == 'medium-slow':
            # Medium Slow: 1.2 * n^3 - 15 * n^2 + 100 * n - 140
            return int(1.2 * (n ** 3) - 15 * (n ** 2) + 100 * n - 140)
        
        elif curve == 'slow':
            # Slow: 1.25 * n^3
            return int(1.25 * (n ** 3))
        
        elif curve == 'fluctuating':
            # Fluctuating: Complex piecewise function
            if n <= 15:
                return int(n ** 3 * ((((n + 1) // 3) + 24) / 50))
            elif n <= 36:
                return int(n ** 3 * ((n + 14) / 50))
            else:
                return int(n ** 3 * (((n // 2) + 32) / 50))
        
        else:
            # Default to medium-fast if unknown
            return n ** 3
    
    @staticmethod
    def exp_to_next_level(current_level: int, curve: str) -> int:
        """
        Calculate EXP needed to go from current level to next level.
        
        Args:
            current_level: Current level (1-99)
            curve: Growth curve name
            
        Returns:
            EXP needed for next level
        """
        if current_level >= 100:
            return 0
        
        current_exp = ExperienceCurve.exp_for_level(current_level, curve)
        next_exp = ExperienceCurve.exp_for_level(current_level + 1, curve)
        return next_exp - current_exp
    
    @staticmethod
    def level_from_exp(total_exp: int, curve: str) -> int:
        """
        Determine level based on total EXP.
        
        Args:
            total_exp: Total accumulated EXP
            curve: Growth curve name
            
        Returns:
            Current level (1-100)
        """
        # Binary search for efficiency
        low, high = 1, 100
        
        while low < high:
            mid = (low + high + 1) // 2
            if ExperienceCurve.exp_for_level(mid, curve) <= total_exp:
                low = mid
            else:
                high = mid - 1
        
        return low
    
    @staticmethod
    def calculate_exp_gain(defeated_pokemon, winner_level: int, is_wild: bool = False, 
                          is_trainer: bool = True, participated: bool = True,
                          holding_exp_share: bool = False) -> int:
        """
        Calculate EXP gained from defeating a Pokemon (Gen 5 formula).
        
        Args:
            defeated_pokemon: The defeated Pokemon instance
            winner_level: Level of the Pokemon receiving EXP
            is_wild: Whether the defeated Pokemon was wild
            is_trainer: Whether the defeated Pokemon was owned by a trainer
            participated: Whether the Pokemon participated in battle
            holding_exp_share: Whether using EXP Share
            
        Returns:
            EXP points gained
        """
        # Base experience yield (based on base stat total)
        base_exp = defeated_pokemon.base_hp + defeated_pokemon.base_attack + \
                   defeated_pokemon.base_defense + defeated_pokemon.base_sp_attack + \
                   defeated_pokemon.base_sp_defense + defeated_pokemon.base_speed
        
        # Scale base exp (roughly matches official values)
        base_exp = max(50, base_exp // 3)
        
        # Level of defeated Pokemon
        defeated_level = defeated_pokemon.level
        
        # Basic formula: (base * level) / 7
        exp_gain = (base_exp * defeated_level) // 7
        
        # Trainer bonus (1.5x for trainer battles)
        if is_trainer and not is_wild:
            exp_gain = int(exp_gain * 1.5)
        
        # Participation modifier
        if not participated and holding_exp_share:
            exp_gain = exp_gain // 2
        
        # Level scaling (if winner is higher level, less EXP)
        if winner_level > defeated_level:
            level_diff = winner_level - defeated_level
            # Reduce by 10% per level difference (minimum 50%)
            reduction = min(0.5, level_diff * 0.1)
            exp_gain = int(exp_gain * (1.0 - reduction))
        
        return max(1, exp_gain)  # Minimum 1 EXP
    
    @staticmethod
    def get_curve_multiplier(curve: str) -> float:
        """
        Get relative speed multiplier for a growth curve.
        Used for level scaling - faster curves = higher levels for same strength.
        
        Args:
            curve: Growth curve name
            
        Returns:
            Multiplier relative to medium-fast (1.0 baseline)
        """
        # Compare EXP required at level 50
        reference_level = 50
        medium_fast_exp = ExperienceCurve.exp_for_level(reference_level, 'medium-fast')
        curve_exp = ExperienceCurve.exp_for_level(reference_level, curve)
        
        # Return ratio (how much faster/slower)
        return curve_exp / medium_fast_exp
    
    @staticmethod
    def scale_level_for_curve(base_level: int, curve: str) -> int:
        """
        Scale a base level to account for growth curve.
        Slow curves get lower levels, fast curves get higher levels.
        
        Args:
            base_level: Target power level
            curve: Growth curve to scale for
            
        Returns:
            Adjusted level
        """
        multiplier = ExperienceCurve.get_curve_multiplier(curve)
        
        # Inverse relationship: slow curves (high multiplier) = lower level
        # Fast curves (low multiplier) = higher level
        if multiplier > 1.0:
            # Slower than medium-fast: reduce level
            scaled = base_level / (multiplier ** 0.5)
        else:
            # Faster than medium-fast: increase level
            scaled = base_level * ((1.0 / multiplier) ** 0.5)
        
        return max(1, min(100, round(scaled)))


# Example usage and testing
if __name__ == "__main__":
    print("="*70)
    print("POKEMON EXPERIENCE SYSTEM")
    print("="*70)
    
    # Test 1: EXP requirements for different curves
    print("\n1. EXP Required to Reach Level 50:")
    print("-"*70)
    
    curves = ['fast', 'medium-fast', 'medium-slow', 'slow', 'fluctuating']
    for curve in curves:
        exp = ExperienceCurve.exp_for_level(50, curve)
        print(f"  {curve:15s}: {exp:,} EXP")
    
    # Test 2: Level progression comparison
    print("\n2. Level Progression (EXP required):")
    print("-"*70)
    print(f"{'Level':<8} {'Fast':>12} {'Medium-Fast':>12} {'Medium-Slow':>12} {'Slow':>12}")
    print("-"*70)
    
    for level in [5, 10, 20, 30, 50, 75, 100]:
        print(f"{level:<8} ", end="")
        for curve in ['fast', 'medium-fast', 'medium-slow', 'slow']:
            exp = ExperienceCurve.exp_for_level(level, curve)
            print(f"{exp:>12,} ", end="")
        print()
    
    # Test 3: Level scaling
    print("\n3. Level Scaling for Balanced Difficulty:")
    print("-"*70)
    print("Base Level 20 scaled for each curve:")
    print("-"*70)
    
    base_level = 20
    for curve in curves:
        scaled = ExperienceCurve.scale_level_for_curve(base_level, curve)
        multiplier = ExperienceCurve.get_curve_multiplier(curve)
        print(f"  {curve:15s}: Level {scaled:2d} (multiplier: {multiplier:.2f})")
    
    print("\n" + "="*70)
    print("✅ Experience system ready!")
    print("="*70)
