class BaseAI:
    def __init__(self, name, max_speed, accel, radius, color):
        self.name = name
        self.max_speed = max_speed
        self.accel = accel
        self.radius = radius
        self.color = color

    def get_agent_attributes(self):
        return {
            "name": self.name,
            "max_speed": self.max_speed,
            "accel": self.accel,
            "radius": self.radius,
            "color": self.color,
        }

    def move(self, player, opponent, puck, game_state):
        """
        Returns:
            (thrust, angle)
            - thrust: float between 0 and 1 (how much of accel to apply)
            - angle: float (degrees, 0 = right, 90 = down, 180 = left, 270 = up)
        """
        raise NotImplementedError("AI must implement move() returning (thrust, angle)")
