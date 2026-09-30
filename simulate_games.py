import os

os.environ["SDL_VIDEODRIVER"] = "dummy"  # Run pygame headless

import math
import pygame  # only for Vector2
import random
from Klonk import (
    Puck,
    handle_collision,
    check_goal,
    create_agent,
    WIDTH,
    HEIGHT,
    GAME_DURATION,
)


def simulate_matches(ai_left, ai_right, num_matches=10, info=True):
    results = {
        "left_wins": 0,
        "right_wins": 0,
        "draws": 0,
        "match_results": [],
    }

    FPS = 60  # fixed simulation rate
    dt = 1 / FPS
    frames_per_match = int(GAME_DURATION * FPS)

    for match in range(num_matches):
        player1 = create_agent(ai_left, "left")
        player2 = create_agent(ai_right, "right")
        # Puck y coordinate can not be in the middle line to avoid deadlocks
        puck = Puck(
            WIDTH / 2, HEIGHT / 2 + random.choice([-1, 1]) * random.randint(1, 30)
        )
        score1 = score2 = 0

        # Simulate GAME_DURATION seconds at 60 FPS (but as fast as possible)
        for frame in range(frames_per_match):
            remaining = GAME_DURATION - frame * dt

            angle1 = angle2 = 0.0
            thrust1 = thrust2 = 0.0

            # --- AI Decisions ---
            if not player1.stunned:
                thrust1, angle1 = ai_left.move(
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

            if not player2.stunned:
                thrust2, angle2 = ai_right.move(
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

            direction1 = pygame.Vector2(1, 0).rotate(-angle1)
            player1.vel += direction1 * (player1.accel * max(0, min(1, thrust1)))

            direction2 = pygame.Vector2(1, 0).rotate(-angle2)
            player2.vel += direction2 * (player2.accel * max(0, min(1, thrust2)))

            # --- Physics update ---
            player1.move()
            player2.move()
            puck.move()

            handle_collision(player1, puck)
            handle_collision(player2, puck)
            handle_collision(player1, player2)

            score1, score2 = check_goal(
                puck, player1, player2, score1, score2, render=False
            )

            # Tick one frame for stun duration
            if player1.frames_stunned > 0:
                player1.frames_stunned -= 1
            if player2.frames_stunned > 0:
                player2.frames_stunned -= 1

        # --- Record result ---
        results["match_results"].append({"left": score1, "right": score2})
        if score1 > score2:
            results["left_wins"] += 1
        elif score2 > score1:
            results["right_wins"] += 1
        else:
            results["draws"] += 1

        if info:
            print(f"Match {match+1}: Left {score1} - Right {score2}")

    return results
