#!/usr/bin/env python
# 
# tournament.py -- implementation of a Swiss-system tournament
#
# This file can be used to track the results of a Swiss-draw style tournament
# First use set_tournament_id() to generate a new tournament
# Register new players with register_player()
# Once all players are registered, assign pairings with swiss_pairings()
# As matches are finished, report the winner with report_match()
# For a simple match with a clear winner:
#       use report_match(winner, loser) where winner and loser are player_ids
# For a match that resulted in a draw:
#       use report_match(player1_id, player2_id, True)
# Use swiss_pairings() again once the round is finished.
# Once the tournament is over, run finalRankings() to print the final results.

import psycopg2
import random
import re
tournament_id = None


def set_tournament_id(t_id=0):
    """
    Sets a global tournament_id to keep track of the current tournament.
    Takes an optional argument to assign a tournament other than the first.
    """
    new_tournament(t_id)
    global tournament_id
    tournament_id = t_id
    return t_id


def new_tournament(t_id):
    pg = connect()
    c = pg.cursor()
    try:
        c.execute("INSERT INTO tournaments                                    \
                      VALUES ('GENERATED_TOURNAMENT', %s)", (t_id,))
        pg.commit()
    except psycopg2.IntegrityError:
        pg.rollback()
    finally:
        pg.close()


def connect():
    """Connect to the PostgreSQL database.
    Returns a database connection."""
    pg = psycopg2.connect("dbname = tournament")
    return pg


def execute_query(query, variables=()):
    pg = connect()
    c = pg.cursor()
    c.execute(query, variables)
    if re.match("(^INSERT|^UPDATE|^DELETE)", query, re.I) is not None:
        pg.commit()
        pg.close()
    else:
        fetch = c.fetchall()
        pg.close()
        return fetch


def delete_matches():
    """Remove all the match records from the database."""
    execute_query("DELETE FROM matches WHERE tournament_id = %s",
                  (tournament_id,))


def delete_players():
    """Remove all the player records from the database."""
    execute_query("DELETE FROM players WHERE tournament_id = %s",
                  (tournament_id,))


def count_players():
    """Returns the number of players currently registered."""
    return_value = execute_query("SELECT COUNT(*) FROM players\
                                  WHERE tournament_id = %s",
                                 (tournament_id,))
    return return_value[0][0]


def register_player(name):
    """Adds a player to the tournament database.
  
    The database assigns a unique serial id number for the player.  (This
    should be handled by your SQL database schema, not in your Python code.)
  
    Args:
      name: the player's full name (need not be unique).
    """
    execute_query("INSERT INTO players (name, tournament_id, prev_opponents)\
                VALUES (%s, %s, %s)", (name, tournament_id, [],))


def player_standings():
    """Returns a list of the players and their win records, sorted by wins.

    The first entry in the list should be the player in first place,
    or a player tied for first place if there is currently a tie.

    Returns:
      A list of tuples, each of which contains (id, name, wins, matches):
        id: the player's unique id (assigned by the database)
        name: the player's full name (as registered)
        wins: the number of matches the player has won
        matches: the number of matches the player has played
    """
    r_value = execute_query("SELECT player_id, name, points,matches_played \
                            FROM players where tournament_id = %s \
                            ORDER BY points DESC, opp_win, name",
                            (tournament_id,))
    return r_value


def report_match(winner, loser, draw=False):
    """Records the outcome of a single match between two players.
    For a simple match with a clear winner:
        use report_match(winner, loser) where winner and loser are player_ids
    For a match that resulted in a draw:
        use report_match(player1_id, player2_id, True)

    Args:
      winner:  the player_id of the player who won
      loser:  the player_id of the player who lost
      draw: boolean on whether the match was a draw or split. Defaults to False
    """
    if not draw:
            execute_query("""UPDATE players SET
                          matches_played = matches_played +1,
                          prev_opponents = prev_opponents || %s
                          WHERE player_id = %s and tournament_id = %s""",
                          (winner, loser, tournament_id))
            execute_query("UPDATE players SET points = points + 1.0,\
                                      matches_played = matches_played +1,\
                                      prev_opponents = prev_opponents || %s\
                          WHERE player_id = %s and tournament_id = %s",
                          (loser, winner, tournament_id))
    else:
        for player in range(0, 1):
            execute_query("""UPDATE players SET points = (points + 0.5)
                          WHERE (player_id = %s or player_id = %s) and
                                                tournament_id = %s""",
                          (winner, loser, tournament_id))
    execute_query("INSERT INTO matches VALUES (%s, %s, %s, %s)",
                  (winner, loser, tournament_id, draw))

 
def swiss_pairings():
    """Returns a list of pairs of players for the next round of a match.
  
    Assuming that there are an even number of players registered, each player
    appears exactly once in the pairings.  Each player is paired with another
    player with an equal or nearly-equal win record, that is, a player adjacent
    to him or her in the standings.
  
    Returns:
      A list of tuples, each of which contains (id1, name1, id2, name2)
        id1: the first player's unique id
        name1: the first player's name
        id2: the second player's unique id
        name2: the second player's name
    """
    standings = player_standings()
    pairings = []
    global prev_bye
    global bye_player
    if len(standings) % 2 != 0:
        prev_bye = True
        while prev_bye:
            random.shuffle(standings)
            bye_player = standings[0]
            prev_bye = execute_query("Select bye from players\
                                      WHERE player_id = %s",
                                     (bye_player[0],))[0][0]
        standings = player_standings()
        standings.remove(bye_player)
        assign_bye(bye_player[0])
    while len(standings) > 1:
        idx = 1
        prev_opponents = execute_query("""SELECT prev_opponents from players
                                          WHERE player_id = %s""",
                                       (standings[0][0],))
        while True:
            if standings[idx][0] in prev_opponents and\
                    idx != len(standings)-1:
                idx += 1
            else:
                pairings.append(sum([list(standings[0][0:2]),
                                     list(standings[idx][0:2])], []))
                standings.pop(idx)
                standings.pop(0)
                break
    return pairings


def final_rankings():
    """
    Calculates any tie-breakers and prints the rankings
    in table form. Can be used on any round.
    """
    ties = 1  # used to keep track of how many players tied at a certain rank
    last_record = [0, 0]  # used to track the previous players record
    rank = 0  # keeps track of the current rank during iteration

    players = execute_query("""SELECT player_id, prev_opponents FROM players
                            WHERE tournament_id = %s
                            ORDER BY points DESC, name""",
                            (tournament_id,))
    for (player, opponents) in players:
        player_sum = 0  # tracks a certain player's opponent points
        for opponent in opponents:
            player_sum += execute_query("""SELECT points FROM players
                                           WHERE player_id = %s""",
                                        (opponent,))[0][0]
        execute_query("""UPDATE players SET opp_win = %s
                         WHERE player_id = %s""",
                      (float(player_sum)/len(opponents), player,))
    standings = execute_query("""SELECT name, points, opp_win FROM players
                                ORDER BY points DESC, opp_win DESC, name""")
    print "\nCurrent Rankings:"
    for player in standings:
        if [player[1], player[2]] != last_record:
            rank += 1 * ties
            ties = 1
        else:  # Must be a tie, increment ties multiplier
            ties += 1
        last_record = [player[1], player[2]]
        print("%d.: %s" % (rank, player))


def assign_bye(player):
    """
    Assigns a bye to a player and updates their points.
    Should be called automatically when necessary.
    :param player: The player's id.
    """
    execute_query("""UPDATE players SET bye = TRUE, points = points + 1
                     WHERE player_id = %s and tournament_id = %s """,
                  (player, tournament_id,))


def main():
    """
    Sets the tournament_id if it is not already. Runs on initialization.
    """
    if tournament_id is None:
        print("""Tournament id not found...\
        \nChecking for existing tournaments...""")
        t_id = set_tournament_id()
        t_name = execute_query("""
                  Select tournament_name from tournaments
                  WHERE tournament_id = %s
                  """, (t_id,))[0][0]
        print("""Using tournament: %s\
        \nTo change this, use setTournament(t_id)""" % t_name)

if __name__ == '__main__':
    main()
