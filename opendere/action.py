from collections import defaultdict


"""
Pattern:
- Actions are *applied* by users. When applied they are pushed to the Game.phase_actions queue.
- Game.phase_actions is a list of Actions ordered by time of entry.
- An action mutates the game state. A special case of game state mutation is updating Game.phase_actions itself. Some Actions
  delete other Actions from Game.phase_actions, for example a HideAction deletes a KillAction directed at the user. Some
  actions add "post-processing" actions to Game.phase_actions. For example, GuardAction will ensure if you're guarding
  yandere UnstoppableKillAction exists, and in turn UnstoppableKillAction will kill you once it's applied.
- When adding to Game.phase_changes, it should be checked whether the Action already exists:`action in Game.phase_changes`
"""


class Action:
    def __init__(self, game, user, target_user):
        self.game = game
        self.user = user
        self.target_user = target_user

    def __call__(self):
        # apply the Action. Actions either update game state by changing the
        # Actions to be evaluated, or it updates the game in another way
        # returns messages resulting from the action
        raise NotImplementedError

    @property
    def actions_of_my_type(self):
        return [
            action for action in self.game.phase_actions
            if isinstance(action, type(self))
        ] + [self]

    def del_actions_of_type(self, action_type):
        self.game.phase_actions = [
            action for action in self.game.phase_actions
            if not isinstance(action, action_type)
        ]


class KillAction(Action):
    def __call__(self):
        # kill the target
        self.target_user.is_alive = False
        return []


class VoteToKillAction(Action):
    def __call__(self):
        # at the end of the phase, the first VoteToKillAction handles this logic for all
        # instances of this action then deletes all instances of VoteToKillAction
        vote_counts = defaultdict(int)
        for action in self.actions_of_my_type:
            vote_counts[action.target_user] += 1
        most_voted_user = max(vote_counts, key=vote_counts.get)
        # TODO: need logic to handle case whether there is a tie for most-voted

        # TODO: "abstain" is bad, it should probably be a constant
        if most_voted_user == "abstain":
            return []  # TODO: message something about failing to lynch
        else:
            self.game.phase_actions.append(
                KillAction(self.game, None, most_voted_user)
            )
            return []  # TODO: some message about who was voted to be lynched

        # ensure VoteToKillAction isn't processed twice
        self.del_actions_of_type(type(self))


class UnstoppableKillAction(Action):
    # A kill that shouldn't be eliminated from the action list
    __call__ = KillAction.__call__


class GuardAction(Action):
    def __call__(self):
        # eliminate any actions that kill self.user
        self.game.phase_actions = [
            action for action in self.game.phase_actions
            if not (isinstance(action, KillAction) and action.target_user == self.target_user)
        ]
        # kill self if the guarded role isn't safe to guard
        if not self.target_user.role.safe_to_guard:
            self.game.phase_actions.append(
                UnstoppableKillAction(self.game, self.target_user, self.user)
            )
        return []


class HideAction(Action):
    is_legal_during_day = False
    def __call__(self):
        # eliminate any actions that kill self.user
        self.game.phase_actions = [
            action for action in self.game.phase_actions
            if not (isinstance(action, KillAction) and action.target_user == self.user)
        ]
        return []


# determines the order in which actions are evaluated. Many actions override other actions.
action_priority = [
    VoteToKillAction,
    GuardAction,
    HideAction,
    KillAction,
    UnstoppableKillAction,
]
