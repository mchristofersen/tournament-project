-- Table definitions for the tournament project.

-- The tournaments table allows for the database to handle multiple
-- tournaments.
CREATE TABLE tournaments (tournament_name VARCHAR(200),
                          tournament_id serial PRIMARY KEY
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
                      tournament_id int,
                      player_id serial PRIMARY KEY
                      );

-- The matches table is just for reference to find the winner of a particular
-- match.
CREATE TABLE matches (player1_id int,
                      player2_id int,
                      tournament_id int REFERENCES tournaments,
                      draw boolean DEFAULT FALSE
                      );