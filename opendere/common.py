from enum import Enum
from opendere import action


class User:
    def __init__(self, game, uid, nick):
        """
        uid (str): the player's user identifier, such as nick!user@host for irc or discord's user.id
        nick (str): the player's nickname
        role (Role): the player's role
        alignment (Alignment): the player's alignment, potentially changed from the default
        is_alive (bool): whether a player is dead or alive
        is_hidden (bool): whether a player is hiding from the mean and scary yanderes ;_;
        """
        self.game = game
        self.uid = uid
        self.nick = nick
        self.role = None
        self.alignment = None
        self.is_alive = True

    def __str__(self):
        return self.nick

    @property
    def is_protected(self):
        for act in self.game.phase_actions + self.game.completed_actions:
            if isinstance(act, action.HideAction) and act.user == self:
                return True
            if isinstance(act, action.GuardAction) and act.target_user == self:
                return True
        return False

class Alignment(Enum):
    good = 0
    evil = 1
    neutral = 2


class Phase(Enum):
    day = 0
    night = 1
