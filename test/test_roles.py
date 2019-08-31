from opendere import roles, ability


def test_roles_dont_share_ability_objects():
    hik0 = roles.Hikikomori()
    hik1 = roles.Hikikomori()
    assert len(hik0.abilities) == len(hik1.abilities)
    hik0.abilities += ['foo']
    assert len(hik0.abilities) != len(hik1.abilities)


def test_no_illegal_ability_configurations():
    # for now, all phase abilities are illegal during the day except for votekill
    legal_phase_abilities = [ability.VoteKillAbility]
    for role in roles.all_role_classes:
        for role_ability in role.abilities:
            if type(role_ability) not in legal_phase_abilities and roles.Phase.day in role_ability.phases:
                assert not role_ability.is_exclusively_phase_action, ('failed for', role, role_ability)
