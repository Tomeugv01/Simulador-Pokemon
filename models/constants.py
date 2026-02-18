"""
Shared constants for the Pokemon battle system.
Centralizes type definitions, type chart, and type-related utility functions.
"""

# =============================================================================
# TYPE ID TO NAME MAPPING
# =============================================================================

TYPE_NAMES = {
    1: 'Normal', 2: 'Fire', 3: 'Water', 4: 'Electric', 5: 'Grass',
    6: 'Ice', 7: 'Fighting', 8: 'Poison', 9: 'Ground', 10: 'Flying',
    11: 'Psychic', 12: 'Bug', 13: 'Rock', 14: 'Ghost', 15: 'Dragon',
    16: 'Dark', 17: 'Steel', 18: 'Fairy'
}

# Reverse mapping: name -> ID
TYPE_IDS = {name: id for id, name in TYPE_NAMES.items()}


def get_type_name(type_id):
    """Convert type ID to type name.
    
    Args:
        type_id: Integer type ID (1-18) or string type name
        
    Returns:
        Type name string, or 'Unknown' if not found
    """
    if isinstance(type_id, str):
        return type_id  # Already a name
    return TYPE_NAMES.get(type_id, 'Unknown')


# =============================================================================
# TYPE EFFECTIVENESS CHART (Gen 6+)
# =============================================================================
# Maps attacking type -> {defending type: multiplier}
# Only non-1.0 multipliers are listed (super effective, not very effective, immune)

TYPE_CHART = {
    'Normal': {'Rock': 0.5, 'Steel': 0.5, 'Ghost': 0.0},
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
    'Ice': {'Grass': 2.0, 'Ground': 2.0, 'Flying': 2.0, 'Dragon': 2.0,
            'Fire': 0.5, 'Water': 0.5, 'Ice': 0.5, 'Steel': 0.5},
    'Fighting': {'Normal': 2.0, 'Ice': 2.0, 'Rock': 2.0, 'Dark': 2.0, 'Steel': 2.0,
                 'Poison': 0.5, 'Flying': 0.5, 'Psychic': 0.5, 'Bug': 0.5, 'Fairy': 0.5,
                 'Ghost': 0.0},
    'Poison': {'Grass': 2.0, 'Fairy': 2.0,
               'Poison': 0.5, 'Ground': 0.5, 'Rock': 0.5, 'Ghost': 0.5,
               'Steel': 0.0},
    'Ground': {'Fire': 2.0, 'Electric': 2.0, 'Poison': 2.0, 'Rock': 2.0, 'Steel': 2.0,
               'Grass': 0.5, 'Bug': 0.5,
               'Flying': 0.0},
    'Flying': {'Grass': 2.0, 'Fighting': 2.0, 'Bug': 2.0,
               'Electric': 0.5, 'Rock': 0.5, 'Steel': 0.5},
    'Psychic': {'Fighting': 2.0, 'Poison': 2.0,
                'Psychic': 0.5, 'Steel': 0.5,
                'Dark': 0.0},
    'Bug': {'Grass': 2.0, 'Psychic': 2.0, 'Dark': 2.0,
            'Fire': 0.5, 'Fighting': 0.5, 'Poison': 0.5, 'Flying': 0.5,
            'Ghost': 0.5, 'Steel': 0.5, 'Fairy': 0.5},
    'Rock': {'Fire': 2.0, 'Ice': 2.0, 'Flying': 2.0, 'Bug': 2.0,
             'Fighting': 0.5, 'Ground': 0.5, 'Steel': 0.5},
    'Ghost': {'Psychic': 2.0, 'Ghost': 2.0,
              'Dark': 0.5,
              'Normal': 0.0},
    'Dragon': {'Dragon': 2.0,
               'Steel': 0.5,
               'Fairy': 0.0},
    'Dark': {'Psychic': 2.0, 'Ghost': 2.0,
             'Fighting': 0.5, 'Dark': 0.5, 'Fairy': 0.5},
    'Steel': {'Ice': 2.0, 'Rock': 2.0, 'Fairy': 2.0,
              'Fire': 0.5, 'Water': 0.5, 'Electric': 0.5, 'Steel': 0.5},
    'Fairy': {'Fighting': 2.0, 'Dragon': 2.0, 'Dark': 2.0,
              'Fire': 0.5, 'Poison': 0.5, 'Steel': 0.5}
}


def get_type_effectiveness(attack_type, defender_type1, defender_type2=None):
    """Calculate type effectiveness multiplier.
    
    Args:
        attack_type: Attacking type name (string)
        defender_type1: Defender's primary type name
        defender_type2: Defender's secondary type name (optional)
        
    Returns:
        Float multiplier (0.0, 0.25, 0.5, 1.0, 2.0, or 4.0)
    """
    multiplier = 1.0
    
    for def_type in [defender_type1, defender_type2]:
        if def_type and attack_type in TYPE_CHART:
            multiplier *= TYPE_CHART[attack_type].get(def_type, 1.0)
    
    return multiplier
