This repo can be used to track the results of a Swiss-draw style tournament

First create a new database in PostgreSQL named "tournament"


Then using tournament.py, use set_tournament_id() to generate a new tournament

Register new players with register_player()

Once all players are registered, assign pairings with swiss_pairings()

As matches are finished, report the winner with report_match()

Use swiss_pairings() again once the round is finished.

Once the tournament is over, run finalRankings() to print the final results.