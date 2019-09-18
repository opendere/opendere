import math

from opendere import action


class Ability:
    name = None  # one-word name of the ability
    action_description = None  # brief description of the ability
    command = None  # command user runs to create the Action
    action = action.Action  # the action this ability calls

    # some actions, such as Guard and Hide, cannot *LOGICALLY* be done as non-phase operations
    # this isn't for replicating yandere logic, it's for ensuring actions like "hide"
    # that aren't even sane being done "immediately" cannot be applied, because all they do
    # is update game.phase_actions
    is_exclusively_phase_action = None

    # whether an ability _requires_ a target or not
    requires_target = None


    def __init__(self, num_uses=0, phases=[], command_public=False):
        """
        num_ability_uses (int): the number of times the ability can be used per game, usually either 0, 1 or infinity
        phases (List[Phase]): when the ability can be used. day, night or both
        command_public (boolean): determines whether the action is executed through private message or in the channel
        """
        self.num_uses = num_uses
        self.phases = phases or []
        self.command_public = command_public

    def __call__(self, game, user, target_user=None):
        previous_action = next((act for act in game.phase_actions if isinstance(act, self.action) and user == act.user), None)
        if previous_action and previous_action.target_user == target_user:
            recipient = game.channel if self.command_public else user.uid
            return [(recipient, f"{user}: you've already told me you were going to do that, baka ;_;")]

        if previous_action:
            game.phase_actions.remove(previous_action)
            action_obj = self.action(game, user, target_user, ability=self, previous_action=previous_action)
        else:
            action_obj = self.action(game, user, target_user, ability=self)

        if self.is_exclusively_phase_action or game.phase_name == 'night':
            game.phase_actions.append(action_obj)
            return action_obj.messages
        else:
            game.completed_actions.append(action_obj)
            return action_obj()

    @property
    def description(self):
        return '{} during the {}, {}, using the command `{}`'.format(
            self.action_description,
            ' or '.join([phase.name for phase in self.phases]),
            'once per game' if self.num_uses != math.inf else f"once every {self.phases[0].name}",
            self.command,
        )


class UpgradeAbility(Ability):
    name = 'upgrade'
    action_description = "upgrade another player's role"
    command = 'upgrade <user>'
    is_exclusively_phase_action = False
    requires_target = True
    action = action.UpgradeAction


class HideAbility(Ability):
    name = 'hide'
    action_description = 'hide from killers'
    command = 'hide'
    is_exclusively_phase_action = True
    requires_target = False
    action = action.HideAction


class RevealAbility(Ability):
    name = 'reveal'
    action_description = 'reveal to all other players'
    command = 'reveal'
    is_exclusively_phase_action = False
    requires_target = False
    # TODO: make this a partial(RevealAction, self.reveal_as)
    action = action.RevealAction
    def __init__(self, *args, reveal_as=None, **kwargs):
        super().__init__(*args, **kwargs)
        # allow revealing as something else
        self.reveal_as = reveal_as


class SpyAbility(Ability):
    name = 'spy'
    action_description = "inspect a player's role (be wary of disguised roles which can appear as other roles!)"
    command = 'spy <user>'
    is_exclusively_phase_action = False
    requires_target = True
    action = action.SpyAction


class StalkAbility(Ability):
    name = 'stalk'
    action_description = 'learn where another player goes'
    command = 'stalk <user>'
    is_exclusively_phase_action = True
    requires_target = True
    action = action.StalkAction


class CheckAbility(Ability):
    name = 'check'
    action_description = "inspect another player's alignment"
    command = 'check <user>'
    is_exclusively_phase_action = True
    requires_target = True
    action = action.CheckAction


class GuardAbility(Ability):
    name = 'guard'
    action_description = 'protect another player from danger (except yanderes, who may kill you :D)'
    command = 'guard <user>'
    is_exclusively_phase_action = True
    requires_target = True
    action = action.GuardAction


class KillAbility(Ability):
    name = 'kill'
    action_description = 'single-handedly kill another player of their choosing'
    command = 'kill <user>'
    is_exclusively_phase_action = False
    requires_target = True
    action = action.KillAction


class VoteKillAbility(Ability):
    """
    vote to kill someone with your voting cohort
    your cohort consists of your unique (command_public, phase) combination,
    that means public-command day voters vote together (typical lynching)
    """
    name = 'vote'
    action_description = 'vote with others to kill'
    command = 'vote <user>'
    is_exclusively_phase_action = True
    requires_target = True
    action = action.VoteKillAction
