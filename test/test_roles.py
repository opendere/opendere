from opendere import roles


def test_roles_dont_share_ability_objects():
    hik0 = roles.Hikikomori()
    hik1 = roles.Hikikomori()
    assert len(hik0.abilities) == len(hik1.abilities)
    hik0.abilities += ['foo']
    assert len(hik0.abilities) != len(hik1.abilities)
