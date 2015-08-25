-- Table definitions for the tournament project.
SELECT pg_terminate_backend(pg_stat_activity.pid)
FROM pg_stat_activity
WHERE pg_stat_activity.datname = 'tournament'
AND pid <> pg_backend_pid();
DROP DATABASE tournament;
CREATE DATABASE tournament;
\c tournament;

-- The tournaments table allows for the database to handle multiple
-- tournaments.
CREATE TABLE tournaments (tournament_name VARCHAR(200),
                          tournament_id int PRIMARY KEY
                          );


-- players.points is the players sum of all points earned
--                +1.0 for a win or bye
--                +0.5 for a draw
--                +0.0 for a loss
-- players.opp_win is the average points of a players opponents faced so far
-- it is only used for tie-breakers

CREATE TABLE players (name VARCHAR(100),
                      points FLOAT DEFAULT 0.0,
                      matches_played int DEFAULT 0,
                      prev_opponents INT[],
                      bye boolean DEFAULT FALSE,
                      opp_win FLOAT,
                      tournament_id int REFERENCES tournaments,
                      player_id serial PRIMARY KEY
                      );

-- The matches table is just for reference to find the winner of a particular
-- match.
CREATE TABLE matches (
    player1_id INTEGER REFERENCES players(player_id) ON DELETE CASCADE,
    player2_id INTEGER REFERENCES players(player_id) ON DELETE CASCADE,
    CHECK (player1_id <> player2_id),
    tournament_id int REFERENCES tournaments,
    draw boolean DEFAULT FALSE
                      );

-- Creates a function to display player standings
CREATE FUNCTION tournament_filter (x int, OUT player_id int, OUT name text,
                          OUT points FLOAT, OUT matches_played int)
RETURNS SETOF record AS $$
    SELECT player_id, name, points, matches_played
    FROM players WHERE tournament_id = $1
    ORDER BY points DESC, name;
$$ LANGUAGE SQL;