from ai_players.ai_base import BaseAI
import pygame

"""
Make your own AI by editing this file!

To make your bot appear in the game, you must first change the name of this file to something other than "my_ai.py".
The move() function is called every frame and is where you will implement your bot's logic.
REMEMBER: All vectors (i.e. positions and velocities) are in the format (x, y) where x increases to the right and y increases downward.
"""
class AIPlayer(BaseAI):
    def __init__(
        self,
        name="Enter bot name here",     # Name your bot! This will be displayed on the scoreboard!
        max_speed=3 + 15 / 3,           # Base skill plus added skill
        accel=0.1 + 7 / 30,             # Pro tip: write your bot's skill in this format
        radius=10 + 18 / 2,             # Just make sure the numerators of all skill values sum to at most 40
        color=(255, 100, 100),          # RGB color of your bot (red, green, blue)
    ):
        self.name = name
        self.max_speed = max_speed
        self.accel = accel
        self.radius = radius
        self.color = color

    def move(self, player, opponent, puck, game_state):
        """
        Determine the next move for the AI player.

        Each frame, this function is called with the current state of the game. The AI should return thrust and angle where:
            - thrust: float between 0 and 1 (how much of accel to apply)
            - angle: float (degrees, 0 = right, 90 = up, 180 = left, 270 = down)

        Args:
            - player:       The AI player's current state (position, velocity, etc.). 
                            The player is a Circle object and can be further read about in utils/circles.py.
            - opponent:     The opponent player's current state.
                            The opponent is also a Circle object and can be further read about in utils/circles.py.
            - puck:         The puck's current state.
                            The puck is a Puck object and can be further read about in utils/circles.py.
            - game_state:   Dictionary with additional information about the game.
                            game_state{"score_left"} - The score of the left player
                            game_state{"score_right"} - The score of the right player
                            game_state{"time_remaining"} - The time remaining in the game (in seconds)
                            game_state{"side"} - The side the AI player is on ("left" or "right")
        """