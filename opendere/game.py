from numpy import random

from opendere import roles

def weighted_choices(choice_weight_map, num_choices):
    choices = list(choice_weight_map)
    weight_sum = sum(choice_weight_map.values())
    probabilities = [choice_weight_map[c] / weight_sum for c in choices]
    return list(random.choice(choices, (num_choices,), p=probabilities))

class User:
    def __init__(self, uid, nick):
        """
        uid (str): the player's user identifier, such as nick!user@host for irc or discord's user.id
        nick (str): the player's nickname
        role (Role): the player's role
        alignment (Alignment): the player's alignment, potentially changed from the default
        alive (bool): whether a player is dead or alive
        vote (str): whom if anyone the player has voted for
        """
        self.uid = uid
        self.nick = nick
        self.role = None
        self.alignment = None
        self.alive = True
        self.vote = str()

class Game:
    def __init__(self, channel='#opendere', prefix=']', allow_late=False):
        """
        channel (str): the channel in which the game commands are to be sent
        name (str): the name of the current game, probably will want to move this elsewhere for themes
        prefix (str): the prefix used for game commands
        ticks (int): seconds until the end of the current phase
        users (Dict[str, User]): players who've joined the game
        allow_late (bool): whether a player can join the game during the first phase
        phase (int): current phase (1 day and 1 night is 2 phases)
        hurry_requested_users (List[str]): users who've requested the phase be hurried
        """
        self.channel = channel
        self.name = channel.lstrip('#')
        self.prefix = prefix
        self.ticks = None
        self.users = {}
        self.allow_late = allow_late
        self.phase = None
        self.hurry_requested_users = []

    def reset(self):
        self.__init__()

    def _start_game(self):
        """
        initialize and start a new game
        """
        messages = list()
        self.phase, self.ticks = 0, None
        if len(self.users) <= 3:
            messages.append((self.channel, f"there aren't enough players to start a {self.name} game. try again later."))
            self.users = {}
            return messages

        roles = self._select_roles(len(self.users))
        random.shuffle(roles)
        for i, uid in enumerate(self.users):
            self.users[uid].role = roles[i]
            messages.append((uid, f"you're a {self.users[uid].role.name}. {self.users[uid].role.description}"))

        messages.append((self.channel, f"welcome to {self.name}. there are {len([uid for uid in self.users if self.users[uid].role.is_yandere])} yanderes. it's your job to determine the yanderes."))
        messages.append((self.channel, f"this game starts at {self.phase_name.upper()}. discuss!"))
        messages.append((self.channel, f"current players: {', '.join([self.users[uid].nick for uid in self.users])}."))

        return messages

    @staticmethod
    def _select_roles(num_users):
        """
        Select N roles for the players of the game
        """
        # why aren't these weights in roles.py instead? - libbies
        weighted_good_role_classes = {
            roles.Hikikomori: 1, roles.Tokokyohi: 2,
            roles.Shogun: 1, roles.Warrior: 2,
            roles.Samurai: 1, roles.Ronin: 2,
            roles.Shisho: 1, roles.Sensei: 2,
            roles.Idol: 1, roles.Janitor: 2,
            roles.Spy: 1, roles.DaySpy: 1, roles.Esper: 2,
            roles.Stalker: 1, roles.Witness: 2,
            roles.Detective: 1, roles.Snoop: 2,
            roles.Guardian: 1, roles.Nurse: 2,
            roles.Civilian: 3, roles.Tsundere: 3
        }
        weighted_neutral_role_classes = {r: 1 for r in roles.all_role_classes if r.default_alignment == roles.Alignment.neutral}
        weighted_good_and_neutral_role_classes = {
            **weighted_good_role_classes,
            **weighted_neutral_role_classes
        }
        unweighted_yanderes = {r: 1 for r in roles.all_role_classes if r.is_yandere}

        # possibly needs tweaking for balance:
        #  4-6  players: 1 yandere
        #  7-9  players: 2 yanderes
        # 10-12 players: 3 yanderes
        num_yanderes = (num_users - 1) // 3

        role_classes = list(random.choice(
            [role for role in roles.all_role_classes if role.is_yandere],
            size = num_yanderes
        ))

        role_classes += list(weighted_choices(weighted_good_and_neutral_role_classes, num_users - num_yanderes))
        return [role() for role in role_classes]

    def _is_first_phase_day(self):
        """
        algorithm: odd numbers = night
        """
        return len(self.users) % 2 == 1

    @property
    def phase_name(self):
        return "night" if (self.phase + len(self.users)) % 2 else "day"

    def _phase_change(self):
        """
        handle events that happen during a phase change
        """
        pass

    def join_game(self, uid, nick):
        """
        uid (str): a unique user identifier, such as nick!user@host for irc, or discord's user.id
        nick (str): the player's nickname
        """
        messages = list()

        if not self.users:
            self.ticks = 60
            messages.append((self.channel, f"a {self.name} game is starting in {self.ticks} seconds! please type {self.prefix}{self.name} to join!"))

        if uid in self.users:
            if self.phase is None:
                messages.append((uid, f"you're already in the current game, which is starting in {self.ticks} seconds."))
            else:
                messages.append((uid, f"you're already playing in the current game."))

        elif uid not in self.users:
            if self.phase is None:
                self.users[uid] = User(uid, nick)
                messages.append((uid, f"you've joined the current game, which is starting in {self.ticks} seconds."))

            # allow a player to join the game late if it's the very first phase of the game
            elif self.allow_late and self.phase == 0:
                self.users[uid] = User(uid, nick)
                # TODO: assign a random role if joining late...
                messages.append((self.channel, f"suspicious slow-poke {nick} joined the game late."))
                messages.append((user, f"you've joined the current game with role {self.users[uid].role.name} - {self.users[uid].role.description}"))

            else:
                messages.append((uid, f"sorry, you can't join a game that's already in-progress. please wait for the next game."))
        return messages

    def tick(self):
        if self.ticks == None:
            return

        if self.ticks:
            self.ticks -= 1

        if self.ticks == 0:
            self.ticks = None
            if self.phase == None:
                return self._start_game()
            else:
                # TODO: self._phase_change()
                pass

    def user_action(self, user, action):
        """
        determines whether a user has the ability to take an action, then executes the action
        """
        pass

    def user_hurry(self, user):
        """
        request that the game be hurried
        """
        messages = list()
        if self.ticks == None and self.phase >= 0:
            self.ticks = 60
            messages.append((self.channel, f"people are getting impatient! the {self._get_phase_name()} roles have {self.ticks} seconds to make their decisions before the {self._get_phase_name()} ends."))
        else:
            messages.append((user, f"you can't hurry the game right now."))
        return messages
