*This started as personal challenge to write something that may, even remotely, count as game. In one month*

# a2s3

## Description:

**a2s3** is work-in-progress action arena game, written in python + panda3d. For now there is not much to do, but the goal is to make a survival wave-based arena, where you fight hordes of enemies in order to get to the top of leaderboard.

## Project's Status:

**Early pre-alpha**

## Dependencies:

- python 3.9+
- panda3d 1.10.8

## How to Play:

- Install all dependencies (no setup.py available yet)
- [Download game's assets](https://i.fiery.me/b2dyt.zip) and unpack them to game's folder
- Run `./play`

## Compiling natively for your platform:

*Not yet*

## TODO:

In order to reach 0.1 milestone (effectively an equal to "alpha"), the following features should be implemented (in no particular order):

- Main menu, where you can change window resolution and music/sfx volume, rebind keys and select size of map to play on
- Restart menu, shown on player's death, that ~~show your score~~ and has buttons to reset the map, exit to main menu and ~~leave the game~~
- Simple leaderboard menu where you can see your previous high scores
- Placeholder birth and death animations
- Save/load settings into custom Config.prc located in `$HOME/.config/a2s3/config.prc`
- Spawn enemies in waves, instead of one at a time. Amount of enemies per wave should increase progressively
- At least 2 types of enemy: ~~chaser~~ and turret/ranger
- At least one item to pickup (med kit/health potion)
- Basic charge meter. The more you hit enemy - the higher charge meter gets (up to 100).
- At least 2 player's attacks: ~~basic~~ and charge-based (require certain amount of charge points to be used)
- Ability to roll
- Basic in-game UI that show ~~player's hp~~, charge, ~~score, score multiplier~~ and number of current wave. Maybe also amount of damage dealt/received and amount of enemies left to clear the wave
- Maybe something like force field appearing around character on getting damage (like in dead cells), to avoid enemies endlessly pushing you into the wall and causing screen shake
- Maybe ability to overcharge basic attack by holding down the button (like knights/archers in king arthur's gold work), coz its fun
- Maybe move hitboxes under the legs of characters (e.g to some sort of "shadow") and reshape them to be ovals or rectangles, to make combat feel the same regardless of camera angle
- Maybe make camera angle adjustable in game (with mouse wheel or something, between some degrees)
- Custom font for UI and separate track for in-game music and main menu

## License:

**Code**: [GPLv3](LICENSE)

**Assets**: whatever else, see `resources.txt` inside assets archive for info about particular license of each file
