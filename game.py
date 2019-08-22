import random
import roles


def weighted_choices(choice_weight_map, num_choices):
    choices = sorted(choice_weight_map)
    weight_sum = sum(choice_weight_map.values())
    probabilities = [choice_weight_map[c] / weight_sum for c in choices]
    return random.choice(choices, num_choices, p=probabilities)


class Game:
    def __init__(self, usernames):
        """
        usernames (list[str]): usernames in the game
        """
        self.lynch_votes = {}  # who has voted to lynch who
        self.phase_num = 0  # current phase (1 day and 1 night is 2 phases)
        self.hurry_requested_users = {}

        # all users start alive
        self.users_alive = {username: True for username in usernames}

        # get set of N roles, and apply them randomly to users
        roles = self._select_roles(len(usernames))
        self.user_roles = {username: role for username, role in zip(usernames, random.shuffle(roles))}

        # get day/night phase
        self.is_day = self._is_first_phase_day(len(usernames))

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
        weighted_neutral_role_classes = {r: 1 for r in roles.all_role_classes if r.alignment == Alignment.neutral}
        weighted_good_and_neutral_role_classes = {
            **weighted_good_roles_classes,
            **weighted_neutral_roles_classes
        }

        if num_users <= 3:
            raise ValueError('A game requires at least 4 players')

        elif num_users <= 5:
            # choose 1 yandere, 3 to 4 good-aligned roles
            role_classes = random.choice([r for r in roles.all_role_classes if r.is_yandere], 1)
            role_classes += weighted_choices(weighted_good_role_classes, num_users - 1)
            return [r() for r in role_classes]

        elif num_users <= 8:
            # choose 2 yandere, 6, 7, or 8 non-yandere roles
            roles = random.choice([r for r in all_role_classes if r.is_yandere], 2)
            roles += weighted_choices(weighted_good_and_neutral_role_classes, num_users - 2)
            return [r() for r in role_classes]

    def _is_first_phase_day(self, num_users):
        """
        algorithm: odd numbers = night
        """
        return num_users % 1 == 1

    def user_action(self, user, action):
        """
        determines whether a user has the ability to take an action, then executes the action
        """
        pass

    def user_hurry(self, user):
        """
        request that the game be hurried
        """
        pass
