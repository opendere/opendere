from numpy import random

from opendere import roles


def weighted_choices(choice_weight_map, num_choices):
    choices = sorted(choice_weight_map)
    weight_sum = sum(choice_weight_map.values())
    probabilities = [choice_weight_map[c] / weight_sum for c in choices]
    return random.choice(choices, num_choices, p=probabilities)

class User:
    def __init__(self, hostmask):
        """
        hostmask (list[str]): a list of the hostmasks used to track disconnects/reconnects
        role (Role): the player's role
        alignment (Alignment): the player's alignment, potentially changed from the default
        alive (bool): whether a player is dead or alive
        vote (str): whom if anyone the player has voted for
        """
        self.hostmask = [hostmask]
        self.role = roles.Civilian
        self.alignment = self.role.default_alignment
        self.alive = True
        self.vote = str() 

class Game:
    def __init__(self, name='opendere', channel='#opendere', prefix=']', allow_late=False):
        """
        name (str): the name of the game; may want to move this elsewhere for themes... 
        channel (str): the channel in which the game commands are to be sent
        prefix (str): the prefix used for game commands
        ticks (int): seconds until the end of the current phase
        users (dict[str]User): players who've joined the game
        allow_late (bool): whether a player can join the game during the first phase
        phase (int): current phase (1 day and 1 night is 2 phases)
        hurry_requested_users (list[str]): users who've requested the phase be hurried
        """
        self.name = name
        self.channel = channel
        self.prefix = prefix
        self.ticks = -1
        self.users = {}
        self.allow_late = allow_late
        self.phase = -1
        self.hurry_requested_users = []

    def _start_game(self):
        """
        initialize and start a new game
        """
        self.phase, self.ticks = 0, -1
        # get set of N roles, and apply them randomly to users
        # TODO: rejigger this
        roles = self._select_roles(len(self.users))
        self.user_roles = {username: role for username, role in zip(usernames, random.shuffle(roles))}

    @staticmethod
    def _select_roles(num_users):
        """
        Select N roles for the players of the game
        """
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

        if num_users <= 3:
            raise ValueError('A game requires at least 4 players')

        elif num_users <= 5:
            # choose 1 yandere, 3 to 4 good-aligned roles
            role_classes = random.choice(
                [r for r in roles.all_role_classes if r.is_yandere],
                size=1
            )
            role_classes += weighted_choices(weighted_good_role_classes, num_users - 1)
            return [r() for r in role_classes]

        elif num_users <= 8:
            # choose 2 yandere, 6, 7, or 8 non-yandere roles
            role_classes = random.choice([r for r in all_role_classes if r.is_yandere], 2)
            role_classes += weighted_choices(weighted_good_and_neutral_role_classes, num_users - 2)
            return [r() for r in role_classes]

    def _is_first_phase_day(self):
        """
        algorithm: odd numbers = night
        """
        return len(self.users) % 2 == 1

    def _get_phase_name(self) -> str:
        return "night" if (self.phase + self._is_first_phase_day) % 2 else "day"

    def _phase_change(self):
        """
        handle events that happen during a phase change
        """
        pass

    def join_game(self, user, hostmask) -> list:
        """
        join an existing (or create a new) opendare game. returns a list of messages to send to players
        """
        messages = list()

        if not self.users:
            # the first player to join kicks off the announcement and sets a timer
            self.ticks = 60
            messages.append((self.channel, f"a {self.name} game is starting in {self.ticks} seconds! please type {self.prefix}{self.name} to join!"))

        if user in self.users:
            # player is already in the game
            if self.phase < 0:
                messages.append((user, f"you're already joined the current game, with {len(self.users)} players, starting in {self.ticks} seconds."))
            else:
                messages.append((user, f"you're already playing in the current game."))

        if user not in self.users:
            if self.phase < 0:
                self.users[user] = User(hostmask)
                messages.append((user, f"you've joined the current game, with {len(self.users)} players, starting in {self.ticks} seconds."))
            elif self.phase == 0 and self.allow_late:
                self.users[user] = User(hostmask)
                # TODO: assign a random role if joining late during the first phase...
                messages.append((self.channel, f"suspicious slow-poke {nick} joined the game late."))
                messages.append((user, f"you've joined the current game with role {self.users[nick].role.name} - {self.users[nick].role.description}"))
            else:
                messages.append((user, f"sorry, you cannot join a game that is already in progress. please wait for the current game to complete before trying again."))
        return messages
 
    def tick(self):
        if self.ticks > 0:
            self.ticks -= 1
        if self.ticks == 0:
            if self.phase < 0:
                # TODO: self._start_game()
                pass
            else:
                # TODO: self._phase_change()
                pass

    def user_action(self, user, action):
        """
        determines whether a user has the ability to take an action, then executes the action
        """
        pass

    def user_hurry(self, user) -> list:
        """
        request that the game be hurried
        """
        messages = list()
        if self.ticks < 0 and self.phase >= 0:
            self.ticks = 60
            messages.append((self.channel, f"people are getting impatient! the {self._get_phase_name()} roles have {self.ticks} seconds to make their decision before the {self._get_phase_name()} ends."))
        else:
            messages.append((user, f"you can't hurry the game right now."))
        return messages
