from opendere import game
from opendere import action
from freezegun import freeze_time
from numpy import random


def test_vote_kill():
    g = game.Game('game', None, None)
    for i in range(4):
        g.join_game(str(i), str(i))
    with freeze_time(g.phase_end):
        g.tick()

    assert g.users['3'].is_alive
    assert g.num_players_alive == 4

    g.user_action('0', '!vote 3', 'game')
    g.user_action('1', '!vote 3', 'game')
    g.user_action('2', '!vote 3', 'game')
    g.user_action('3', '!vote abstain', 'game')

    g.tick()

    assert not g.users['3'].is_alive
    assert g.num_players_alive == 3
    assert g.phase_actions == []


def test_hide_vote_kill():
    g = game.Game('game', None, None)
    for i in range(5):
        g.join_game(str(i), str(i))
    users = [user for user in g.users.values()]
    with freeze_time(g.phase_end):
        g.tick()

    # u1 hides, u3 and u4 vote to kill u1
    g.phase_actions = [
        action.VoteToKillAction(g, users[3], users[1]),
        action.HideAction(g, users[1], None),
        action.VoteToKillAction(g, users[4], users[1]),
    ]

    with freeze_time(g.phase_end):
        g.tick()

    assert users[1].is_alive
    assert g.phase_actions == []
