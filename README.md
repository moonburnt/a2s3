*This started as personal challenge to write something that may, even remotely, count as game. In one month*

# a2s3

## Description:

**a2s3** is work-in-progress action arena game, written in python + panda3d. For now there is not much to do, but the goal is to make a survival wave-based arena, where you fight hordes of enemies in order to get to the top of leaderboard.

## Project's Status:

**Early pre-alpha**

## Dependencies:

- python 3.8
- panda3d 1.10.8

## How to Play:

*Not yet*

## TODO:

In order to reach 0.1 milestone (effectively an equal to "alpha"), the following features should be implemented (in no particular order):

- Main menu, where you can change window resolution and music/sfx volume, rebind keys and select size of map to play on
- Restart menu, shown on player's death, that resets scene and makes you play again.
- Simple leaderboard menu where you can see your previous high scores
- Placeholder birth and death animations
- Save/load settings into custom Config.prc located in `$HOME/.config/a2s3/config.prc`
- Score multiplier. The more player kills without taking damage - the higher it gets
- Spawn enemies in waves, instead of one at a time. Amount of enemies per wave should increase progressively
- At least 2 types of enemy: chaser (implemented) and turret/ranger (unimplemented)
- At least one item to pickup (med kit/health potion)
- Basic charge meter. The more you hit enemy - the higher charge meter gets (up to 100).
- At least 2 player's attacks: basic (implemented) and charge-based (require certain amount of charge points to be used)
- Basic in-game UI that show player's hp, charge, score, score multiplier and number of current wave. Maybe also amount of damage dealt/received and amount of enemies left to clear the wave

## License:

*Not yet*
