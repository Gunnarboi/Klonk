import pygame
import os
import importlib
import time
import random
import math

from utils.circles import Circle, Puck

# from utils import moves

RINK_WIDTH, RINK_HEIGHT = 800, 400
WINDOW_WIDTH = 1000
WINDOW_HEIGHT = 700

WIDTH = RINK_WIDTH
HEIGHT = RINK_HEIGHT

FPS = 60

# --- Colors ---
WHITE = (255, 255, 255)
BLUE = (70, 130, 180)
RED = (220, 20, 60)
BLACK = (0, 0, 0)
GREY = (230, 230, 230)
GOAL_COLOR = (200, 200, 200)
HIGHLIGHT = (255, 255, 100)
BACKGROUND_TOP = (180, 220, 255)
BACKGROUND_BOTTOM = (100, 170, 240)
DARK_BLUE = (10, 10, 30)
NEON_BLUE = (0, 255, 255)
NEON_RED = (255, 50, 50)
NEON_PURPLE = (200, 0, 255)
DARK_GREY = (50, 50, 60)
KLONK_BLUE = (0, 0, 150)
KLONK_YELLOW = (255, 255, 204)
KLONK_RED = (255, 69, 0)

FRICTION = 0.99
PUCK_FRICTION = 0.995
GOAL_WIDTH = 200
STUN_DURATION = 5.0  # seconds of stun time
GAME_DURATION = 120  # seconds
ENERGY_THRESHOLD = 4000  # energy transfer threshold for stun

# --- Attributes costs ---
start_attr = {
    "max_speed": 3.0,
    "accel": 0.1,
    "radius": 10.0,
}
attr_cost = {
    "max_speed": 3.0,
    "accel": 30.0,
    "radius": 2.0,
}
budget = 40.01
goal_effect_duration = 2  # seconds


def start_game():
    # --- Initialization ---
    pygame.init()

    global SCREEN, RINK_RECT
    SCREEN = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
    RINK_RECT = pygame.Rect(0, 0, RINK_WIDTH, RINK_HEIGHT)
    RINK_RECT.center = (WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2)

    global offset_x, offset_y
    offset_x, offset_y = RINK_RECT.left, RINK_RECT.top + 20

    pygame.display.set_caption("Air Hockey")

    global font  # , small_font
    font = pygame.font.SysFont("Arial", 48)
    # small_font = pygame.font.SysFont("Arial", 32)

    # --- Load and Play Music ---"""

    music_path = os.path.join("assets", "klonk_theme.mp3")
    pygame.mixer.init()
    pygame.mixer.music.load(music_path)
    pygame.mixer.music.set_volume(0.5)  # 0.0 to 1.0 (adjust to taste)
    pygame.mixer.music.play(-1)  # -1 means loop forever

    # --- Fonts ---
    font_path = os.path.join("assets", "fonts", "DS-DIGI.TTF")
    if not os.path.exists(font_path):
        raise FileNotFoundError(f"Font not found at {font_path}")
    # Font setup (use your DS-DIGI or similar)
    global title_font, option_font, small_font, SCOREBOARD_FONT, SMALL_SCORE_FONT
    title_font = pygame.font.Font(
        os.path.join("assets", "fonts", "PlavorRegular-nAK6R.otf"), 120
    )
    option_font = pygame.font.Font(
        os.path.join("assets", "fonts", "PlavorRegular-nAK6R.otf"), 40
    )
    small_font = pygame.font.Font(
        os.path.join("assets", "fonts", "PlavorRegular-nAK6R.otf"), 28
    )

    SCOREBOARD_FONT = pygame.font.Font(font_path, 64)  # Big LED look
    SMALL_SCORE_FONT = pygame.font.Font(font_path, 32)

    # --- AI Detection ---
    ai_folder = "ai_players"
    ai_files = [
        f[:-3]
        for f in os.listdir(ai_folder)
        if f.endswith(".py") and f not in ("__init__.py", "ai_base.py")
    ]

    global ai_options
    ai_options = []
    for f in ai_files:
        module = importlib.import_module(f"{ai_folder}.{f}")
        ai_class = getattr(module, "AIPlayer", None)
        if ai_class:
            ai_instance = ai_class()
            ai_options.append(
                {"file": f, "name": ai_instance.name}  # this uses the internal AI name
            )
    ai_options.insert(0, {"file": None, "name": "Human"})  # for human players


def load_ai(ai_option):
    if ai_option["file"] is None:
        return None  # human player
    module = importlib.import_module(f"ai_players.{ai_option['file']}")
    return module.AIPlayer()


# --- Collision Handling ---
def handle_collision(c1, c2):
    dist_vec = c1.pos - c2.pos
    dist = dist_vec.length()
    if dist < c1.radius + c2.radius:
        overlap = c1.radius + c2.radius - dist
        direction = dist_vec.normalize() if dist > 0 else pygame.Vector2(1, 0)
        total_mass = c1.mass + c2.mass
        c1.pos += direction * overlap * (c2.mass / total_mass)
        c2.pos -= direction * overlap * (c1.mass / total_mass)

        normal_vec = c1.pos - c2.pos
        if normal_vec.length() == 0:
            normal_vec = pygame.Vector2(1, 0)
        unit_normal = normal_vec.normalize()
        unit_tangent = pygame.Vector2(-unit_normal.y, unit_normal.x)

        v1n = c1.vel.dot(unit_normal)
        v1t = c1.vel.dot(unit_tangent)
        v2n = c2.vel.dot(unit_normal)
        v2t = c2.vel.dot(unit_tangent)

        m1, m2 = c1.mass, c2.mass
        v1n_final = (v1n * (m1 - m2) + 2 * m2 * v2n) / (m1 + m2)
        v2n_final = (v2n * (m2 - m1) + 2 * m1 * v1n) / (m1 + m2)

        c1.vel = v1n_final * unit_normal + v1t * unit_tangent
        c2.vel = v2n_final * unit_normal + v2t * unit_tangent

        # --- Energy-based stun logic ---
        if (
            isinstance(c1, Circle)
            and isinstance(c2, Circle)
            and not isinstance(c1, Puck)
            and not isinstance(c2, Puck)
        ):
            delta_v = v1n - v2n
            reduced_mass = (m1 * m2) / (m1 + m2)
            energy_transfer = 0.5 * reduced_mass * (abs(delta_v) ** (2))

            if energy_transfer > ENERGY_THRESHOLD:
                if m1 * abs(v1n) < m2 * abs(v2n):
                    c1.stun()
                else:
                    c2.stun()


# --- Utility ---
def reset_positions(player1, player2, puck):
    player1.pos = pygame.Vector2(150, HEIGHT // 2)
    player2.pos = pygame.Vector2(WIDTH - 150, HEIGHT // 2)
    player1.vel *= 0
    player2.vel *= 0
    y = random.choice([-1, 1]) * random.randint(1, 30)
    puck.pos = pygame.Vector2(WIDTH // 2, HEIGHT // 2 + y)
    puck.vel *= 0
    player1.frames_stunned = 0
    player2.frames_stunned = 0


def check_goal(
    puck, player1, player2, score1, score2, left_ai=None, right_ai=None, render=True
):
    is_goal = False
    if puck.pos.x - puck.radius <= 0 and (HEIGHT / 2 - GOAL_WIDTH / 2) < puck.pos.y < (
        HEIGHT / 2 + GOAL_WIDTH / 2
    ):
        score2 += 1
        is_goal = True
        (
            draw_goal_effect(right_ai if right_ai else player2, "right", score1, score2)
            if render
            else None
        )
    if puck.pos.x + puck.radius >= WIDTH and (
        HEIGHT / 2 - GOAL_WIDTH / 2
    ) < puck.pos.y < (HEIGHT / 2 + GOAL_WIDTH / 2):
        score1 += 1
        is_goal = True
        (
            draw_goal_effect(left_ai if left_ai else player1, "left", score1, score2)
            if render
            else None
        )
    if is_goal:
        reset_positions(player1, player2, puck)
    return score1, score2


# --- Start Screen ---
def start_screen():
    left_index, right_index = 0, 0
    selected = 0
    clock = pygame.time.Clock()
    t = 0

    while True:
        dt = clock.tick(60) / 1000.0
        t += dt

        # --- Animated Background ---
        SCREEN.fill(KLONK_BLUE)

        # --- Title Animation ---
        title_text = "KLONK"
        title_surf = title_font.render(title_text, True, KLONK_YELLOW)
        x = WINDOW_WIDTH // 2 - title_surf.get_width() // 2
        y = 120 + math.sin(t * 2) * 10
        # draw_glow_text(SCREEN, title_text, title_font, (x, y), NEON_BLUE, (0, 100, 255))
        SCREEN.blit(title_surf, (x, y))

        # subtitle = small_font.render("Arcade Physics Mayhem", True, DARK_GREY)
        # SCREEN.blit(subtitle, (WINDOW_WIDTH // 2 - subtitle.get_width() // 2, y + 120))

        # --- Menu Options ---
        options = [
            f"Left Player: {ai_options[left_index]['name']}",
            f"Right Player: {ai_options[right_index]['name']}",
            "Start Game",
        ]

        for i, opt in enumerate(options):
            y_pos = 350 + i * 80
            if i == selected:
                glow_col = KLONK_RED if i == 2 else KLONK_YELLOW
                pygame.draw.rect(
                    SCREEN,
                    glow_col,
                    (WINDOW_WIDTH // 2 - 220, y_pos - 10, 440, 60),
                    border_radius=2,
                )
                text_col = BLACK
            else:
                text_col = WHITE
                glow_col = DARK_GREY
            text = option_font.render(opt, True, text_col)
            SCREEN.blit(text, (WINDOW_WIDTH // 2 - text.get_width() // 2, y_pos))

        # --- Bottom hint ---
        hint = small_font.render(
            "UP/DOWN to move  •  LEFT/RIGHT to change  •  ENTER to start",
            True,
            KLONK_YELLOW,
        )
        SCREEN.blit(
            hint, (WINDOW_WIDTH // 2 - hint.get_width() // 2, WINDOW_HEIGHT - 60)
        )

        pygame.display.flip()

        # --- Input handling ---
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                exit()
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_UP:
                    selected = (selected - 1) % len(options)
                elif event.key == pygame.K_DOWN:
                    selected = (selected + 1) % len(options)
                elif event.key == pygame.K_LEFT:
                    if selected == 0:
                        left_index = (left_index - 1) % len(ai_options)
                    elif selected == 1:
                        right_index = (right_index - 1) % len(ai_options)
                elif event.key == pygame.K_RIGHT:
                    if selected == 0:
                        left_index = (left_index + 1) % len(ai_options)
                    elif selected == 1:
                        right_index = (right_index + 1) % len(ai_options)
                elif event.key == pygame.K_RETURN:
                    if selected == 0:
                        pass
                    elif selected == 1:
                        pass
                    elif selected == 2:
                        left_ai = load_ai(ai_options[left_index])
                        right_ai = load_ai(ai_options[right_index])

                    return left_ai, right_ai


def draw_scoreboard(screen, left_score, right_score, remaining_time, rink_rect):
    """Draw a retro LED scoreboard at the top center."""
    # Colors
    BLACK = (10, 10, 10)
    LIGHT_BLACK = (40, 40, 40)
    RED = (255, 60, 60)
    ORANGE = (255, 150, 50)
    YELLOW = (255, 220, 100)

    # Scoreboard dimensions
    width = 400
    height = 100
    x = rink_rect.centerx - width // 2
    y = rink_rect.top - height - 20  # just above rink

    # Draw background
    pygame.draw.rect(screen, LIGHT_BLACK, (x, y, width, height), border_radius=2)

    # Glowing outer frame
    pygame.draw.rect(
        screen,
        KLONK_RED,
        (x - 2, y - 2, width + 4, height + 4),
        width=2,
        border_radius=4,
    )

    # Compute time text
    minutes = remaining_time // 60
    seconds = remaining_time % 60
    time_text = f"{minutes:02}:{seconds:02}"

    # Render text
    time_surface = SCOREBOARD_FONT.render(time_text, True, ORANGE)
    left_score_surface = SCOREBOARD_FONT.render(str(left_score), True, YELLOW)
    right_score_surface = SCOREBOARD_FONT.render(str(right_score), True, YELLOW)

    # Position elements
    screen.blit(left_score_surface, (x + 40, y + 20))
    screen.blit(time_surface, (x + width // 2 - time_surface.get_width() // 2, y + 20))
    screen.blit(
        right_score_surface, (x + width - right_score_surface.get_width() - 40, y + 20)
    )

    # Optional small labels
    left_label = SMALL_SCORE_FONT.render("P1", True, ORANGE)
    right_label = SMALL_SCORE_FONT.render("P2", True, ORANGE)
    screen.blit(left_label, (x + 40, y + 70))
    screen.blit(right_label, (x + width - right_label.get_width() - 40, y + 70))


# --- Draw KLONK Arena ---
def draw_arena(SCREEN, offset_x, offset_y, WIDTH, HEIGHT, GOAL_WIDTH, RINK_RECT):

    # Cover the window with a dark background
    SCREEN.fill(KLONK_BLUE)

    # Draw main field (plain rectangle)
    pygame.draw.rect(SCREEN, KLONK_YELLOW, (offset_x, offset_y, WIDTH, HEIGHT))

    # Center line
    pygame.draw.line(
        SCREEN,
        WHITE,
        (offset_x + WIDTH // 2, offset_y),
        (offset_x + WIDTH // 2, offset_y + HEIGHT),
        width=2,
    )

    # Outer border (thin red frame)
    pygame.draw.rect(
        SCREEN,
        KLONK_RED,
        (offset_x - 2, offset_y - 2, WIDTH + 4, HEIGHT + 4),
        width=4,
    )

    # Goals (simple rectangles)
    pygame.draw.rect(
        SCREEN,
        WHITE,
        (offset_x, offset_y + HEIGHT / 2 - GOAL_WIDTH / 2, 10, GOAL_WIDTH),
    )
    pygame.draw.rect(
        SCREEN,
        WHITE,
        (offset_x + WIDTH - 10, offset_y + HEIGHT / 2 - GOAL_WIDTH / 2, 10, GOAL_WIDTH),
    )


def end_screen(left_ai, right_ai, score1, score2):
    clock = pygame.time.Clock()
    t = 0

    if score1 > score2:
        name = left_ai.name if hasattr(left_ai, "name") else "Player 1"
        result_text = f"{name} Wins!"
    elif score2 > score1:
        name = right_ai.name if hasattr(right_ai, "name") else "Player 2"
        result_text = f"{name} Wins!"
    else:
        result_text = f"It's a Draw!"
    score = f"{score1} - {score2}"

    while True:
        dt = clock.tick(60) / 1000.0
        t += dt

        SCREEN.fill(KLONK_RED)

        # Result Text
        result_surf = title_font.render(result_text, True, KLONK_YELLOW)
        score_surf = option_font.render(score, True, KLONK_YELLOW)
        x = WINDOW_WIDTH // 2 - result_surf.get_width() // 2
        y = WINDOW_HEIGHT // 2 - result_surf.get_height() // 2 + math.sin(t * 2) * 10
        SCREEN.blit(result_surf, (x, y))
        SCREEN.blit(
            score_surf,
            (
                WINDOW_WIDTH // 2 - score_surf.get_width() // 2,
                y + result_surf.get_height() + 10,
            ),
        )

        # Instruction to restart
        hint = small_font.render("Press ENTER to return to Menu", True, KLONK_YELLOW)
        SCREEN.blit(
            hint, (WINDOW_WIDTH // 2 - hint.get_width() // 2, WINDOW_HEIGHT - 100)
        )

        pygame.display.flip()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                exit()
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN:
                    main()  # Return to main menu


def draw_goal_effect(scoring_ai, side, score1, score2):
    """Draw a brief visual effect when a goal is scored."""
    start_time = time.time()
    # clock = pygame.time.Clock()

    while time.time() - start_time < goal_effect_duration:
        # dt = clock.tick(60) / 1000.0

        # Draw semi-transparent overlay
        overlay = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT))
        overlay.set_alpha(150)
        overlay.fill(KLONK_RED)
        SCREEN.blit(overlay, (0, 0))

        player_nr = 1 if side == "left" else 2

        # Flashing text
        flash_text = f"{scoring_ai.name if hasattr(scoring_ai, 'name') else f'Player {player_nr}'} Scores!"
        scorer_text = f"{score1}" if side == "left" else f"{score2}"
        score_text = f" - {score2}" if side == "left" else f"{score1} - "
        flash_surf = title_font.render(flash_text, True, KLONK_YELLOW)
        scorer_surf = option_font.render(scorer_text, True, KLONK_YELLOW)
        score_surf = option_font.render(score_text, True, KLONK_YELLOW)
        alpha = int(
            255 * abs(math.sin((time.time() - start_time) * 5))
        )  # oscillate alpha
        scorer_surf.set_alpha(alpha)
        x = WINDOW_WIDTH // 2 - flash_surf.get_width() // 2
        y = WINDOW_HEIGHT // 2 - flash_surf.get_height() // 2
        SCREEN.blit(flash_surf, (x, y))
        SCREEN.blit(
            scorer_surf,
            (
                WINDOW_WIDTH // 2
                - scorer_surf.get_width() // 2
                - (
                    score_surf.get_width() // 2
                    if side == "left"
                    else -score_surf.get_width() // 2
                ),
                y + flash_surf.get_height() + 10,
            ),
        )
        SCREEN.blit(
            score_surf,
            (
                WINDOW_WIDTH // 2
                - score_surf.get_width() // 2
                - (
                    -scorer_surf.get_width() // 2
                    if side == "left"
                    else scorer_surf.get_width() // 2
                ),
                y + flash_surf.get_height() + 10,
            ),
        )

        pygame.display.flip()


def menue_button():
    button_width = 120
    button_height = 40
    button_x = 20
    button_y = 20

    mouse_pos = pygame.mouse.get_pos()
    mouse_clicked = pygame.mouse.get_pressed()[0]

    button_rect = pygame.Rect(button_x, button_y, button_width, button_height)

    if button_rect.collidepoint(mouse_pos):
        color = KLONK_RED
        if mouse_clicked:
            main()  # Restart the game
    else:
        color = DARK_GREY

    pygame.draw.rect(SCREEN, color, button_rect, border_radius=5)
    text_surf = small_font.render("Menu", True, WHITE)
    text_rect = text_surf.get_rect(center=button_rect.center)
    SCREEN.blit(text_surf, text_rect)


def parameter_power(attrs):
    return sum(attr_cost[key] * (attrs[key] - start_attr[key]) for key in attr_cost)


# --- Player Creation ---
def create_agent(ai_obj, side):
    if ai_obj:
        attrs = ai_obj.get_agent_attributes()
    else:
        if side == "left":
            attrs = {
                "radius": 10 + 0 / 2,
                "max_speed": 3 + 0 / 3,
                "accel": 0.1 + 40 / 30,
                "color": (255, 0, 0),
            }
        else:
            attrs = {
                "radius": 10 + 20 / 2,
                "max_speed": 3 + 15 / 3,
                "accel": 0.1 + 5 / 30,
                "color": (0, 255, 0),
            }

    if parameter_power(attrs) > budget:
        raise ValueError(
            f"Agent on {side}, parameters exceed budget ({parameter_power(attrs):.2f})."
        )

    for key in start_attr:
        if attrs.get(key, 0) < start_attr[key]:
            raise ValueError(
                f"Agent on {side}, attribute '{key}' is below minimum allowed value ({attrs.get(key, 0)} < {start_attr[key]})."
            )
    # print(f"Creating agent on {side} with power: {parameter_power(attrs):.2f}")
    x = 150 if side == "left" else WIDTH - 150
    y = HEIGHT // 2
    return Circle(
        x, y, attrs["radius"], attrs["color"], attrs["max_speed"], attrs["accel"]
    )


# --- Main ---
def main():
    start_game()
    left_ai, right_ai = start_screen()
    player1 = create_agent(left_ai, "left")
    player2 = create_agent(right_ai, "right")
    y = random.choice([-1, 1]) * random.randint(1, 30)
    puck = Puck(WIDTH // 2, HEIGHT // 2 + y, 10, BLACK)
    score1, score2 = 0, 0

    clock = pygame.time.Clock()
    running = True
    start_time = time.time()
    t = 0
    while running:
        clock.tick(FPS)
        elapsed = time.time() - start_time  # add slight time for each goal
        remaining = max(
            0, GAME_DURATION - int(elapsed) + (score1 + score2) * goal_effect_duration
        )

        if remaining == 0:
            running = False
            end_screen(left_ai, right_ai, score1, score2)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        keys = pygame.key.get_pressed()

        angle1 = angle2 = 0.0
        thrust1 = thrust2 = 0.0

        # --- Control handling ---
        if not player1.stunned:
            if left_ai:
                thrust1, angle1 = left_ai.move(
                    player1,
                    player2,
                    puck,
                    {
                        "score_left": score1,
                        "score_right": score2,
                        "time_remaining": remaining,
                        "side": "left",
                    },
                )
            else:
                if keys[pygame.K_w]:
                    player1.vel.y -= player1.accel
                if keys[pygame.K_s]:
                    player1.vel.y += player1.accel
                if keys[pygame.K_a]:
                    player1.vel.x -= player1.accel
                if keys[pygame.K_d]:
                    player1.vel.x += player1.accel

        if not player2.stunned:
            if right_ai:
                thrust2, angle2 = right_ai.move(
                    player2,
                    player1,
                    puck,
                    {
                        "score_left": score1,
                        "score_right": score2,
                        "time_remaining": remaining,
                        "side": "right",
                    },
                )
            else:
                if keys[pygame.K_UP]:
                    player2.vel.y -= player2.accel
                if keys[pygame.K_DOWN]:
                    player2.vel.y += player2.accel
                if keys[pygame.K_LEFT]:
                    player2.vel.x -= player2.accel
                if keys[pygame.K_RIGHT]:
                    player2.vel.x += player2.accel

            # convert to vector and apply force
            direction1 = pygame.Vector2(1, 0).rotate(-angle1)
            player1.vel += direction1 * (player1.accel * max(0, min(1, thrust1)))

            direction2 = pygame.Vector2(1, 0).rotate(-angle2)
            player2.vel += direction2 * (player2.accel * max(0, min(1, thrust2)))

        # Movement and collisions
        player1.move()
        player2.move()
        puck.move()
        handle_collision(player1, puck)
        handle_collision(player2, puck)
        handle_collision(player1, player2)
        score1, score2 = check_goal(
            puck, player1, player2, score1, score2, left_ai, right_ai
        )

        # Tick one frame for stun duration
        if player1.frames_stunned > 0:
            player1.frames_stunned -= 1
        if player2.frames_stunned > 0:
            player2.frames_stunned -= 1

        # Draw
        draw_arena(SCREEN, offset_x, offset_y, WIDTH, HEIGHT, GOAL_WIDTH, RINK_RECT)
        player1.draw(offset_x, offset_y)
        player2.draw(offset_x, offset_y)
        puck.draw(offset_x, offset_y)
        draw_scoreboard(SCREEN, score1, score2, remaining, rink_rect=RINK_RECT)
        menue_button()

        pygame.display.flip()

    # pygame.mixer.music.stop()
    pygame.quit()


if __name__ == "__main__":
    main()
