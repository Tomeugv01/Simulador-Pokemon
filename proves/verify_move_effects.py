#!/usr/bin/env python3
"""Verify move effects in the database"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.database import DatabaseManager

def verify_move_effects():
    """Count total move effect instances in the database"""
    db_manager = DatabaseManager()
    conn = db_manager.get_connection()
    cursor = conn.cursor()
    
    # Count move-effect relationships
    cursor.execute("SELECT COUNT(*) FROM move_effect_instances")
    effect_count = cursor.fetchone()[0]
    
    # Count total moves
    cursor.execute("SELECT COUNT(*) FROM moves")
    move_count = cursor.fetchone()[0]
    
    # Count moves with effects
    cursor.execute("""
        SELECT COUNT(DISTINCT move_id) 
        FROM move_effect_instances
    """)
    moves_with_effects = cursor.fetchone()[0]
    
    # Get effect type distribution
    cursor.execute("""
        SELECT me.effect_type, COUNT(*) as count
        FROM move_effect_instances mei
        JOIN move_effects me ON mei.effect_id = me.id
        GROUP BY me.effect_type
        ORDER BY count DESC
    """)
    effect_distribution = cursor.fetchall()
    
    print("="*70)
    print("MOVE EFFECT DATABASE VERIFICATION")
    print("="*70)
    print(f"\nTotal moves in database: {move_count}")
    print(f"Moves with effects: {moves_with_effects}")
    print(f"Total effect instances: {effect_count}")
    print(f"\nEffect Type Distribution:")
    print("-"*70)
    for effect_type, count in effect_distribution:
        print(f"  {effect_type:20s}: {count:4d} instances")
    print("-"*70)
    
    # Show some example complex moves
    cursor.execute("""
        SELECT m.name, me.name, me.effect_type
        FROM moves m
        JOIN move_effect_instances mei ON m.id = mei.move_id
        JOIN move_effects me ON mei.effect_id = me.id
        WHERE m.name IN ('Solar Beam', 'Dig', 'Fly', 'Counter', 'Bide', 'Reflect', 'Super Fang')
        ORDER BY m.name, me.effect_type
    """)
    
    print(f"\nSample Complex Moves:")
    print("-"*70)
    current_move = None
    for move_name, effect_name, effect_type in cursor.fetchall():
        if move_name != current_move:
            print(f"\n{move_name}:")
            current_move = move_name
        print(f"  - {effect_name} ({effect_type})")
    print("-"*70)
    
    conn.close()
    
    # Verify expected count
    if effect_count >= 425:
        print(f"\n✅ SUCCESS: Database has {effect_count} effect instances (expected ≥425)")
    else:
        print(f"\n⚠️  WARNING: Database has only {effect_count} effect instances (expected ≥425)")
    
    return effect_count

if __name__ == "__main__":
    verify_move_effects()
