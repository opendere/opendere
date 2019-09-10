import inspect
import math
from numpy import random

from opendere import ability
from opendere.common import Alignment, Phase


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
        return "a {} can {}. {}".format(
            self.name,
            ', and can '.join([ab.description for ab in self.abilities if not ab.command_public]) or '...do nothing special. :( sorry',
            f'you appear as a {self.appear_as}.' if self.is_yandere and self.appear_as != self.name else ''
        )
# TODO: change all classes to PARTIALS


class Hikikomori(Role):
    name = 'hikikomori'
    is_yandere = False
    default_alignment = Alignment.good
    abilities = [
        ability.HideAbility(num_uses=math.inf, phases=[Phase.night]),
        ability.VoteKillAbility(num_uses=math.inf, phases=[Phase.day], command_public=True),
    ]


class Tokokyohi(Role):
    name = 'tokokyohi'
    is_yandere = False
    default_alignment = Alignment.good
    abilities = [
        ability.HideAbility(num_uses=1, phases=[Phase.night]),
        ability.VoteKillAbility(num_uses=math.inf, phases=[Phase.day], command_public=True),
    ]
    upgrades = [Hikikomori]


class Shogun(Role):
    name = 'shogun'
    is_yandere = False
    default_alignment = Alignment.good
    abilities = [
        ability.KillAbility(num_uses=math.inf, phases=[Phase.night]),
        ability.VoteKillAbility(num_uses=math.inf, phases=[Phase.day], command_public=True),
    ]


class Warrior(Role):
    name = 'warrior'
    is_yandere = False
    default_alignment = Alignment.good
    abilities = [
        ability.KillAbility(num_uses=1, phases=[Phase.night]),
        ability.VoteKillAbility(num_uses=math.inf, phases=[Phase.day], command_public=True),
    ]
    upgrades = [Shogun]


class Samurai(Role):
    name = 'samurai'
    is_yandere = False
    default_alignment = Alignment.good
    abilities = [
        ability.KillAbility(num_uses=math.inf, phases=[Phase.day]),
        ability.VoteKillAbility(num_uses=math.inf, phases=[Phase.day], command_public=True),
    ]


class Ronin(Role):
    name = 'ronin'
    is_yandere = False
    default_alignment = Alignment.good
    abilities = [
        ability.KillAbility(num_uses=1, phases=[Phase.day]),
        ability.VoteKillAbility(num_uses=math.inf, phases=[Phase.day], command_public=True),
    ]
    upgrades = [Samurai],


class Shisho(Role):
    name = 'shisho'
    is_yandere = False
    default_alignment = Alignment.good
    abilities = [
        ability.UpgradeAbility(num_uses=math.inf, phases=[Phase.day]),
        ability.VoteKillAbility(num_uses=math.inf, phases=[Phase.day], command_public=True),
    ]


class Sensei(Role):
    name = 'sensei'
    is_yandere = False
    default_alignment = Alignment.good
    abilities = [
        ability.UpgradeAbility(num_uses=1, phases=[Phase.day]),
        ability.VoteKillAbility(num_uses=math.inf, phases=[Phase.day], command_public=True),
    ]
    upgrades = [Shisho],


class Idol(Role):
    name = 'idol'
    is_yandere = False
    default_alignment = Alignment.good
    abilities = [
        ability.RevealAbility(num_uses=math.inf, phases=[Phase.day]),
        ability.VoteKillAbility(num_uses=math.inf, phases=[Phase.day], command_public=True),
    ]
    upgrades = [Sensei, Ronin],


class Janitor(Role):
    name = 'janitor'
    is_yandere = False
    default_alignment = Alignment.good
    abilities = [
        ability.VoteKillAbility(num_uses=math.inf, phases=[Phase.day], command_public=True),
    ]
    upgrades = [Idol]


class Spy(Role):
    name = 'spy'
    is_yandere = False
    default_alignment = Alignment.good
    abilities = [
        ability.SpyAbility(num_uses=math.inf, phases=[Phase.night]),
        ability.VoteKillAbility(num_uses=math.inf, phases=[Phase.day], command_public=True),
    ]


class DaySpy(Role):
    name = 'spy'
    is_yandere = False
    default_alignment = Alignment.good
    abilities = [
        ability.SpyAbility(num_uses=math.inf, phases=[Phase.day]),
        ability.VoteKillAbility(num_uses=math.inf, phases=[Phase.day], command_public=True),
    ]


class Esper(Role):
    name = 'esper'
    is_yandere = False
    default_alignment = Alignment.good
    abilities = [
        ability.SpyAbility(num_uses=1, phases=[Phase.day, Phase.night]),
        ability.VoteKillAbility(num_uses=math.inf, phases=[Phase.day], command_public=True),
    ]
    upgrades = [Spy, DaySpy]


class Stalker(Role):
    name = 'stalker'
    is_yandere = False
    default_alignment = Alignment.good
    abilities = [
        ability.StalkAbility(num_uses=math.inf, phases=[Phase.night]),
        ability.VoteKillAbility(num_uses=math.inf, phases=[Phase.day], command_public=True),
    ]


class Witness(Role):
    name = 'witness'
    is_yandere = False
    default_alignment = Alignment.good
    abilities = [
        ability.StalkAbility(num_uses=1, phases=[Phase.night]),
        ability.VoteKillAbility(num_uses=math.inf, phases=[Phase.day], command_public=True),
    ]
    upgrades = [Stalker]


class Detective(Role):
    name = 'detective'
    is_yandere = False
    default_alignment = Alignment.good
    abilities = [
        ability.CheckAbility(num_uses=math.inf, phases=[Phase.night]),
        ability.VoteKillAbility(num_uses=math.inf, phases=[Phase.day], command_public=True),
    ]
    appearances = ['yandere', 'yandere spy', 'yandere doppelganger', 'strawberry yandere']


class Snoop(Role):
    name = 'snoop'
    is_yandere = False
    default_alignment = Alignment.good
    abilities = [
        ability.CheckAbility(num_uses=1, phases=[Phase.night]),
        ability.VoteKillAbility(num_uses=math.inf, phases=[Phase.day], command_public=True),
    ]
    upgrades = [Detective]
    appearances = ['yandere', 'psychic yandere', 'yandere doppelganger', 'vanilla yandere', 'yandere senpai']


class Guardian(Role):
    name = 'guardian'
    is_yandere = False
    default_alignment = Alignment.good
    abilities = [
        ability.GuardAbility(num_uses=math.inf, phases=[Phase.night]),
        ability.VoteKillAbility(num_uses=math.inf, phases=[Phase.day], command_public=True),
    ]


class Nurse(Role):
    name = 'nurse'
    is_yandere = False
    default_alignment = Alignment.good
    abilities = [
        ability.GuardAbility(num_uses=1, phases=[Phase.night]),
        ability.VoteKillAbility(num_uses=math.inf, phases=[Phase.day], command_public=True),
    ]
    upgrades = [Guardian]


class Civilian(Role):
    name = 'civilian'
    is_yandere = False
    default_alignment = Alignment.good
    abilities = [
        ability.VoteKillAbility(num_uses=math.inf, phases=[Phase.day], command_public=True),
    ]
    upgrades = [Tokokyohi, Warrior, Janitor, Esper, Witness, Snoop, Nurse]


class Tsundere(Role):
    name = 'tsundere'
    is_yandere = False
    default_alignment = Alignment.good
    abilities = [
        ability.VoteKillAbility(num_uses=math.inf, phases=[Phase.day], command_public=True),
    ]
    upgrades = [Hikikomori]
    appearances = ['yandere', 'psychic yandere', 'yandere ronin', 'yandere senpai', 'yandere doppelganger', 'chocolate yandere']


class PsychicIdiot(Role):
    name = 'psychic idiot'
    is_yandere = False
    default_alignment = Alignment.neutral
    abilities = [
        ability.SpyAbility(num_uses=math.inf, phases=[Phase.day, Phase.night]),
        ability.VoteKillAbility(num_uses=math.inf, phases=[Phase.day], command_public=True),
    ]


class IdiotSavant(Role):
    name = 'idiot savant'
    is_yandere = False
    default_alignment = Alignment.neutral
    abilities = [
        ability.UpgradeAbility(num_uses=math.inf, phases=[Phase.day]),
        ability.VoteKillAbility(num_uses=math.inf, phases=[Phase.day], command_public=True),
    ]


class Myth(Role):
    name = 'myth'
    is_yandere = False
    default_alignment = Alignment.neutral
    abilities = [
        ability.KillAbility(num_uses=math.inf, phases=[Phase.day]),
        ability.VoteKillAbility(num_uses=math.inf, phases=[Phase.day], command_public=True),
    ]


class NullCarrier(Role):
    name = 'null carrier'
    is_yandere = False
    default_alignment = Alignment.neutral
    abilities = [
        ability.HideAbility(num_uses=math.inf, phases=[Phase.night]),
        ability.VoteKillAbility(num_uses=math.inf, phases=[Phase.day], command_public=True),
    ]


class BakaRanger(Role):
    name = 'baka ranger'
    is_yandere = False
    default_alignment = Alignment.neutral
    abilities = [
        ability.VoteKillAbility(num_uses=math.inf, phases=[Phase.day], command_public=True),
    ]
    upgrades = [PsychicIdiot, IdiotSavant, Myth, NullCarrier],


class YandereSpy(Role):
    name = 'yandere spy'
    is_yandere = True
    default_alignment = Alignment.evil
    abilities = [
        ability.SpyAbility(num_uses=math.inf, phases=[Phase.day]),
        ability.VoteKillAbility(num_uses=math.inf, phases=[Phase.night]),
        ability.VoteKillAbility(num_uses=math.inf, phases=[Phase.day], command_public=True),
    ]
    safe_to_guard = False


class YandereSenpai(Role):
    name = 'yandere senpai'
    is_yandere = True
    default_alignment = Alignment.evil
    abilities = [
        ability.UpgradeAbility(num_uses=1, phases=[Phase.day]),
        ability.VoteKillAbility(num_uses=math.inf, phases=[Phase.night]),
        ability.VoteKillAbility(num_uses=math.inf, phases=[Phase.day], command_public=True),
    ]
    safe_to_guard = False


class YandereRonin(Role):
    name = 'yandere ronin'
    is_yandere = True
    default_alignment = Alignment.evil
    abilities = [
        ability.KillAbility(num_uses=1, phases=[Phase.day]),
        ability.VoteKillAbility(num_uses=math.inf, phases=[Phase.night]),
        ability.VoteKillAbility(num_uses=math.inf, phases=[Phase.day], command_public=True),
    ]
    safe_to_guard = False


class PsychicYandere(Role):
    name = 'psychic yandere'
    is_yandere = True
    default_alignment = Alignment.evil
    abilities = [
        ability.SpyAbility(num_uses=1, phases=[Phase.day]),
        ability.VoteKillAbility(num_uses=math.inf, phases=[Phase.night]),
        ability.VoteKillAbility(num_uses=math.inf, phases=[Phase.day], command_public=True),
    ]
    upgrades = [YandereSpy]
    safe_to_guard = False


class CloakedPsychicYandere(Role):
    name = 'cloaked psychic yandere'
    is_yandere = True
    default_alignment = Alignment.evil
    abilities = [
        ability.SpyAbility(num_uses=1, phases=[Phase.day]),
        ability.VoteKillAbility(num_uses=math.inf, phases=[Phase.night]),
        ability.VoteKillAbility(num_uses=math.inf, phases=[Phase.day], command_public=True),
    ]
    appearances = ['civilian', 'dayspy', 'tokokyohi', 'hikikomori', 'nurse', 'guardian', 'warrior', 'esper', 'spy', 'shogun']
    safe_to_guard = True


class CloakedYandere(Role):
    name = 'cloaked yandere'
    is_yandere = True
    default_alignment = Alignment.evil
    abilities = [
        ability.VoteKillAbility(num_uses=math.inf, phases=[Phase.night]),
        ability.VoteKillAbility(num_uses=math.inf, phases=[Phase.day], command_public=True),
    ]
    upgrades = [CloakedPsychicYandere]
    appearances = ['civilian', 'tokokyohi', 'hikikomori', 'nurse', 'guardian', 'warrior', 'witness', 'stalker', 'shogun']
    safe_to_guard = True


class YandereDoppelganger(Role):
    name = 'yandere doppelganger'
    is_yandere = True
    default_alignment = Alignment.evil
    abilities = [
        ability.VoteKillAbility(num_uses=math.inf, phases=[Phase.night]),
        ability.VoteKillAbility(num_uses=math.inf, phases=[Phase.day], command_public=True),
    ]
    upgrades = [CloakedYandere]
    safe_to_guard = False


class Yandere(Role):
    name = 'yandere'
    is_yandere = True
    default_alignment = Alignment.evil
    abilities = [
        ability.VoteKillAbility(num_uses=math.inf, phases=[Phase.night]),
        ability.VoteKillAbility(num_uses=math.inf, phases=[Phase.day], command_public=True),
    ]
    upgrades = [YandereDoppelganger, CloakedYandere, PsychicYandere, YandereSpy, YandereRonin, YandereSenpai]
    safe_to_guard = False


class Trap(Role):
    name = 'trap'
    is_yandere = True
    default_alignment = Alignment.evil
    abilities = [
        ability.VoteKillAbility(num_uses=math.inf, phases=[Phase.day], command_public=True),
    ]
    upgrades = [CloakedYandere, BakaRanger]
    appearances = ['civilian', 'tokokyohi', 'hikikomori', 'nurse', 'guardian', 'warrior', 'witness', 'snoop', 'detective']
    safe_to_guard = True


# hack
all_role_classes = [l for l in locals().values() if inspect.isclass(l) and issubclass(l, Role) and l != Role]
