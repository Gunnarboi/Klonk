import time
from utils.constants import *


# --- Classes ---
class Circle:
    def __init__(self, x, y, radius, color, max_speed=8, accel=0.5):
        self.pos = pygame.Vector2(x, y)
        self.vel = pygame.Vector2(0, 0)
        self.radius = radius
        self.base_color = color
        self.color = color
        self.max_speed = max_speed
        self.accel = accel
        self.mass = self.radius**2
        self.frames_stunned = 0

    @property
    def stunned(self):
        return self.frames_stunned > 0

    def stun(self):
        self.frames_stunned = int(STUN_DURATION * FPS)

    def move(self):
        self.pos += self.vel
        self.vel *= FRICTION
        if self.vel.length() > self.max_speed:
            self.vel.scale_to_length(self.max_speed)

        # Wall collisions
        if self.pos.x - self.radius < 0:
            self.pos.x = self.radius
            self.vel.x *= -1
        elif self.pos.x + self.radius > WIDTH:
            self.pos.x = WIDTH - self.radius
            self.vel.x *= -1
        if self.pos.y - self.radius < 0:
            self.pos.y = self.radius
            self.vel.y *= -1
        elif self.pos.y + self.radius > HEIGHT:
            self.pos.y = HEIGHT - self.radius
            self.vel.y *= -1

        # Color when stunned
        if self.stunned:
            self.color = tuple(max(0, min(255, c - 70)) for c in self.base_color)
        else:
            self.color = self.base_color

    def draw(self, offset_x=0, offset_y=0):
        pygame.draw.circle(
            SCREEN,
            self.color,
            (int(self.pos.x + offset_x), int(self.pos.y + offset_y)),
            self.radius,
        )


class Puck(Circle):
    def __init__(self, x, y, radius=10, color=BLACK):
        super().__init__(x, y, radius, color, max_speed=15, accel=0)

    def move(self):
        self.pos += self.vel
        self.vel *= PUCK_FRICTION
        # Wall collisions
        if self.pos.x - self.radius < 0:
            self.pos.x = self.radius
            self.vel.x *= -1
        elif self.pos.x + self.radius > WIDTH:
            self.pos.x = WIDTH - self.radius
            self.vel.x *= -1
        if self.pos.y - self.radius < 0:
            self.pos.y = self.radius
            self.vel.y *= -1
        elif self.pos.y + self.radius > HEIGHT:
            self.pos.y = HEIGHT - self.radius
            self.vel.y *= -1
