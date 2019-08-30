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


class KillAction(Action):
    def __call__(self):
        # kill the target
        self.game.users[self.target_user].is_alive = False
        return []


class UnstoppableKillAction(Action):
    # A kill that shouldn't be eliminated from the action list
    __call__ = KillAction.__call__


class GuardAction(Action):
    def __call__(self):
        # eliminate any actions that kill self.user
        self.game.phase_actions = [
            action for action in self.phase_actions
            if self.phase_action.target_user != self.target_user or
            isinstance(action, KillAction)
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
            action for action in self.phase_actions
            if self.phase_action.target_user != self.user or
            isinstance(action, KillAction)
        ]
        return []


# determines the order in which actions are evaluated. Many actions override other actions.
phase_action_priority = [
    GuardAction,
    HideAction,
    KillAction,
    UnstoppableKillAction
]
