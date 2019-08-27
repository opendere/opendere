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
        self.is_alive = True

class Game:
    def __init__(self, channel, bot, name, prefix='!', allow_late=False):
        """
        channel (str): the channel in which the game commands are to be sent
        bot (str): the name of the bot running the game
        name (str): the name of the current game, may want to move this elsewhere for themes
        prefix (str): the prefix used for game commands
        allow_late (bool): whether a player can join the game during the first phase
        users (Dict[str, User]): players who've joined the game
        ticks (int): seconds until the end of the current phase
        phase (int): current phase (1 day and 1 night is 2 phases)
        hurry_requested_users (List[str]): users who've requested the phase be hurried
        votes (Dict[User, User]): users and who've they've voted to kill
        actions (Dict[User, Ability]): abilities queued to execute at the end of phase (e.g. hides, kills, checks)
        """
        self.channel = channel
        self.bot = bot 
        self.name = name
        self.prefix = prefix
        self.allow_late = allow_late
        self.users = {}
        self.ticks = None
        self.phase = None
        self.hurry_requested_users = []
        # maybe should be moved to User for `[user.vote for user in self.users.values()]` instead
        self.votes = {}
        self.actions = {}

    def _start_game(self):
        """
        initialize and start a new game
        """
        messages = list()
        self.phase, self.ticks = 0, None
        if len(self.users) <= 3:
            messages.append((self.channel, f"there aren't enough players to start a {self.name} game. try again later."))
            self.__init__(channel=None, bot=None, name=None)
            return messages

        roles = self._select_roles(len(self.users))
        random.shuffle(roles)
        for i, user in enumerate(self.users):
            self.users[user].role = roles[i]
            messages.append((user, f"you're a {self.users[user].role.name}. {self.users[user].role.description}"))

        messages.append((self.channel, "welcome to {}. There {} {} {}. it's your job to determine who the {} {}.".format(
                    self.name,
                    'is' if self.yanderes_alive == 1 else 'are',
                    self.yanderes_alive,
                    'yandere' if self.yanderes_alive == 1 else 'yanderes',
                    'yandere' if self.yanderes_alive == 1 else 'yanderes',
                    'is' if self.yanderes_alive == 1 else 'are'
        )))

        if len(self.users) % 2:
            messages.append((self.channel, f"this game starts on the {self.phase_name.upper()} of day {self.day_num}. if you have a night role, please send {self.bot} a private message with any commands you may have, or with 'abstain' to abstain from using any abilities."))

        else:
            messages.append((self.channel, f"this game starts on {self.phase_name.upper()} {self.day_num}. discuss!"))
        messages.append((self.channel, f"current players: {', '.join([user.nick for user in self.users.values()])}."))

        return messages

    @staticmethod
    def _select_roles(num_users):
        """
        Select N roles for the players of the game
        """
        # why aren't these weights in roles.py instead? - libbies
        weighted_good_role_classes = {
            roles.Hikikomori: 2, roles.Tokokyohi: 4,
            roles.Shogun: 2, roles.Warrior: 4,
            roles.Samurai: 2, roles.Ronin: 4,
            roles.Shisho: 2, roles.Sensei: 4,
            roles.Idol: 2, roles.Janitor: 4,
            roles.Spy: 1, roles.DaySpy: 1, roles.Esper: 4,
            roles.Stalker: 2, roles.Witness: 4,
            roles.Detective: 2, roles.Snoop: 4,
            roles.Guardian: 2, roles.Nurse: 4,
            roles.Civilian: 6, roles.Tsundere: 6
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

    @property
    def phase_name(self) -> str:
        """
        the name of the current phase...
        """
        return "night" if (self.phase + len(self.users)) % 2 else "day"

    @property
    def day_num(self) -> int:
        """
        the current day as a number, e.g. "it is Day 2". nights start with 0
        """
        return (2 - (len(self.users) % 2) + self.phase) // 2

    @property
    def players_alive(self) -> int:
        """
        number of yanderes still alive
        """
        return len([user for user in self.users.values() if user.is_alive])

    @property
    def yanderes_alive(self) -> int:
        """
        number of yanderes still alive
        """
        return len([user for user in self.users.values() if user.is_alive and user.role.is_yandere])

    @property
    def list_votes(self):
        """
        a list of votes and count of each
        """
        if not self.votes:
            return str() 
        votes = "current votes are: " 
        # i don't really like how this looks... - libbies 
        for vote in set([vote.nick for vote in self.votes.values() if vote]):
            votes += f"{vote}: {[vote.nick if vote else 'abstain' for vote in self.votes.values()].count(vote)}, " 
        for vote in [None for vote in self.votes.values() if vote is None]:
            votes += f"abstain: {[vote.nick if vote else 'abstain' for vote in self.votes.values()].count(vote)}, " 
        votes += f"undecided: {len(self.users) - len(self.votes)}"
        return votes

    def _phase_change(self):
        """
        handle events that happen during a phase change
        """
        pass

    def get_user(self, nick):
        """
        return the User object by uid or nick if found
        """
        if nick in self.users:
            return self.users[nick]
        for user in self.users.values():
            if nick.lower() == user.nick.lower():
                return user 
        return None

    def join_game(self, user, nick):
        """
        user (str): a unique user identifier, such as nick!user@host for irc, or discord's user.id
        nick (str): the player's nickname
        """
        messages = list()

        if not self.users:
            self.ticks = 60
            messages.append((self.channel, f"a {self.name} game is starting in {self.ticks} seconds! please type {self.prefix}{self.name} to join!"))

        if user in self.users:
            if self.phase is None:
                messages.append((user, f"you're already in the current game, which is starting in {self.ticks} seconds."))
            else:
                messages.append((user, f"you're already playing in the current game."))

        elif user not in self.users:
            if self.phase is None:
                self.users[user] = User(user, nick)
                messages.append((user, f"you've joined the current game, which is starting in {self.ticks} seconds."))

            # allow a player to join the game late if it's the very first phase of the game
            elif self.allow_late and self.phase == 0:
                self.users[user] = User(user, nick)
                # a 1 in 6 chance of being a yandere
                self.users[user].role = random.choice(self._select_roles(6))
                messages.append((self.channel, f"suspicious slow-poke {nick} joined the game late."))
                messages.append((user, f"you've joined the current game with role {self.users[user].role.name} - {self.users[user].role.description}"))

            else:
                messages.append((user, f"sorry, you can't join a game that's already in-progress. please wait for the next game."))
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

    def user_action(self, user, action, channel=None, nick=None):
        """
        determines whether a user has the ability to take an action, then executes the action
        """
        if channel and not action.startswith(self.prefix):
            return
        elif action.startswith(self.prefix):
            action = action.lstrip(self.prefix)

        if channel:
            if action.lower() == self.name.lower():
                return self.join_game(user, nick) 
            elif action.lower() in ['end', 'reset', 'restart']:
                return self.reset()
            elif action.lower() in ['h', 'hurry']:
                return self.user_hurry(user)
            elif self.phase_name == "night":
                return [(self.channel, f"commands in the channel are ignored at night. please PM/notice {self.bot} with your commands instead.")]
            # aliases that are user actions should probably be moved to the ability instead...
            elif action.lower() in ['u', 'unvote']:
                return self.user_action(user, 'vote undecided', channel)
            elif action.lower() in ['a', 'abstain']:
                return self.user_action(user, 'vote abstain', channel)

        action = action.lstrip(self.name).split(maxsplit=1)
        for ability in self.users[user].role.abilities:
            # maybe change ability.name to a list, so we can use that as a list of command aliases?
            if action[0].lower() != ability.name or self.phase_name not in [phase.name for phase in ability.phases]:
                continue
            elif channel and not ability.command_public:
                return [(user, f"please PM/notice {self.bot} with your commands instead.")]
            elif ability.command_public and not channel:
                return [(user, f"please enter that command in {self.channel} instead.")]
            else:
                return ability(self, user, action[1])

    def reset(self):
        messages = list()
        messages.append((self.channel, f"the current game of {self.name} has ended or been reset."))
        self.__init__(channel=None, bot=None, name=None)
        return messages

    def user_hurry(self, user):
        """
        request that the game be hurried
        """
        messages = list()

        if user not in self.users:
            messages.append((self.channel, f"you're not playing in the current game."))

        elif self.ticks == None and self.phase >= 0:
            self.ticks = 60
            messages.append((self.channel, f"people are getting impatient! the {self.phase} roles have {self.ticks} seconds to make their decisions before the {self.phase} ends."))

        else:
            messages.append((user, f"you can't hurry the game right now."))
        return messages
