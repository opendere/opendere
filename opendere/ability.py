import math

from opendere import action


class Ability:
    name = None  # one-word name of the ability
    action_description = None  # brief description of the ability
    command = None  # command user runs to create the Action

    # some actions, such as Guard and Hide, cannot *LOGICALLY* be done as non-phase operations
    # this isn't for replicating yandere logic, it's for ensuring actions like "hide"
    # that aren't even sane being done "immediately" cannot be applied, because all they do
    # is update game.phase_actions
    is_exclusively_phase_action = None

    def __init__(self, num_uses=0, phases=[], command_public=False):
        """
        num_ability_uses (int): the number of times the ability can be used per game, usually either 0, 1 or infinity
        phases (List[Phase]): when the ability can be used. day, night or both
        command_public (boolean): determines whether the action is executed through private message or in the channel
        """
        self.num_uses = num_uses
        self.phases = phases
        self.command_public = command_public

    def __call__(self, game, user, target_user=None):
        action_obj = self.action(game, user, target_user)
        if self.is_exclusively_phase_action or game.phase_name == 'night':
            previous_action = next((act for act in game.phase_actions if isinstance(act, type(self)) and user == act.user), None) 
            if previous_action:
                game.phase_actions.remove(previous_action)
            else:
                self.num_uses -= 1
            game.phase_actions.append(action_obj)
            return action_obj.messages
        else:
            self.num_uses -= 1
            game.completed_actions.append(action_obj)
            return action_obj()

    @property
    def description(self):
        return '{} during the {}, {}, using the command `{}`'.format(
            self.action_description,
            ' or '.join([phase.name for phase in self.phases]),
            'once per game' if self.num_uses != math.inf else f"once every {self.phases[0].name}",
            self.command
        )


class UpgradeAbility(Ability):
    name = 'upgrade'
    action_description = 'upgrade any other player'
    command = 'upgrade <user>'
    is_exclusively_phase_action = False
    #action = UpgradeAction


class HideAbility(Ability):
    name = 'hide'
    action_description = 'hide from killers'
    command = 'hide'
    is_exclusively_phase_action = True
    action = action.HideAction


class RevealAbility(Ability):
    name = 'reveal'
    action_description = 'reveal to all other players'
    command = 'reveal'
    is_exclusively_phase_action = False
    #action = RevealAction


class SpyAbility(Ability):
    name = 'spy'
    action_description = 'inspect another player\'s role (be careful of disguised roles which may appear as other roles!)'
    command = 'spy <user>'
    is_exclusively_phase_action = False
    #action = SpyAction


class StalkAbility(Ability):
    name = 'stalk'
    action_description = 'learn where another player goes'
    command = 'stalk <user>'
    is_exclusively_phase_action = True
    #action = StalkAction


class CheckAbility(Ability):
    name = 'check'
    action_description = 'inspect another player\'s alignment'
    command = 'check <user>'
    is_exclusively_phase_action = True
    #action = CheckAction


class GuardAbility(Ability):
    name = 'guard'
    action_description = 'protect a player from any danger'
    command = 'guard <user>'
    is_exclusively_phase_action = True
    action = action.GuardAction


class KillAbility(Ability):
    name = 'kill'
    action_description = 'single-handedly kill a player of their choosing'
    command = 'kill <user>'
    is_exclusively_phase_action = False
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
    action = action.VoteToKillAction
