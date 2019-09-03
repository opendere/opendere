from opendere import action, game


def test_vote_kill():
    g = game.Game(None, None, None)
    users = [game.User(str(i), str(i)) for i in range(5)]
    for user in users:
        g.users[user.uid] = user

    # u2 guards u1, u3 and u4 vote to kill u1
    g.phase_actions = [
        action.VoteToKillAction(g, users[3], users[1]),
        action.VoteToKillAction(g, users[4], users[1]),
    ]

    g._process_phase_actions()

    assert not users[1].is_alive
    assert g.phase_actions == []


def test_hide_vote_kill():
    g = game.Game(None, None, None)
    users = [game.User(str(i), str(i)) for i in range(5)]
    for user in users:
        g.users[user.uid] = user

    # u1 hides, u3 and u4 vote to kill u1
    g.phase_actions = [
        action.VoteToKillAction(g, users[3], users[1]),
        action.HideAction(g, users[1], None),
        action.VoteToKillAction(g, users[4], users[1]),
    ]

    g._process_phase_actions()

    assert users[1].is_alive
    assert g.phase_actions == []
