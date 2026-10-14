from ai_players.ai_base import BaseAI
import pygame
import random

attr_cost = {"max_speed": 3.0, "accel": 30.0, "radius": 2.0}
budget_spending = {
    "max_speed": 9 + 18.23,
    "accel": 3 + 10.6,
    "radius": 20 + 11.17,
}  # base + value


def find_attr_value(attr_name):

    if attr_name not in budget_spending:  # safety check
        return 0

    return budget_spending[attr_name] / attr_cost[attr_name]


def predict_puck_with_bounce(puck, frames_ahead):
    pos = pygame.Vector2(puck.pos)
    vel = pygame.Vector2(puck.vel)
    for _ in range(int(frames_ahead)):
        pos += vel
        vel *= 0.995  # PUCK_FRICTION from game
        if pos.y <= 0 or pos.y >= 400:
            vel.y *= -1
        # x bounces are walls, not goals — clamp loosely
        pos.y = max(0, min(400, pos.y))
    return pos


class AIPlayer(BaseAI):
    def __init__(self, max_speed=None, accel=None, radius=None):
        # Fyll automatiskt i värden om de inte ges
        max_speed = max_speed if max_speed is not None else find_attr_value("max_speed")
        accel = accel if accel is not None else find_attr_value("accel")
        radius = radius if radius is not None else find_attr_value("radius")

        # Spara dem på objektet
        self.max_speed = max_speed
        self.accel = accel
        self.radius = radius
        self.start = True
        self.home_team = True

        # Skicka vidare de korrekta värdena till BaseAI
        super().__init__(
            name="LittelSheDevil",
            max_speed=max_speed,
            accel=accel,
            radius=radius,
            color=(255, 69, 69),
        )

        self.last_charge = 0
        self.charge_cooldown = 0

    def move(self, player, opponent, puck, game_state):
        """
        Return thrust (0-1) and angle (degrees)
        """
        if self.start:
            if puck.pos.x < player.pos.x:
                self.home_team = False
        self.start = False

        now = pygame.time.get_ticks() / 1000
        thrust = 1.0
        angle = 0.0
        right_vec = pygame.Vector2(1, 0)

        # Useful vectors
        to_puck = puck.pos - player.pos
        dist_to_puck = to_puck.length()

        # ----------------------------------------------------s--------
        # PUCK PREDICTION (small lookahead)
        # ------------------------------------------------------------
        prediction_factor = 2
        predicted_puck = puck.pos + puck.vel * prediction_factor * 5

        # ------------------------------------------------------------
        # PRIO 1: DEFENSE — stay between puck and own goal (x=0)
        # ------------------------------------------------------------

        if self.home_team:
            # Are we between puck and goal?
            player_is_between = player.pos.x < puck.pos.x
            # Is the puck moving towards the goal?
            puck_moving_towards_goal = puck.vel.x < 0
        else:
            player_is_between = player.pos.x > puck.pos.x
            puck_moving_towards_goal = puck.vel.x > 0

        # If NOT between puck and goal → retreat (x-direction)
        if not player_is_between:

            thrust = 1.0

            # Basic retreat direction: go left
            if self.home_team:
                angle = 180
            else:
                angle = 0

            # Avoid colliding with puck during retreat
            if dist_to_puck < 20:
                if puck.pos.y < player.pos.y:
                    angle = 90  # up-left-ish
                else:
                    angle = 270  # down-left-ish

            # If puck is moving toward goal → intercept predicted point
            if puck_moving_towards_goal:
                intercept_vec = predicted_puck - player.pos
                if intercept_vec.length() > 0:
                    angle = intercept_vec.angle_to(right_vec)

            # Avoid walls vertically
            margin = 20
            if player.pos.y < margin:
                angle = 90
            elif player.pos.y > 400 - margin:
                angle = 270

            return thrust, angle

        # ------------------------------------------------------------
        # PRIO 2: ATTACK — we ARE between goal and puck
        # ------------------------------------------------------------

        # Predictive attack target
        # attack_target = puck.pos + puck.vel * 5
        attack_target = puck.pos + puck.vel
        to_attack = attack_target - player.pos

        if to_attack.length() > 0:
            angle = to_attack.angle_to(right_vec)

        margin = 20
        if player.pos.y < margin:
            angle = 270
        elif player.pos.y > 400 - margin:
            angle = 90

        return thrust, angle
