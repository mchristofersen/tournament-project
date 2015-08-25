This repo can be used to track the results of a Swiss-draw style tournament

First create a new database in PostgreSQL named "tournament"


Then using tournament.py, use setTournamentId() to generate a new tournament

Register new players with registerPlayer()

Once all players are registered, assign pairings with swissPairings()

As matches are finished, report the winner with reportMatch()

Use swissPairings() again once the round is finished.

Once the tournament is over, run finalRankings() to print the final results.