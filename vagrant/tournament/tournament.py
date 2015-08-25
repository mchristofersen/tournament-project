#!/usr/bin/env python
# 
# tournament.py -- implementation of a Swiss-system tournament
#
# This file can be used to track the results of a Swiss-draw style tournament
# First use setTournamentId() to generate a new tournament
# Register new players with registerPlayer()
# Once all players are registered, assign pairings with swissPairings()
# As matches are finished, report the winner with reportMatch()
# Use swissPairings() again once the round is finished.
# Once the tournament is over, run finalRankings() to print the final results.

import psycopg2
import random


def setTournamentId(t_id=0):
    """
    Sets a global tournament_id to keep track of the current tournament.
    Takes an optional argument to assign a tournament other than the first.
    """
    global tournament_id
    tournament_id = t_id
    return tournament_id


def connect():
    """Connect to the PostgreSQL database.
    Returns a database connection."""
    pg = psycopg2.connect("dbname = tournament")
    c = pg.cursor()
    c.execute("SELECT * FROM tournaments WHERE tournament_id= %s",
              (tournament_id,))
    if len(c.fetchall()) == 0:
        print "Tournament id not found...\n\
               Creating new tournament..."
        c.execute("INSERT INTO tournaments                                    \
                  VALUES ('GENERATED_TOURNAMENT', %s)", (tournament_id,))
        pg.commit()
    return pg


def deleteMatches():
    """Remove all the match records from the database."""
    pg = connect()
    c = pg.cursor()
    c.execute("DELETE FROM matches WHERE tournament_id = %s", (tournament_id,))
    pg.commit()
    pg.close()


def deletePlayers():
    """Remove all the player records from the database."""
    pg = connect()
    c = pg.cursor()
    c.execute("DELETE FROM players WHERE tournament_id = %s", (tournament_id,))
    pg.commit()
    pg.close()

def countPlayers():
    """Returns the number of players currently registered."""
    pg = connect()
    c = pg.cursor()
    c.execute("SELECT COUNT(*) FROM players WHERE tournament_id = %s",
              (tournament_id,))
    return_value = c.fetchall()[0][0]
    pg.close()
    return return_value

def registerPlayer(name):
    """Adds a player to the tournament database.
  
    The database assigns a unique serial id number for the player.  (This
    should be handled by your SQL database schema, not in your Python code.)
  
    Args:
      name: the player's full name (need not be unique).
    """
    pg = connect()
    c = pg.cursor()
    c.execute("INSERT INTO players (name, tournament_id, prev_opponents)\
                VALUES (%s, %s, %s)", (name, tournament_id, [],))
    pg.commit()
    pg.close()

def playerStandings():
    """Returns a list of the players and their win records, sorted by wins.

    The first entry in the list should be the player in first place, or a player
    tied for first place if there is currently a tie.

    Returns:
      A list of tuples, each of which contains (id, name, wins, matches):
        id: the player's unique id (assigned by the database)
        name: the player's full name (as registered)
        wins: the number of matches the player has won
        matches: the number of matches the player has played
    """
    pg = connect()
    c = pg.cursor()
    c.execute("SELECT player_id,\
                      name,\
                      points,\
                      matches_played \
                      FROM players where tournament_id = %s ORDER BY points DESC, opp_win, name",
              (tournament_id,))
    return_value = c.fetchall()
    pg.close()
    return return_value


def reportMatch(winner, loser, draw=False):
    """Records the outcome of a single match between two players.

    Args:
      winner:  the id number of the player who won
      loser:  the id number of the player who lost
      draw: boolean on whether the match was a draw or split. DEFAULT False
    """
    pg = connect()
    c = pg.cursor()
    if not draw:
            c.execute("UPDATE players SET matches_played = matches_played +1,\
                                          prev_opponents = prev_opponents || %s\
                                      WHERE player_id = %s and\
                                            tournament_id = %s",
                    (winner, loser, tournament_id))
            c.execute("UPDATE players SET points = points + 1.0,\
                                          matches_played = matches_played +1,\
                                          prev_opponents = prev_opponents || %s\
                                      WHERE player_id = %s and\
                                            tournament_id = %s",
                    (loser, winner, tournament_id))
            pg.commit()
    else:
        for player in range(0,1):
            c.execute("UPDATE players SET points = (points + 0.5)\
                                      WHERE (player_id = %s or \
                                            player_id = %s) and\
                                            tournament_id = %s",
                    (winner, loser, tournament_id))
            pg.commit()
    c.execute("INSERT INTO matches VALUES (%s, %s, %s, %s)",
              (winner, loser, tournament_id, draw))
    pg.commit()
    pg.close()

 
def swissPairings():
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
    pg = connect()
    c = pg.cursor()
    print "------------------"
    standings = playerStandings()
    pairings = []
    global prev_bye
    global bye_player
    if len(standings) % 2 != 0:
        prev_bye = True
        while prev_bye:
            random.shuffle(standings)
            bye_player = standings[0]
            c.execute("Select bye from players WHERE player_id = %s", (bye_player[0],))
            prev_bye = c.fetchall()[0][0]
        standings = playerStandings()
        standings.remove(bye_player)
        assign_bye(bye_player[0])
    while len(standings) > 1:
        idx = 1
        c.execute("Select prev_opponents from players \
                  WHERE player_id = %s",
                  (standings[0][0],))
        prev_opponents = c.fetchall()[0][0]
        while True:
            if standings[idx][0] in prev_opponents and\
                    idx != len(standings)-1:
                idx += 1
            else:
                pairings.append([standings[0][0],
                                 standings[0][1],
                                 standings[idx][0],
                                 standings[idx][1]])
                standings.pop(idx)
                standings.pop(0)
                break
    pg.close()
    return pairings


def final_rankings():
    """
    Calculates any tie-breakers and prints the rankings
    in table form. Can be used on any round.
    """
    pg = connect()
    c = pg.cursor()
    ties = 1  # used to keep track of how many players tied at a certain rank
    last_record = [0, 0]  # used to track the previous players record
    rank = 0  # keeps track of the current rank during iteration

    c.execute("SELECT player_id, prev_opponents FROM players \
              WHERE tournament_id = %s ORDER BY points DESC, name",
              (tournament_id,))
    players = c.fetchall()

    for (player, opponents) in players:
        player_sum = 0  # tracks a certain player's opponent points
        for opponent in opponents:
            c.execute("SELECT points FROM players WHERE player_id = %s",
                      (opponent,))
            player_sum += c.fetchall()[0][0]

        c.execute("UPDATE players SET opp_win = %s \
                  WHERE player_id = %s",
                  (float(player_sum)/len(opponents), player,))
        pg.commit()
    c.execute("SELECT name, points, opp_win FROM players\
              ORDER BY points DESC, opp_win DESC, name")
    standings = c.fetchall()
    print "\nCurrent Rankings:"
    for player in standings:
        if [player[1], player[2]] != last_record:
            rank += 1 * ties
            ties = 1
        else:  # Must be a tie, increment ties multiplier
            ties += 1
        last_record = [player[1], player[2]]
        print("%d.: %s" % (rank, player))
    pg.close()


def assign_bye(player):
    """
    Assigns a bye to a player and updates their points.
    Should be called automatically when necessary.
    :param player: The player's id.
    """
    pg = connect()
    c = pg.cursor()
    c.execute("UPDATE players SET bye = TRUE,                                 \
                                  points = points + 1                         \
              WHERE player_id = %s and                                        \
                    tournament_id = %s",
              (player, tournament_id,))
    pg.commit()
    pg.close()
