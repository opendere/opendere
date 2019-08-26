from enum import Enum
import inspect
import math
from numpy import random

class Alignment(Enum):
    good = 0
    evil = 1
    neutral = 2


class Phase(Enum):
    day = 0
    night = 1


class Ability:
    def __init__(self, num_uses=0, phases=[], command_public=False):
        """
        num_ability_uses (int): the number of times the ability can be used per game, usually either 0, 1 or infinity
        phases (List[Phase]): when the ability can be used. day, night or both
        command_public (boolean): determines whether the action is executed through private message or in the channel
        """
        self.num_uses = num_uses
        self.phases = phases
        self.command_public = command_public

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
    def __call__(self):
        pass


class HideAbility(Ability):
    name = 'hide'
    action_description = 'hide from killers'
    command = 'hide'
    def __call__(self, user):
        pass


class RevealAbility(Ability):
    name = 'reveal'
    action_description = 'reveal to all other players'
    command = 'reveal'
    def __call__(self, user):
        pass


class SpyAbility(Ability):
    name = 'spy'
    action_description = 'inspect another player\'s role'
    command = 'spy <user>'
    def __call__(self, user):
        pass


class StalkAbility(Ability):
    name = 'stalk'
    action_description = 'learn where another player goes'
    command = 'stalk <user>'
    def __call__(self, user):
        pass


class CheckAbility(Ability):
    name = 'check'
    action_description = 'inspect another players alignment'
    command = 'check <user>'
    def __call__(self, user):
        pass


class GuardAbility(Ability):
    name = 'guard'
    action_description = 'protect a player from any danger'
    command = 'guard <user>' 
    def __call__(self, user):
        pass

class KillAbility(Ability):
    name = 'kill'
    action_description = 'single-handedly kill a player of their choosing'
    command = 'kill <user>'
    def __call__(self, user):
        pass


class VoteKillAbility(Ability):
    """
    vote to kill someone with your voting cohort
    your cohort consists of your unique (command_public, phase) combination,
    that means public-command day voters vote together (typical lynching)
    """
    name = 'vote to kill'
    action_description = 'vote with others to kill'
    command = 'vote <user>'
    def __call__(self, user):
        pass


class Role:
    """
    name (string): name of the role
    is_yandare (boolean): killing all the yandere wins the game
    default_alignment (boolean): the alignment at the start of game
    ability (Ability): the ability of the role
    upgrades (list[Role]): the possible roles that can be upgraded to
    appearance (list[str]): the list of possible appearances a role can have to spies
    safe_to_guard (boolean): whether GuardAbility dies when guarding you
    """
    name = None
    is_yandere = None
    default_alignment = None
    abilities = []
    upgrades = []
    appearances = None
    safe_to_guard = True

    def __init__(self):
        assert isinstance(self.name, str)
        assert isinstance(self.is_yandere, bool)
        assert isinstance(self.default_alignment, Alignment)
        assert isinstance(self.safe_to_guard, bool)

        self.abilities = list(self.abilities)
        self.upgrades = list(self.upgrades)
        self.appearances = self.appearances or [self.name]
        self.appear_as = random.choice(self.appearances)

    @property
    def description(self):
        # TODO: "Be careful of disguised roles like traps and tsunderes which will be misreported."
        return "a {} has the ability to {}. {}{}".format(
            self.name,
            ', and to '.join([ability.description for ability in self.abilities if not ability.command_public]) or '...do nothing special. :( sorry',
            "be careful of disguised roles which may appear as other roles. " if 'spy' in [ability.name for ability in self.abilities] else '',
            f'you appear as a {self.appear_as}.' if self.appear_as != self.name else ''
        )
# TODO: change all classes to PARTIALS


class Hikikomori(Role):
    name = 'hikikomori'
    is_yandere = False
    default_alignment = Alignment.good
    abilities = [
        HideAbility(num_uses=math.inf, phases=[Phase.night]),
        VoteKillAbility(num_uses=math.inf, phases=[Phase.day], command_public=True),
    ]


class Tokokyohi(Role):
    name = 'tokokyohi'
    is_yandere = False
    default_alignment = Alignment.good
    abilities = [
        HideAbility(num_uses=1, phases=[Phase.night]),
        VoteKillAbility(num_uses=math.inf, phases=[Phase.day], command_public=True),
    ]
    upgrades = [Hikikomori]


class Shogun(Role):
    name = 'shogun'
    is_yandere = False
    default_alignment = Alignment.good
    abilities = [
        KillAbility(num_uses=math.inf, phases=[Phase.night]),
        VoteKillAbility(num_uses=math.inf, phases=[Phase.day], command_public=True),
    ]


class Warrior(Role):
    name = 'warrior'
    is_yandere = False
    default_alignment = Alignment.good
    abilities = [
        KillAbility(num_uses=1, phases=[Phase.night]),
        VoteKillAbility(num_uses=math.inf, phases=[Phase.day], command_public=True),
    ]
    upgrades = [Shogun]


class Samurai(Role):
    name = 'ronin'
    is_yandere = False
    default_alignment = Alignment.good
    abilities = [
        KillAbility(num_uses=math.inf, phases=[Phase.day]),
        VoteKillAbility(num_uses=math.inf, phases=[Phase.day], command_public=True),
    ]


class Ronin(Role):
    name = 'ronin'
    is_yandere = False
    default_alignment = Alignment.good
    abilities = [
        KillAbility(num_uses=1, phases=[Phase.day]),
        VoteKillAbility(num_uses=math.inf, phases=[Phase.day], command_public=True),
    ]
    upgrades = [Samurai],


class Shisho(Role):
    name = 'shisho'
    is_yandere = False
    default_alignment = Alignment.good
    abilities = [
        UpgradeAbility(num_uses=math.inf, phases=[Phase.day]),
        VoteKillAbility(num_uses=math.inf, phases=[Phase.day], command_public=True),
    ]


class Sensei(Role):
    name = 'sensei'
    is_yandere = False
    default_alignment = Alignment.good
    abilities = [
        UpgradeAbility(num_uses=1, phases=[Phase.day]),
        VoteKillAbility(num_uses=math.inf, phases=[Phase.day], command_public=True),
    ]
    upgrades = [Shisho],


class Idol(Role):
    name = 'idol'
    is_yandere = False
    default_alignment = Alignment.good
    abilities = [
        RevealAbility(num_uses=math.inf, phases=[Phase.day]),
        VoteKillAbility(num_uses=math.inf, phases=[Phase.day], command_public=True),
    ]
    upgrades = [Sensei, Ronin],


class Janitor(Role):
    name = 'janitor'
    is_yandere = False
    default_alignment = Alignment.good
    abilities = [
        VoteKillAbility(num_uses=math.inf, phases=[Phase.day], command_public=True),
    ]
    upgrades = [Idol]


class Spy(Role):
    name = 'spy'
    is_yandere = False
    default_alignment = Alignment.good
    abilities = [
        SpyAbility(num_uses=math.inf, phases=[Phase.night]),
        VoteKillAbility(num_uses=math.inf, phases=[Phase.day], command_public=True),
    ]


class DaySpy(Role):
    name = 'spy'
    is_yandere = False
    default_alignment = Alignment.good
    abilities = [
        SpyAbility(num_uses=math.inf, phases=[Phase.day]),
        VoteKillAbility(num_uses=math.inf, phases=[Phase.day], command_public=True),
    ]


class Esper(Role):
    name = 'esper'
    is_yandere = False
    default_alignment = Alignment.good
    abilities = [
        SpyAbility(num_uses=1, phases=[Phase.day, Phase.night]),
        VoteKillAbility(num_uses=math.inf, phases=[Phase.day], command_public=True),
    ]
    upgrades = [Spy, DaySpy]


class Stalker(Role):
    name = 'stalker'
    is_yandere = False
    default_alignment = Alignment.good
    abilities = [
        StalkAbility(num_uses=math.inf, phases=[Phase.night]),
        VoteKillAbility(num_uses=math.inf, phases=[Phase.day], command_public=True),
    ]


class Witness(Role):
    name = 'witness'
    is_yandere = False
    default_alignment = Alignment.good
    abilities = [
        StalkAbility(num_uses=1, phases=[Phase.night]),
        VoteKillAbility(num_uses=math.inf, phases=[Phase.day], command_public=True),
    ]
    upgrades = [Stalker]


class Detective(Role):
    name = 'detective'
    is_yandere = False
    default_alignment = Alignment.good
    abilities = [
        CheckAbility(num_uses=math.inf, phases=[Phase.night]),
        VoteKillAbility(num_uses=math.inf, phases=[Phase.day], command_public=True),
    ]
    appearances = ['yandere', 'yandere spy', 'yandere doppelganger', 'strawberry yandere']


class Snoop(Role):
    name = 'snoop'
    is_yandere = False
    default_alignment = Alignment.good
    abilities = [
        CheckAbility(num_uses=1, phases=[Phase.night]),
        VoteKillAbility(num_uses=math.inf, phases=[Phase.day], command_public=True),
    ]
    upgrades = [Detective]
    appearances = ['yandere', 'psychic yandere', 'yandere doppelganger', 'vanilla yandere', 'yandere senpai']


class Guardian(Role):
    name = 'guardian'
    is_yandere = False
    default_alignment = Alignment.good
    abilities = [
        GuardAbility(num_uses=math.inf, phases=[Phase.night]),
        VoteKillAbility(num_uses=math.inf, phases=[Phase.day], command_public=True),
    ]


class Nurse(Role):
    name = 'nurse'
    is_yandere = False
    default_alignment = Alignment.good
    abilities = [
        GuardAbility(num_uses=1, phases=[Phase.night]),
        VoteKillAbility(num_uses=math.inf, phases=[Phase.day], command_public=True),
    ]
    upgrades = [Guardian]


class Civilian(Role):
    name = 'civilian'
    is_yandere = False
    default_alignment = Alignment.good
    abilities = [
        VoteKillAbility(num_uses=math.inf, phases=[Phase.day], command_public=True),
    ]
    upgrades = [Tokokyohi, Warrior, Janitor, Esper, Witness, Snoop, Nurse]


class Tsundere(Role):
    name = 'tsundere'
    is_yandere = False
    default_alignment = Alignment.good
    abilities = [
        VoteKillAbility(num_uses=math.inf, phases=[Phase.day], command_public=True),
    ]
    upgrades = [Hikikomori]
    appearances = ['yandere', 'psychic yandere', 'yandere ronin', 'yandere senpai', 'yandere doppelganger', 'chocolate yandere']


class PsychicIdiot(Role):
    name = 'psychic idiot'
    is_yandere = False
    default_alignment = Alignment.neutral
    abilities = [
        SpyAbility(num_uses=math.inf, phases=[Phase.day, Phase.night]),
        VoteKillAbility(num_uses=math.inf, phases=[Phase.day], command_public=True),
    ]


class IdiotSavant(Role):
    name = 'idiot savant'
    is_yandere = False
    default_alignment = Alignment.neutral
    abilities = [
        UpgradeAbility(num_uses=math.inf, phases=[Phase.day]),
        VoteKillAbility(num_uses=math.inf, phases=[Phase.day], command_public=True),
    ]


class Myth(Role):
    name = 'myth'
    is_yandere = False
    default_alignment = Alignment.neutral
    abilities = [
        KillAbility(num_uses=math.inf, phases=[Phase.day]),
        VoteKillAbility(num_uses=math.inf, phases=[Phase.day], command_public=True),
    ]


class NullCarrier(Role):
    name = 'null carrier'
    is_yandere = False
    default_alignment = Alignment.neutral
    abilities = [
        HideAbility(num_uses=math.inf, phases=[Phase.night]),
        VoteKillAbility(num_uses=math.inf, phases=[Phase.day], command_public=True),
    ]


class BakaRanger(Role):
    name = 'baka ranger'
    is_yandere = False
    default_alignment = Alignment.neutral
    abilities = [
        VoteKillAbility(num_uses=math.inf, phases=[Phase.day], command_public=True),
    ]
    upgrades = [PsychicIdiot, IdiotSavant, Myth, NullCarrier],


class YandereSpy(Role):
    name = 'yandere spy'
    is_yandere = True
    default_alignment = Alignment.evil
    abilities = [
        SpyAbility(num_uses=math.inf, phases=[Phase.day]),
        VoteKillAbility(num_uses=math.inf, phases=[Phase.night]),
        VoteKillAbility(num_uses=math.inf, phases=[Phase.day], command_public=True),
    ]
    safe_to_guard = False


class YandereSenpai(Role):
    name = 'yandere senpai'
    is_yandere = True
    default_alignment = Alignment.evil
    abilities = [
        UpgradeAbility(num_uses=1, phases=[Phase.day]),
        VoteKillAbility(num_uses=math.inf, phases=[Phase.night]),
        VoteKillAbility(num_uses=math.inf, phases=[Phase.day], command_public=True),
    ]
    safe_to_guard = False


class YandereRonin(Role):
    name = 'yandere ronin'
    is_yandere = True
    default_alignment = Alignment.evil
    abilities = [
        KillAbility(num_uses=1, phases=[Phase.day]),
        VoteKillAbility(num_uses=math.inf, phases=[Phase.night]),
        VoteKillAbility(num_uses=math.inf, phases=[Phase.day], command_public=True),
    ]
    safe_to_guard = False


class PsychicYandere(Role):
    name = 'psychic yandere'
    is_yandere = True
    default_alignment = Alignment.evil
    abilities = [
        SpyAbility(num_uses=1, phases=[Phase.day]),
        VoteKillAbility(num_uses=math.inf, phases=[Phase.night]),
        VoteKillAbility(num_uses=math.inf, phases=[Phase.day], command_public=True),
    ]
    upgrades = [YandereSpy]
    safe_to_guard = False


class CloakedPsychicYandere(Role):
    name = 'cloaked psychic yandere'
    is_yandere = True
    default_alignment = Alignment.evil
    abilities = [
        SpyAbility(num_uses=1, phases=[Phase.day]),
        VoteKillAbility(num_uses=math.inf, phases=[Phase.night]),
        VoteKillAbility(num_uses=math.inf, phases=[Phase.day], command_public=True),
    ]
    appearances = ['civilian', 'dayspy', 'tokokyohi', 'hikikomori', 'nurse', 'guardian', 'warrior', 'esper', 'spy', 'shogun']
    safe_to_guard = True


class CloakedYandere(Role):
    name = 'cloaked yandere'
    is_yandere = True
    default_alignment = Alignment.evil
    abilities = [
        VoteKillAbility(num_uses=math.inf, phases=[Phase.night]),
        VoteKillAbility(num_uses=math.inf, phases=[Phase.day], command_public=True),
    ]
    upgrades = [CloakedPsychicYandere]
    appearances = ['civilian', 'tokokyohi', 'hikikomori', 'nurse', 'guardian', 'warrior', 'witness', 'stalker', 'shogun']
    safe_to_guard = True


class YandereDoppelganger(Role):
    name = 'yandere doppelganger'
    is_yandere = True
    default_alignment = Alignment.evil
    abilities = [
        VoteKillAbility(num_uses=math.inf, phases=[Phase.night]),
        VoteKillAbility(num_uses=math.inf, phases=[Phase.day], command_public=True),
    ]
    upgrades = [CloakedYandere]
    safe_to_guard = False


class Yandere(Role):
    name = 'yandere'
    is_yandere = True
    default_alignment = Alignment.evil
    abilities = [
        VoteKillAbility(num_uses=math.inf, phases=[Phase.night]),
        VoteKillAbility(num_uses=math.inf, phases=[Phase.day], command_public=True),
    ]
    upgrades = [YandereDoppelganger, CloakedYandere, PsychicYandere, YandereSpy, YandereRonin, YandereSenpai]
    safe_to_guard = False


class Trap(Role):
    name = 'trap'
    is_yandere = True
    default_alignment = Alignment.evil
    abilities = [
        VoteKillAbility(num_uses=math.inf, phases=[Phase.day], command_public=True),
    ]
    upgrades = [CloakedYandere, BakaRanger]
    appearances = ['civilian', 'tokokyohi', 'hikikomori', 'nurse', 'guardian', 'warrior', 'witness', 'snoop', 'detective']
    safe_to_guard = True


# hack
all_role_classes = [l for l in locals().values() if inspect.isclass(l) and issubclass(l, Role) and l != Role]
