import pytest

from opendere import game


def test_create_game_too_few():
    with pytest.raises(ValueError):
        game.Game(['a'])
    with pytest.raises(ValueError):
        game.Game(['a', 'b'])
    with pytest.raises(ValueError):
        game.Game(['a', 'b', 'c'])

def test_create_game_success():
    game.Game(['a', 'b', 'c', 'd'])
