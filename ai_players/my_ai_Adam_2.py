from ai_players.ai_base import BaseAI
import pygame
import math


# Constants duplicated from Klonk.py (environment assumptions)
WIDTH = 800
HEIGHT = 400
GOAL_WIDTH = 200
GOAL_Y_CENTER = HEIGHT / 2
GOAL_HALF = GOAL_WIDTH / 2
ENERGY_THRESHOLD = 4000  # for stun estimation


class AIPlayer(BaseAI):
    """
    Tournament-focused Klonk AI.
    Uses a state/utility hybrid controller with puck prediction,
    goal-aware defense, and basic stun (klonk) awareness.
    """

    def __init__(self):
        # Public attributes used by Klonk.py when instantiating the agent
        self.name = "KlonkTournamentPro2"
        self.max_speed = 8.0
        self.accel = 0.4
        self.radius = 18.0
        # High-contrast cyan-ish color
        self.color = (30, 255, 200)

        # --- Tunable behavior parameters ---

        # Defensive positioning
        self.defense_depth = 90.0  # distance in front of own goal to hold line
        self.defense_soft_radius = 40.0

        # Puck interception / prediction
        self.puck_prediction_frames = 18  # ~0.3 s at 60 FPS
        self.puck_prediction_dampen = 0.7

        # Shooting / attacking
        self.shot_approach_extra = 6.0  # extra distance behind puck
        self.behind_puck_margin = 8.0

        # Movement / thrust control
        self.max_thrust = 1.0
        self.close_slowdown_dist = 40.0
        self.brake_speed_ratio = 0.5

        # Klonk / stun heuristics
        self.klonk_distance_buffer = 4.0
        self.klonk_energy_factor = 0.8  # be conservative vs exact threshold

    # ------------------------------------------------------------------
    # Engine integration helpers
    # ------------------------------------------------------------------
    def get_agent_attributes(self):
        return {
            "name": self.name,
            "max_speed": self.max_speed,
            "accel": self.accel,
            "radius": self.radius,
            "color": self.color,
        }

    # ------------------------------------------------------------------
    # Geometry / math helpers
    # ------------------------------------------------------------------
    @staticmethod
    def clamp(value, lo, hi):
        return lo if value < lo else hi if value > hi else value

    def clamp_point_to_rink(self, pos, radius):
        """Clamp a Vector2 position so the circle stays inside the rink."""
        x = self.clamp(pos.x, radius + 2.0, WIDTH - radius - 2.0)
        y = self.clamp(pos.y, radius + 2.0, HEIGHT - radius - 2.0)
        return pygame.math.Vector2(x, y)

    def vector_to_angle(self, vec):
        """
        Convert a direction vector to engine angle.
        Engine uses direction = Vector2(1, 0).rotate(-angle).
        So angle must be -base.angle_to(vec).
        """
        if vec.length_squared() == 0:
            return 0.0
        base = pygame.math.Vector2(1, 0)
        theta = base.angle_to(vec)  # degrees
        return -theta

    # ------------------------------------------------------------------
    # Game awareness helpers
    # ------------------------------------------------------------------
    def side_params(self, game_state):
        side = game_state.get("side", "left")
        if side == "left":
            my_goal_x = 0.0
            opp_goal_x = float(WIDTH)
            attack_sign = 1.0
            my_score = game_state.get("score_left", 0)
            opp_score = game_state.get("score_right", 0)
        else:
            my_goal_x = float(WIDTH)
            opp_goal_x = 0.0
            attack_sign = -1.0
            my_score = game_state.get("score_right", 0)
            opp_score = game_state.get("score_left", 0)

        goal_center = pygame.math.Vector2(my_goal_x, GOAL_Y_CENTER)
        opp_goal_center = pygame.math.Vector2(opp_goal_x, GOAL_Y_CENTER)
        return side, attack_sign, goal_center, opp_goal_center, my_score, opp_score

    def predict_puck_position(self, puck):
        """
        Simple short-horizon puck prediction.
        Assumes quasi-constant velocity, dampened to account for friction.
        """
        vel = puck.vel
        # small heuristic horizon (in frames) scaled by damp factor
        factor = self.puck_prediction_frames * self.puck_prediction_dampen
        predicted = puck.pos + vel * factor
        return self.clamp_point_to_rink(predicted, puck.radius)

    def compute_defense_point(self, goal_center, puck_pos):
        """
        Stand on the line from our goal to puck, at a fixed depth.
        This blocks direct shots and recenters us after saves.
        """
        direction = puck_pos - goal_center
        if direction.length_squared() == 0:
            # default straight out along x
            direction = pygame.math.Vector2(1.0, 0.0)
        else:
            direction = direction.normalize()
        target = goal_center + direction * self.defense_depth
        return self.clamp_point_to_rink(target, self.radius)

    def compute_shot_approach_point(
        self, puck_pos, opp_goal_center, player_radius, puck_radius
    ):
        """
        Compute a point behind the puck relative to opponent goal,
        so that skating through that point tends to shoot towards goal.
        """
        shot_dir = opp_goal_center - puck_pos
        if shot_dir.length_squared() == 0:
            shot_dir = pygame.math.Vector2(1.0, 0.0)
        else:
            shot_dir = shot_dir.normalize()
        back_dist = player_radius + puck_radius + self.shot_approach_extra
        target = puck_pos - shot_dir * back_dist
        return self.clamp_point_to_rink(target, player_radius)

    def compute_midfield_position(self, goal_center, puck_pos):
        """
        Neutral positioning: between goal and puck, slightly biased to center.
        """
        to_puck = puck_pos - goal_center
        # bias factor: 0 -> at goal, 1 -> at puck
        bias = 0.55
        target = goal_center + to_puck * bias
        # pull slightly toward vertical center to avoid hugging top/bottom too much
        target.y = (target.y * 0.3) + (GOAL_Y_CENTER * 0.7)
        return self.clamp_point_to_rink(target, self.radius)

    # ------------------------------------------------------------------
    # Klonk / stun estimation
    # ------------------------------------------------------------------
    def estimate_klonk(self, player, opponent):
        """
        Roughly estimate whether an imminent collision would likely trigger a stun,
        and if so, whether it favors us or the opponent.

        Returns: (risk_level, favorable_for_us)
            risk_level: 0 (no serious klonk risk) or 1 (significant)
        """
        delta_pos = opponent.pos - player.pos
        dist = delta_pos.length()
        if dist == 0:
            return 0, False

        contact_dist = player.radius + opponent.radius + self.klonk_distance_buffer
        if dist > contact_dist:
            return 0, False

        unit_normal = delta_pos / dist
        v1n = player.vel.dot(unit_normal)
        v2n = opponent.vel.dot(unit_normal)
        delta_v = v1n - v2n

        m1 = player.mass
        m2 = opponent.mass
        if m1 + m2 == 0:
            return 0, False

        reduced_mass = (m1 * m2) / (m1 + m2)
        energy_transfer = 0.5 * reduced_mass * (delta_v**2)

        if energy_transfer < self.klonk_energy_factor * ENERGY_THRESHOLD:
            return 0, False

        mom1 = m1 * abs(v1n)
        mom2 = m2 * abs(v2n)
        # Engine stuns the one with smaller m*|v_n|
        if mom1 < mom2:
            # we are more likely to be stunned
            return 1, False
        else:
            return 1, True

    def avoid_head_on(self, player, opponent, desired_dir):
        """
        Adjust desired_dir to avoid a dangerous head-on collision.
        Slide tangentially relative to opponent.
        """
        normal = opponent.pos - player.pos
        if normal.length_squared() == 0:
            return desired_dir

        unit_normal = normal.normalize()
        # Remove component along normal
        tangential = desired_dir - unit_normal * desired_dir.dot(unit_normal)
        if tangential.length_squared() == 0:
            # pick a perpendicular direction
            tangential = pygame.math.Vector2(-unit_normal.y, unit_normal.x)
        return tangential.normalize()

    # ------------------------------------------------------------------
    # Main decision function
    # ------------------------------------------------------------------
    def move(self, player, opponent, puck, game_state):
        """
        Core AI logic: choose thrust and angle every frame.
        """
        # Unpack common values
        side, attack_sign, goal_center, opp_goal_center, my_score, opp_score = (
            self.side_params(game_state)
        )
        time_remaining = game_state.get("time_remaining", 0)

        pos = player.pos
        opp_pos = opponent.pos
        puck_pos = puck.pos
        puck_vel = puck.vel

        # Basic metrics
        dist_to_puck = (puck_pos - pos).length()
        dist_opp_to_puck = (puck_pos - opp_pos).length()

        puck_in_our_half = (
            (puck_pos.x < WIDTH / 2.0) if side == "left" else (puck_pos.x > WIDTH / 2.0)
        )
        puck_in_goal_band = abs(puck_pos.y - GOAL_Y_CENTER) < (GOAL_HALF + 40.0)
        puck_close_x = abs(puck_pos.x - goal_center.x) < 220.0

        if side == "left":
            vel_towards_us = puck_vel.x < -1.0
        else:
            vel_towards_us = puck_vel.x > 1.0

        danger_score = 0
        if puck_in_our_half:
            danger_score += 1
        if puck_close_x:
            danger_score += 1
        if puck_in_goal_band:
            danger_score += 1
        if vel_towards_us:
            danger_score += 1

        urgent_defense = danger_score >= 2

        # Aggressiveness based on score and time
        score_diff = my_score - opp_score
        aggressive = 1.0
        if score_diff < 0:
            aggressive = 1.2
            if time_remaining < 30:
                aggressive = 1.5
        elif score_diff > 0:
            aggressive = 0.85
            if time_remaining < 30:
                aggressive = 0.7

        late_and_behind = time_remaining < 20 and score_diff < 0

        # Possession and shot geometry
        have_puck = dist_to_puck < (player.radius + puck.radius + 4.0)
        behind_margin = player.radius + self.behind_puck_margin

        if side == "left":
            behind_puck_for_shot = pos.x < puck_pos.x - behind_margin
        else:
            behind_puck_for_shot = pos.x > puck_pos.x + behind_margin

        puck_on_goal_line = abs(puck_pos.y - GOAL_Y_CENTER) < (GOAL_HALF - 5.0)

        # State selection
        mode = "NEUTRAL"
        target = None

        if urgent_defense and not late_and_behind:
            mode = "DEFEND_GOAL"
            target = self.compute_defense_point(goal_center, puck_pos)
        elif behind_puck_for_shot and (
            puck_in_our_half or puck_on_goal_line or late_and_behind
        ):
            mode = "ATTACK_SHOT"
            target = self.compute_shot_approach_point(
                puck_pos, opp_goal_center, player.radius, puck.radius
            )
        elif puck_in_our_half or dist_to_puck < dist_opp_to_puck * 1.1:
            mode = "INTERCEPT"
            predicted = self.predict_puck_position(puck)
            target = predicted
        else:
            mode = "POSITION"
            target = self.compute_midfield_position(goal_center, puck_pos)

        # Ensure we stay inside rink
        target = self.clamp_point_to_rink(target, player.radius)

        # Desired direction
        desired_dir = target - pos
        distance_to_target = desired_dir.length()
        if distance_to_target > 1e-5:
            desired_dir /= distance_to_target
        else:
            desired_dir = pygame.math.Vector2(0.0, 0.0)

        # If we already have puck in an attacking mode, steer through goal
        if have_puck and mode in ("ATTACK_SHOT", "INTERCEPT"):
            desired_dir = opp_goal_center - puck_pos
            if desired_dir.length_squared() > 0:
                desired_dir = desired_dir.normalize()

        # Basic thrust control
        thrust = self.max_thrust

        # Slow down when close to positional targets (especially on defense)
        if (
            mode in ("DEFEND_GOAL", "POSITION")
            and distance_to_target < self.close_slowdown_dist
        ):
            thrust *= 0.5
            # Prefer braking if we're already going too fast
            if player.vel.length() > player.max_speed * self.brake_speed_ratio:
                brake_dir = -player.vel
                if brake_dir.length_squared() > 0:
                    desired_dir = brake_dir.normalize()

        # Klonk awareness
        risk_level, favorable = self.estimate_klonk(player, opponent)

        if risk_level and not favorable and score_diff > 0 and not late_and_behind:
            # Avoid dangerous collisions when leading
            desired_dir = self.avoid_head_on(player, opponent, desired_dir)
        elif risk_level and favorable and (score_diff <= 0 or late_and_behind):
            # When behind, allow beneficial collisions (no special change needed)
            pass

        # If direction is zero (rare), just don't thrust
        if desired_dir.length_squared() == 0:
            return 0.0, 0.0

        # Convert direction to engine angle
        angle = self.vector_to_angle(desired_dir)

        # Final thrust with aggressiveness scaling
        thrust *= aggressive
        if thrust > 1.0:
            thrust = 1.0
        if thrust < 0.0:
            thrust = 0.0

        return float(thrust), float(angle)
