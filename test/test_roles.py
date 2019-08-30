from opendere import roles


def test_roles_dont_share_ability_objects():
    hik0 = roles.Hikikomori()
    hik1 = roles.Hikikomori()
    assert len(hik0.abilities) == len(hik1.abilities)
    hik0.abilities += ['foo']
    assert len(hik0.abilities) != len(hik1.abilities)


def test_no_illegal_ability_configurations():
    for role in roles.all_role_classes:
        for ability in role.abilities:
            if roles.Phase.day in ability.phases:
                assert not ability.is_exclusively_phase_action
