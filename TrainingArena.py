import os
import importlib
from simulate_games import simulate_matches


ai_folder = "ai_players"

ai_files = [
    f[:-3]
    for f in os.listdir(ai_folder)
    if f.endswith(".py")
    and f not in ("__init__.py", "ai_base.py", "my_ai.py")
]

ai_classes = {}

for file in ai_files:
    module = importlib.import_module(f"{ai_folder}.{file}")

    ai_classes[file] = next(
        obj for obj in vars(module).values()
        if isinstance(obj, type) and obj.__module__ == module.__name__
    )

"""
Use ai_classes dictionary to access the AI classes.
For example, to access RoboRusher (aggresive_ai.py), you can do:

robo_rusher = ai_classes["aggresive_ai"]()  # Create an instance of RoboRusher
"""

base_robo_rusher = ai_classes["aggresive_ai"](max_speed=3 + 15 / 3,
                                              accel=0.1 + 7 / 30,
                                              radius=10 + 18 / 2,
                                              )  # Replace "aggresive_ai" with the name of the AI class you want to use for the left player

quick_robo_rusher = ai_classes["aggresive_ai"](max_speed=3 + 20 / 3,
                                              accel=0.1 + 15 / 30,
                                              radius=10 + 5 / 2,
                                              )  # Replace "aggresive_ai" with the name of the AI class you want to use for the right player

results = simulate_matches(ai_left=base_robo_rusher,
                           ai_right=quick_robo_rusher,
                           num_matches=10,
                           info=True,
                           )
