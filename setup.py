from setuptools import setup
from os.path import join

setup(
    name = "A2S3",
    options = {
        "build_apps": {
            # Build game as a GUI application
            "gui_apps": {
                "A2S3": join("Game", "play.py"),
            },

            "log_filename": "log.txt",
            "log_append": False,

            "include_patterns": [
                "Assets/**",
            ],

            "plugins": [
                "pandagl",
                "p3openal_audio",
            ],
        }
    }
)
