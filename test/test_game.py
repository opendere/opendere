import pytest, time
from freezegun import freeze_time
from datetime import datetime, timedelta
from opendere import game


def test_create_game_too_few():
    test = game.Game('#test', 'test', 'test')
    test.join_game('a', 'kitties')
    test.join_game('b', 'bunnies')
    test.join_game('c', 'catties')
    assert len(test.users) == 3
    test.user_hurry('a')
    test.user_hurry('b')
    test.user_hurry('c')
    with freeze_time(test.phase_end):
        with pytest.raises(ValueError):
            test.tick()

def test_create_game_success():
    test = game.Game('#test', 'test', 'test')
    test.join_game('a', 'kitties')
    test.join_game('b', 'bunnies')
    test.join_game('c', 'catties')
    test.join_game('d', 'daddies')
    assert len(test.users) == 4
    test.user_hurry('a')
    test.user_hurry('b')
    test.user_hurry('c')
    test.user_hurry('d')
    assert test.phase == None
    with freeze_time(test.phase_end):
        test.tick()
    assert test.phase == 0
    assert test.phase_name == 'day'
    assert test.num_yanderes_alive == 1

def test_create_night_game_success():
    test = game.Game('#test', 'test', 'test')
    test.join_game('a', 'kitties')
    test.join_game('b', 'bunnies')
    test.join_game('c', 'catties')
    test.join_game('d', 'daddies')
    # test.join_game('e', 'e')
    test.join_game('f', 'furries')
    test.join_game('g', 'gummies')
    test.join_game('h', 'hotties')
    assert len(test.users) == 7
    test.user_hurry('a')
    test.user_hurry('b')
    test.user_hurry('c')
    test.user_hurry('d')
    test.user_hurry('e')
    test.user_hurry('f')
    test.user_hurry('g')
    test.user_hurry('h')
    assert test.phase == None
    with freeze_time(test.phase_end):
        test.tick()
    assert test.phase == 0
    assert test.phase_name == 'night'
    assert test.num_yanderes_alive == 2
