from ai_players.ai_base import BaseAI
import pygame
import random


class AIPlayer(BaseAI):
    def __init__(self, max_speed=3+0, accel=0.1+0.2, radius=10+17):
        super().__init__(
            name="alfbot",
            max_speed=max_speed,
            accel=accel,
            radius=radius,
            color=(38, 235, 146),
        )
        self.last_charge = 0
        self.charge_cooldown = 0
        self.goal_sum = 0
        self.last_goal_time = 0

    def move(self, player, opponent, puck, game_state):
        """
        Return thrust (0-1) and angle (degrees)
        """
        game_time = pygame.time.get_ticks() / 1000
        thrust = 1
        angle = 0.0
        goal_sum = game_state["score_left"] + game_state["score_right"]

        if goal_sum - self.goal_sum > 0:
            self.goal_sum = goal_sum
            self.last_goal_time = game_time

        if game_state["side"] == "left":
            t = (0 - puck.pos[0]) / (puck.vel[0] + 0.001)
            help_position = puck.pos + t * puck.vel
            if game_time - self.last_goal_time < 1:
                to_puck = puck.pos - player.pos
                angle = to_puck.angle_to(pygame.Vector2(1, 0))
            elif puck.vel[0] < 0 and 100 <= help_position[1] <= 300:
                direction = help_position - player.pos
                angle = direction.angle_to(pygame.Vector2(1, 0))
            elif puck.pos[0] < 300 and puck.vel.length() < 2:
                goal_position = pygame.Vector2(0, 200)
                target_position = puck.pos
                direction = target_position - player.pos
                angle = direction.angle_to(pygame.Vector2(1, 0))        
            else:
                goal_position = pygame.Vector2(0, 200)
                target_position = puck.pos + 0.5 * (goal_position - puck.pos)
                target_position[0] = 50
                direction = target_position - player.pos
                angle = direction.angle_to(pygame.Vector2(1, 0))
        else:
            t = (800 - puck.pos[0]) / (puck.vel[0] + 0.001)
            help_position = puck.pos + t * puck.vel
            if game_time - self.last_goal_time < 1:
                to_puck = puck.pos - player.pos
                angle = to_puck.angle_to(pygame.Vector2(1, 0))
            elif puck.vel[0] > 0 and 100 <= help_position[1] <= 300:
                direction = help_position - player.pos
                angle = direction.angle_to(pygame.Vector2(1, 0))
            elif puck.pos[0] > 500 and puck.vel.length() < 2:
                goal_position = pygame.Vector2(800, 200)
                target_position = puck.pos
                direction = target_position - player.pos
                angle = direction.angle_to(pygame.Vector2(1, 0))        
            else:
                goal_position = pygame.Vector2(800, 200)
                target_position = puck.pos + 0.5 * (goal_position - puck.pos)
                target_position[0] = 750
                direction = target_position - player.pos
                angle = direction.angle_to(pygame.Vector2(1, 0))

        # Base behavior: move toward puck
        #to_puck = puck.pos - player.pos
        #if to_puck.length() > 0:
        #    angle = to_puck.angle_to(pygame.Vector2(1, 0))


        # Occasionally charge toward puck or opponent
        #if now - self.last_charge > self.charge_cooldown and random.random() < 0.02:
        #    self.last_charge = now
        #    self.charge_cooldown = random.uniform(2, 4)
        #    thrust = 1.0
        #    target = puck.pos if random.random() < 0.8 else opponent.pos
        #    to_target = target - player.pos
        #    if to_target.length() > 0:
        #        angle = to_target.angle_to(pygame.Vector2(1, 0))

        # Stay away from walls a bit
        #margin = 40
        #if player.pos.y < margin:
        #    angle = 270
        #elif player.pos.y > 400 - margin:
        #    angle = 90

        return thrust, angle
