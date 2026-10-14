from ai_players.ai_base import BaseAI
import pygame
import random

# max_speed=7.5, accel=0.5, radius=17
attr_cost = {"max_speed": 3.0, "accel": 30.0, "radius": 2.0}
budget = 73.0 * 40/41
budget_spending = {"max_speed": 13, "accel": 7, "radius": 80}

def find_attr_value(attr_name):
    total_weight = sum(budget_spending.values()) # will be 100

    if attr_name not in budget_spending: # safety check
        return 0

    spending_percentage = budget_spending[attr_name] / total_weight # 0-1, correct
    allocated_budget = budget * spending_percentage # amount of budget for this attr
    return allocated_budget / attr_cost[attr_name] 


class AIPlayer(BaseAI):
    def __init__(self, max_speed=None, accel=None, radius=None):
        # Fyll automatiskt i värden om de inte ges
        max_speed = max_speed if max_speed is not None else find_attr_value("max_speed")
        accel     = accel     if accel     is not None else find_attr_value("accel")
        radius    = radius    if radius    is not None else find_attr_value("radius")

        # Spara dem på objektet
        self.max_speed = max_speed
        self.accel     = accel
        self.radius    = radius

        # Skicka vidare de korrekta värdena till BaseAI
        super().__init__(
            name="YourMother",
            max_speed=max_speed,
            accel=accel,
            radius=radius,
            color=(255, 30, 255),
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
