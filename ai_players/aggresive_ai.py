from ai_players.ai_base import BaseAI
import pygame
import random


class AIPlayer(BaseAI):
    def __init__(self, max_speed=7.5, accel=0.5, radius=17):
        super().__init__(
            name="RoboRusher",
            max_speed=max_speed,
            accel=accel,
            radius=radius,
            color=(255, 60, 60),
        )
        self.last_charge = 0
        self.charge_cooldown = 0

    def move(self, player, opponent, puck, game_state):
        """
        Return thrust (0-1) and angle (degrees)
        """
        now = pygame.time.get_ticks() / 1000
        thrust = 0.8
        angle = 0.0

        # Base behavior: move toward puck
        to_puck = puck.pos - player.pos
        if to_puck.length() > 0:
            angle = to_puck.angle_to(pygame.Vector2(1, 0))

        # Occasionally charge toward puck or opponent
        if now - self.last_charge > self.charge_cooldown and random.random() < 0.02:
            self.last_charge = now
            self.charge_cooldown = random.uniform(2, 4)
            thrust = 1.0
            target = puck.pos if random.random() < 0.8 else opponent.pos
            to_target = target - player.pos
            if to_target.length() > 0:
                angle = to_target.angle_to(pygame.Vector2(1, 0))

        # Stay away from walls a bit
        margin = 40
        if player.pos.y < margin:
            angle = 270
        elif player.pos.y > 400 - margin:
            angle = 90

        return thrust, angle
