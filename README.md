# a2s3

[![Build](https://github.com/moonburnt/a2s3/actions/workflows/build.yml/badge.svg)](https://github.com/moonburnt/a2s3/actions/workflows/build.yml)

## Description:

**a2s3** is a simple action arena game, written in python + panda3d. There is
not much to do, but the goal was to make a survival wave-based arena, where you
fight hordes of enemies in order to get to the top of leaderboard.

## Project's Status:

**Cancelled. Feel free to fork!**

## Contributing:

This project tries to follow [PEP 8](https://www.python.org/dev/peps/pep-0008/)
for as much as possible. Since #2424156, it uses [black](https://github.com/psf/black)
for automatic code formatting. Also this project tries to follow
[Conventional Commits v1.0.0](https://www.conventionalcommits.org/en/v1.0.0/)
specification for commit messages. If you will decide to contribute, please keep
these things in mind and format related stuff accordingly.

## Dependencies:

- python 3.9+
- panda3d 1.10.8
- toml 0.10.2
- [p3dss](https://github.com/moonburnt/p3dss)
- [p3dae](https://github.com/moonburnt/p3dae)

## How to Play:

```
# Clone git repo locally
git clone https://github.com/moonburnt/a2s3.git

# Get into game's directory
cd A2S3

# Initialize and activate virtual environment
virtualenv .venv && source .venv/bin/activate

# Install all required dependencies
pip install -r requirements.txt

# Run the game
python -m Game
```

## How to Compile:

Since this is a python game, its not necessary to compile it in order to play.
However, if you want to create an executable to use on systems without python
being preinstalled - you can surely do that.

In order to achieve this, you must do all steps from "How to Play" part, except
from the last one. Then do the following:

```
python setup.py build_apps
```

If everything has been done correctly - game's binaries will be generated into
**build/{name-of-your-platform}**.

## TODO:

In order to reach 0.1 milestone (effectively an equal to "alpha"), the following
features should be implemented (in no particular order):

- Main menu, where you can change window resolution ~~and music/sfx volume~~,
  rebind keys and ~~select size of map to play on~~
- Placeholder birth and ~~death~~ animations
- Save/load settings into custom configuration file
- At least 2 types of enemy: ~~chaser~~ and turret/ranger
- At least one item to pickup (med kit/health potion)
- Basic charge meter. The more you hit enemy - the higher charge meter gets (up to 100).
- At least 2 player's attacks: ~~basic~~ and charge-based
  (require certain amount of charge points to be used)
- Ability to roll
- Maybe ability to overcharge basic attack by holding down the button
  (like knights/archers in king arthur's gold work), coz its fun
- Maybe make camera angle adjustable in game (with mouse wheel or something, between some degrees)

## License:

**Code**: [GPLv3](LICENSE)

**Assets**: whatever else, see `resources.txt` inside [assets](Assets)
for info about particular license of each file
