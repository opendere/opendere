import pytest

from opendere import game, roles


def test_roles_dont_share_ability_objects():
    hik0 = roles.Hikikomori()
    hik1 = roles.Hikikomori()
    assert len(hik0.abilities) == len(hik1.abilities)
    hik0.abilities += ['foo']
    assert len(hik0.abilities) != len(hik1.abilities)


def test_create_game_too_few():
    with pytest.raises(ValueError):
        game.Game(['a'])
    with pytest.raises(ValueError):
        game.Game(['a', 'b'])
    with pytest.raises(ValueError):
        game.Game(['a', 'b', 'c'])


def test_create_game_success():
    game.Game(['a', 'b', 'c', 'd'])
