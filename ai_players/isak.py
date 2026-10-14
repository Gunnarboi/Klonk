from ai_players.ai_base import BaseAI
import pygame
import math
import random
import numpy as np


def sigmoid(x):
    return 1.0 / (1.0 + math.exp(-x))


def tanh(x):
    return math.tanh(x)


class AIPlayer(BaseAI):
    def __init__(
        self,
        max_speed=3,
        accel=0.1,
        radius=30,
    ):
        self.name = "Newton Old"
        self.max_speed = max_speed
        self.accel = accel
        self.radius = radius
        self.color = (51, 51, 0)

        # Architecture: 12 inputs -> 14 hidden -> 8 hidden -> 2 outputs
        # layer1: 12*14 + 14 = 182
        # layer2: 14*8  + 8  = 120
        # layer3: 8*2   + 2  = 18
        # total = 320
        self.total_weights = 320

        try:
            self.Weights = np.load("./ai_players/best_weights_6.npy").tolist()
            if len(self.Weights) != self.total_weights:
                print("Saved weights size mismatch, reinitializing")
                raise ValueError
        except Exception:
            self.Weights = [random.uniform(-1, 1) for _ in range(self.total_weights)]

    def get_agent_attributes(self):
        return {
            "name": self.name,
            "max_speed": self.max_speed,
            "accel": self.accel,
            "radius": self.radius,
            "color": self.color,
        }

    def move(self, player, opponent, puck, game_state):

        # ------------------------------
        # Normalization constants
        # ------------------------------
        RINK_W = 800.0
        RINK_H = 400.0
        VMAX = 15.0

        def norm_pos_x(v):
            return (v / RINK_W) * 2 - 1

        def norm_pos_y(v):
            return (v / RINK_H) * 2 - 1

        def norm_vel(v):
            return max(-1, min(1, v / VMAX))

        side = game_state.get("side", "right")

        # ------------------------------
        # Mirror coordinates if playing on left
        # ------------------------------
        if side == "left":
            # player
            p_x = RINK_W - player.pos.x
            p_y = player.pos.y
            pv_x = -player.vel.x
            pv_y = player.vel.y

            # opponent
            o_x = RINK_W - opponent.pos.x
            o_y = opponent.pos.y
            ov_x = -opponent.vel.x
            ov_y = opponent.vel.y

            # puck
            pk_x = RINK_W - puck.pos.x
            pk_y = puck.pos.y
            pkv_x = -puck.vel.x
            pkv_y = puck.vel.y
        else:
            p_x = player.pos.x
            p_y = player.pos.y
            pv_x = player.vel.x
            pv_y = player.vel.y

            o_x = opponent.pos.x
            o_y = opponent.pos.y
            ov_x = opponent.vel.x
            ov_y = opponent.vel.y

            pk_x = puck.pos.x
            pk_y = puck.pos.y
            pkv_x = puck.vel.x
            pkv_y = puck.vel.y

        # ------------------------------
        # Normalized input vector (12 values)
        # ------------------------------
        x = [
            norm_pos_x(p_x),
            norm_pos_y(p_y),
            norm_vel(pv_x),
            norm_vel(pv_y),
            norm_pos_x(pk_x),
            norm_pos_y(pk_y),
            norm_vel(pkv_x),
            norm_vel(pkv_y),
            norm_pos_x(o_x),
            norm_pos_y(o_y),
            norm_vel(ov_x),
            norm_vel(ov_y),
        ]

        # ----------------------
        # Unpack weights
        # ----------------------
        w = self.Weights
        idx = 0

        # Layer 1: 12 -> 14
        W1 = []
        for _ in range(14):
            W1.append(w[idx : idx + 12])
            idx += 12
        b1 = w[idx : idx + 14]
        idx += 14

        # Layer 2: 14 -> 8
        W2 = []
        for _ in range(8):
            W2.append(w[idx : idx + 14])
            idx += 14
        b2 = w[idx : idx + 8]
        idx += 8

        # Layer 3: 8 -> 2
        W3 = []
        for _ in range(2):
            W3.append(w[idx : idx + 8])
            idx += 8
        b3 = w[idx : idx + 2]
        idx += 2

        # ----------------------
        # Forward pass
        # ----------------------
        def layer_forward(inputs, W, b, act):
            out = []
            for i in range(len(W)):
                s = sum(inputs[j] * W[i][j] for j in range(len(inputs))) + b[i]
                out.append(act(s))
            return out

        h1 = layer_forward(x, W1, b1, tanh)
        h2 = layer_forward(h1, W2, b2, tanh)

        o1 = sum(h2[j] * W3[0][j] for j in range(8)) + b3[0]
        o2 = sum(h2[j] * W3[1][j] for j in range(8)) + b3[1]

        thrust = sigmoid(o1)
        angle_net = sigmoid(o2) * 360.0

        if side == "left":
            angle = 180.0 - angle_net
            angle %= 360.0
        else:
            angle = angle_net

        return thrust, angle
