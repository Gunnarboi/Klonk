from ai_players.ai_base import BaseAI
import pygame
import random

default_genome = [0.04037176038200535, 0.4057009957695384, 0.047493009209808076, 0.5947639379053704, 0.21545203825101916, 0.7932084868012129, 0.37614492440994374, 0.6508711852743506]

class AIPlayer(BaseAI):
    def __init__(self, genome=None):
        if genome is None:
            genome = default_genome
        self.genome = genome

        x1, x2, x3 = genome[:3]
        total = x1 + x2 + x3
        alpha = 40 / total if total > 0 else 1
        max_speed = 3 + (x1 * alpha) / 3
        accel     = 0.1 + (x2 * alpha) / 30
        radius    = 10 + (x3 * alpha) / 2

        super().__init__(
            name="Myggan",
            max_speed=max_speed,
            accel=accel,
            radius=radius,
            color=(60, 200, 60),
        )

        self.behind_puck_mode = False  # NEW: track if we are in behind-puck mode
        self.last_reset_time = 0
        self.prev_score = (0, 0)
        self.last_charge = 0
        self.charge_cooldown = 0

    def move(self, player, opponent, puck, game_state):
        now = pygame.time.get_ticks() / 1000
        thrust = 1.0
        angle = 0.0

        # --- Initialize tracking attributes ---
        if not hasattr(self, 'last_reset_time'):
            self.last_reset_time = now
        if not hasattr(self, 'prev_score'):
            self.prev_score = (game_state['score_left'], game_state['score_right'])

        # --- Detect goal reset ---
        current_score = (game_state['score_left'], game_state['score_right'])
        if current_score != self.prev_score:
            self.last_reset_time = now
            self.prev_score = current_score

        # --- Early defensive adjustment ---
        if now - self.last_reset_time < 1.5:
            defensive_distance = 80 + self.genome[5] * 60
            own_goal = pygame.Vector2(0, 200) if game_state['side'] == 'left' else pygame.Vector2(800, 200)
            puck_to_goal = (puck.pos - own_goal).normalize() if (puck.pos - own_goal).length() > 0 else pygame.Vector2(1,0)
            block_pos = own_goal + puck_to_goal * defensive_distance
            target_vec = block_pos - player.pos
            if target_vec.length() > 0:
                angle = target_vec.angle_to(pygame.Vector2(1, 0))
                thrust = 0.5
            return thrust, angle
        


        # --- Define key positions ---
        goal_pos = pygame.Vector2(800, 200) if game_state['side'] == 'left' else pygame.Vector2(0, 200)
        own_goal = pygame.Vector2(0, 200) if game_state['side'] == 'left' else pygame.Vector2(800, 200)
        to_goal_from_ai = goal_pos - player.pos
        to_puck_from_ai = puck.pos - player.pos
        to_goal_from_puck = goal_pos - puck.pos
        puck_to_own_goal = puck.pos - own_goal

        # --- Compute behind-puck position ---
        puck_dir = to_goal_from_puck.normalize() if to_goal_from_puck.length() > 0 else pygame.Vector2(1,0)
        behind_distance = 20 + self.genome[5]*30

        # --- OVERRIDE: If puck dangerously close to own goal, retreat first ---
        if puck_to_own_goal.length() < 150:
            retreat_distance = 50 + self.genome[5]*30
            safe_spot = own_goal + (puck.pos - own_goal).normalize() * retreat_distance
            move_vec = safe_spot - player.pos
            if move_vec.length() > 0:
                angle = move_vec.angle_to(pygame.Vector2(1, 0))
                thrust = 1.0
            return thrust, angle  # override everything else until in safe spot

        vertical_margin = 30
        distance_to_puck = (puck.pos - player.pos).length()
        if distance_to_puck < 70:  # only if puck is close
            # compute horizontal offset toward puck
            x_offset = puck.pos.x - player.pos.x  # move slightly forward/back toward puck
            x_offset *= 0.3  # scale down so mostly vertical

            if puck.pos.y < vertical_margin:
                # move mostly to top, with slight forward/back component
                move_vec = pygame.Vector2(player.pos.x + x_offset, 0) - player.pos
                if move_vec.length() > 0:
                    angle = move_vec.angle_to(pygame.Vector2(1, 0))
                    thrust = 1.0
                    return thrust, angle
            elif puck.pos.y > 400 - vertical_margin:
                # move mostly to bottom, with slight forward/back component
                move_vec = pygame.Vector2(player.pos.x + x_offset, 400) - player.pos
                if move_vec.length() > 0:
                    angle = move_vec.angle_to(pygame.Vector2(1, 0))
                    thrust = 1.0
                    return thrust, angle




        # # Increase behind distance if puck is near own goal
        # if puck_to_own_goal.length() < 150:
        #     behind_distance += 40 + self.genome[5]*20

        # Smooth curve offset when puck is very close to own goal
        curve_offset = pygame.Vector2(0,0)
        if puck_to_own_goal.length() < 100:  # very close
            side = 1 if player.pos.y < puck.pos.y else -1  # choose side to go around puck
            curve_offset = pygame.Vector2(0, side * 40)  # move vertically around puck

        behind_point = puck.pos - puck_dir * behind_distance + curve_offset
        to_behind = behind_point - player.pos
        to_puck = puck.pos - player.pos

        # --- Decide movement strategy ---
        if to_behind.length() > 5 and to_puck.dot(puck_dir) < 10:
            # Move behind the puck with curve if needed
            move_vec = behind_point - player.pos
            if move_vec.length() > 0:
                angle = move_vec.angle_to(pygame.Vector2(1,0))
                thrust = 1.0
        elif to_puck.length() < 50:
            # Close enough: go directly to puck to hit/shoot
            angle = to_puck.angle_to(pygame.Vector2(1,0))
            thrust = 1.0
        else:
            # Default: push puck toward goal
            angle = to_goal_from_ai.angle_to(pygame.Vector2(1,0))
            thrust = 1.0

        # --- Defensive positioning ---
        defensive_distance = 100 + self.genome[5] * 60
        puck_to_goal = (puck.pos - own_goal).normalize() if (puck.pos - own_goal).length() > 0 else pygame.Vector2(1,0)
        block_pos = own_goal + puck_to_goal * defensive_distance
        if not opponent.stunned and (puck.pos - own_goal).length() < 150:
            target_vec = block_pos - player.pos
            if target_vec.length() > 0:
                angle = target_vec.angle_to(pygame.Vector2(1,0))
                thrust = 1.0

        # --- Keep inside vertical field ---
        margin = 35
        if player.pos.y < margin:
            angle = 270
            thrust = 0.7
        elif player.pos.y > 400 - margin:
            angle = 90
            thrust = 0.7

        # --- Don't move if stunned ---
        if player.stunned:
            return 0.0, angle

        return thrust, angle






