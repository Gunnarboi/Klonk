from ai_players.Myggan import AIPlayer as AI1
from ai_players.xabi import AIPlayer as MyAIPlayer
from simulate_games import simulate_matches

left_ai = MyAIPlayer()
right_ai = AI1()
results = simulate_matches(left_ai, right_ai, num_matches=10, info=True)
