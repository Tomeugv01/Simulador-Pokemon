


# Initial characteristics and possible escalation of the project

## Initial play-loop and content

- Initialy, our simulator will be comprised to the original 151 gen1 pokemon with a limited move pool so we can focus on better implementation of our engine, prioritizing going in depth with our combat mechanics
- Initial play loop: The simulator will follow a roguelike game design in which the player will start with a relatively weak team and through a series of increasingly more difficult set of battles will slowly create a stronger team untlil he finaly ends up facing a final bossfights.
- Each run will be comprised of both a randomly generated team for both the player and each of their opponent EXCEPT for the final boss, who will have a unique and predefined pokemon pool from which it will generate its own team, in order to allow for a more difficult and thus satisfiing challenge.
- A longer gamemode where instead of just having a series of reandom battles leading to a final boss fight, there will be a series of battles similar to the original games gym leaders, with tams of pokemon of a single type will also be implemented

## Future implementations
### Since our main priority from the biggining is to ensure that our battle simulation engine is as advanced and solid as we are able to, when this obective is accomplished the following are our priorites of what content to add
- Increase the pokemon pool form the original 151 to the 493 present in gen4
- Increase the move diversity with more complex moves that further expands the pool variety
- Instead of the game loop progression beeing explained fully in the textbox, implement a ui where the player can be aware of their porgress
- With the addition of more pokemon to the existing pool, we will have the option to implement a harder game mode where the boss fight pools can be tuned for a more callenging experience to the player
- A more complex ai system for the enemy cpu in order to add a complex and harder experience.
- Its also in our plans to include a held item system that is also tied to the archetype system




# Team Generation

## Pokemon selector

- Using different ranges of the total_stats value, random teams will be seleected for the opponent, creating an enviroment where teams are created with a difficulty progression is as best reflected as possible
- A similar method will be implemented for the player team, a first team of pokemon will be given with a predetermined range of stats and after each encounter, he will be givven the option to add or swap a new mon of progresivly stronger characteristics

## Move selector

- Once a Pokemon is selected to be added to a team, the move selection proces will begin.
- Depending on the relative value of each stat of the mon (what percentage of their stats are alocated to each one) it will be assigned to a different archetype and thus it will get assigned 4 differnt random moves that fall onto this archetypes.
- In the probable case that a pokemon falls into more than one of these archetypes, its 4 moves will be randomly selected between all of the possible pools of moves
- After each encounter, instead of adding a new pokemon to his team, the player will also get the option to replace one of his moves with an other one of ANY archetype of his liking.


