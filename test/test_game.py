import pytest

from opendere import game


def test_create_game_too_few():
    g = game.Game()
    g.join_game('a', 'a')
    g.join_game('b', 'b')
    assert len(g.users) == 2
    for _ in range(61):
        g.tick()
        assert len(g.users) == 0


def test_create_game_success():
    game.Game(['a', 'b', 'c', 'd'])
