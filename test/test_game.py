import pytest
from freezegun import freeze_time
from opendere import game


def test_create_game_too_few():
    g = game.Game(None, None, None)
    for i in range(3):
        g.join_game(str(i), str(i))

    assert len(g.users) == 3
    with freeze_time(g.phase_end):
        with pytest.raises(ValueError):
            g.tick()


def test_create_game_success():
    g = game.Game(None, None, None)
    for i in range(4):
        g.join_game(str(i), str(i))

    assert len(g.users) == 4
    assert g.phase == None
    with freeze_time(g.phase_end):
        g.tick()
    assert g.phase == 0
    assert g.phase_name == 'day'
    assert g.num_yanderes_alive == 1


def test_create_night_game_success():
    g = game.Game(None, None, None)
    for i in range(7):
        g.join_game(str(i), str(i))

    g.user_hurry('a')
    g.user_hurry('e')

    assert len(g.users) == 7
    assert g.phase == None
    with freeze_time(g.phase_end):
        g.tick()
    assert g.phase == 0
    assert g.phase_name == 'night'
    assert g.num_yanderes_alive == 2
