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
        is_alive (bool): whether a player is dead or alive
        is_hidden (bool): whether a player is hiding from the mean and scary yanderes ;_;
        """
        self.uid = uid
        self.nick = nick
        self.role = None
        self.alignment = None
        self.is_alive = True
        self.is_hidden = False

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
        hurries (List[User]): users who've requested the phase be hurried
        votes (Dict[User, User]): users and who've they've voted to kill
        actions (Dict[User, (Ability, User)]): abilities queued to execute at the end of phase (e.g. hides, kills, checks)
        """
        self.channel = channel
        self.bot = bot
        self.name = name
        self.prefix = prefix
        self.allow_late = allow_late
        self.users = {}
        self.ticks = None
        self.phase = None
        self.hurries = []
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
            messages.append((self.channel, f"there aren't enough players to start a game of opendere in {self.channel}. please try again later."))
            self.__init__(channel=None, bot=None, name=None)
            return messages

        roles = self._select_roles(len(self.users))
        random.shuffle(roles)
        for i, user in enumerate(self.users.values()):
            user.role = roles[i]
            messages.append((user.uid, f"you're a {user.role.name}. {user.role.description}"))

        messages.append((self.channel, "welcome to opendere. There {} {} {}. it's your job to determine who the {} {}.".format(
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
            size=num_yanderes
        ))

        role_classes += list(weighted_choices(weighted_good_and_neutral_role_classes, num_users - num_yanderes))
        return [role() for role in role_classes]

    @property
    def phase_name(self) -> str:
        """
        the name of the current phase...
        """
        return "setup" if self.phase is None else ("night" if (self.phase + len(self.users)) % 2 else "day")

    @property
    def day_num(self) -> int:
        """
        the current day as a number, e.g. "it is Day 2". nights can start from 0
        """
        return (2 - (len(self.users) % 2) + self.phase) // 2

    @property
    def players_alive(self) -> int:
        """
        number of players still alive
        """
        return len([user for user in self.users.values() if user.is_alive])

    @property
    def yanderes_alive(self) -> int:
        """
        number of yanderes still alive
        """
        return len([user for user in self.users.values() if user.is_alive and user.role.is_yandere])

    @property
    def yandere_killers(self) -> int:
        """
        number of yanderes who can kill, i.e. not traps
        """
        return len([user for user in self.users.values() if user.is_alive and user.role.is_yandere for ability in user.role.abilities if ability.name == 'vote' for phase in ability.phases if phase.name == 'night'])

    @property
    def list_votes(self):
        """
        a list of votes and count of each
        """
        votes = "current votes are: "
        for vote in {vote for vote in self.votes.values() if vote}:
            votes += f"{vote.nick}: {[vote for vote in self.votes.values()].count(vote)}, "
        votes += f"abstained: {list(self.votes.values()).count(None)}, "
        votes += f"undecided: {(self.players_alive if self.phase_name == 'day' else self.yandere_killers) - len(self.votes)}"
        return votes

    def _nick_change(self, uid, new_uid, nick, new_nick):
        """
        handle nickname changes
        discord user.id will always stay the same, but nick or name can change so we should track those
        irc hostmask nick!user@host can change, so we should split into a three tuple, and match on any two
        """
        # TODO: handle nickname changes. i still don't know what do about untypeable nicks on discord though
        pass

    def _phase_change(self):
        """
        handle events that happen during a phase change
        """
        messages = list()

        target = self.tally_votes()
        if self.phase_name == 'day':
            if target is None:
                messages.append((self.channel, f"you abstain from killing anyone."))
            elif self.phase_name == 'day' and target is not None:
                target.is_alive = False
                messages.append((self.channel, f"you lynch {target.nick} and it turns out they were{'' if target.role.is_yandere else ' NOT'} a yandere!"))
            messages.append((self.channel, f"dusk sets on the NIGHT of day {self.day_num}. there are {self.yanderes_alive} {'yandere' if self.yanderes_alive == 1 else 'yanderes'} still at large."))
            messages.append((self.channel, f"please PM/notice {self.bot} with any night-time commands you may have, or with 'abstain' to abstain."))
            # TODO: random alignment changes, possibly becoming yanderes in the process
            self.phase += 1
        elif self.phase_name == 'night':
            # TODO: night-time hiding and guarding goes here
            # TODO: night-time killings go here
            if target is not None and not target.is_hidden:
                target.is_alive = False
                # needs like a random.choice(list_of_death_reasons)
                messages.append((self.channel, f"{target.nick} was found brutually murdered D:"))
            # TODO: spying/checking/witnessing goes here
            # TODO: reset hiding/guarding
            if not messages:
                messages.append((self.channel, f"...it seems everyone survived the night. it is a brand new day :D"))
            else:
                random.shuffle(messages)
                messages.insert(0, (self.channel, f"morning comes with the stench of death."))
            self.phase += 1
            messages.append((self.channel, f"dawn rises on DAY {self.day_num}. there are {self.yanderes_alive} {'yandere' if self.yanderes_alive == 1 else 'yanderes'} still at large."))

        # reset everything else for the next phase
        self.ticks = None
        self.hurries = list()
        self.votes = dict()
        self.actions = dict()

        return messages

    def get_user(self, nick):
        """
        return the User object by uid or nick if found and still alive
        """
        if nick in self.users and self.users[nick].is_alive:
            return self.users[nick]
        return next((user for user in self.users.values() if nick.lower() == user.nick.lower() and user.is_alive), None)

    def join_game(self, uid, nick):
        """
        uid (str): a unique user identifier, such as nick!user@host for irc, or discord's user.id
        nick (str): the player's nickname
        """
        messages = list()

        if not self.users:
            self.ticks = 60
            messages.append((self.channel, f"an opendere game is starting in {self.channel} in {self.ticks} seconds! please type !opendere to join!"))

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
                # a 1 in 6 chance of being a yandere
                self.users[uid].role = random.choice(self._select_roles(6))
                messages.append((self.channel, f"suspicious slow-poke {nick} joined the game late."))
                messages.append((uid, f"you've joined the current game with role {self.users[uid].role.name} - {self.users[uid].role.description}"))

            else:
                messages.append((uid, f"sorry, you can't join a game that's already in-progress. please wait for the next game."))
        return messages

    def tick(self):
        if not self.ticks:
            return

        self.ticks -= 1
        if self.ticks == 0:
            if self.phase_name == "setup":
                return self._start_game()
            return self._phase_change()

    def user_action(self, uid, action, channel=None):
        """
        determines whether a user has the ability to take an action, then executes the action
        """
        if channel and not action.startswith(self.prefix):
            return
        action = action.lstrip(self.prefix)

        if self.phase_name == "setup":
            return
        if channel and self.phase_name == "night":
            return [(self.channel, f"commands in the channel are ignored at night. please PM/notice {self.bot} with your commands instead.")]

        action = action.lstrip('opendere').lstrip(self.name).split(maxsplit=1)
        for ability in self.users[uid].role.abilities:
            # maybe change ability.name to a list, so we can use that as a list of command aliases?
            if action[0].lower() != ability.name or self.phase_name not in [phase.name for phase in ability.phases]:
                continue
            elif channel and not ability.command_public:
                return [(uid, f"please PM/notice {self.bot} with your commands instead.")]
            elif ability.command_public and not channel:
                return [(uid, f"please enter that command in {self.channel} instead.")]
            else:
                if action[1] in ['a', 'u', 'abstain', 'undecided']:
                    target = action[1]
                else:
                    target = self.get_user(action[1])
                if target is None:
                    return [(uid, f"invalid target '{action[1]}' for command {action[0]}. please try again.")]
                return ability(self, self.get_user(uid), target)

    def reset(self):
        self.__init__(channel=None, bot=None, name=None)

    def user_hurry(self, uid):
        """
        request that the game be hurried
        """
        messages = list()

        # TODO: implement voting for hurrying

        if uid not in self.users:
            messages.append((self.channel, f"you're not playing in the current game."))

        elif not self.ticks and self.phase >= 0:
            self.ticks = 60
            messages.append((self.channel, f"people are getting impatient! the {self.phase} roles have {self.ticks} seconds to make their decisions before the {self.phase} ends."))

        else:
            messages.append((uid, f"you can't hurry the game right now."))
        return messages

    def tally_votes(self):
        counts = sorted({vote: list(self.votes.values()).count(vote) for vote in set(self.votes.values())}.items(), key=lambda x: x[1], reverse=True)
        # no one voted
        if not counts:
            target = None
        # only one person was voted for
        elif len(counts) == 1:
            target = counts[0][0]
        # one person has the most votes
        elif counts[0][1] > counts[1][1]:
            target = counts[0][0]
        # otherwise, at night, the first yandere to vote for someone (i.e. not abstain) wins
        elif self.phase_name == 'night':
            for target in iter(self.votes.values()):
                if target is not None:
                    return target
            return None
        # otherwise, everyone survives
        else:
            target = None
        return target
