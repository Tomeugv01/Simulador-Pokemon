
# Pokemon Database structure

## Db structure

Pokemon {
- id
- name 
- type1
- type2
- hp
- attack
- deffense
- special_attack
- special_deffense
- speed
- total_stats

}

Move {
- id
- name 
- type1
- power
- accuracity
- pp
- type (physical, special)
- archetype (phiscal_sweeper, special_sweeper, tank, etc)
- effect (JSON)

}

Ability {
- id
- name 
- effect (JSON)

}
