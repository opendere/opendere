from collections import defaultdict
import random
from opendere.common import User


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
    def __init__(self, game, user, target_user, previous_action=None, callback=None):
        self.game = game
        self.user = user
        self.target_user = target_user
        self.previous_action = previous_action
        self.messages = self._get_init_messages()

        self._post_init_hook()

    def __call__(self):
        ret = self.apply()
        if ret and self.user:
            self._decr_uses()
        return ret

    def apply(self):
        # apply the Action. Actions either update game state by changing the
        # Actions to be evaluated, or it updates the game in another way
        # returns messages resulting from the action
        raise NotImplementedError

    def _post_init_hook(self):
        # TODO: this is a hack only applicable to the VoteKillAction, probably should be removed
        return

    def _get_init_messages(self):
        # get the messages resulting from the initialization of the action
        # by default just informs of action changes:
        if not self.user:
            return []
        elif self.previous_action:
            return [(self.user.uid,
                     f"you've changed from {self.action_verb} {self.previous_action} to \
                     {self.action_verb} {self.target_user}")]
        else:
            return [(self.user.uid, f"you're {self.action_verb} {self.target_user}")]

    def _decr_uses(self):
        for ability in self.user.role.abilities:
            if isinstance(self, ability.action):
                ability.num_uses -= 1

    @property
    def action_verb(self):
        # used by _get_init_messages. If there is no action_verb specified, raises an Exception
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
    action_verb = 'killing'
    def apply(self):
        # kill the target
        if self.game.is_protected(self.target_user) and not isinstance(self, UnstoppableKillAction):
            return []
        else:
            return self.game.kill_user(self.user, self.target_user)


class VoteToKillAction(Action):
    action_verb = 'voting to kill'
    def _get_init_messages(self):
        # TODO: clean up this hack, we are only using this for considering previous_action.target_user as 'undecided'
        # in Action.__init__ previous_action should default to this maybe?
        previous_action = self.previous_action or Action(None, None, 'undecided')

        if self.game.phase_name == 'day':
            reply_to = [self.game.channel]
        else:
            reply_to = [user.uid for user in self.game.users.values() if user.role.is_yandere and user.is_alive]

        messages = [
            (uid, f'{self.user} has changed their vote from {previous_action.target_user} to {self.target_user}')
            for uid in reply_to
        ]

        # tally the votes here
        vote_tally = "current_votes are: "
        for target in {act.target_user for act in self.actions_of_my_type if isinstance(act.target_user, User)}:
            vote_tally += f"{target}: {len([act for act in self.actions_of_my_type if act.target_user == target])}, "
        vote_tally += f"abstain: {len([act for act in self.actions_of_my_type if act.target_user == 'abstain'])}, "

        # TODO: we shouldn't care about players alive, we should care about players who can *perform this action* who are alive
        if self.game.phase_name == 'day':
            vote_tally += f"undecided: {self.game.num_players_alive - len([act for act in self.actions_of_my_type if act.target_user])}"
        else:
            vote_tally += f"undecided: {self.game.num_yanderes_alive - len([act for act in self.actions_of_my_type if act.target_user])}"
        messages += [(uid, vote_tally) for uid in reply_to]

        return messages

    def _post_init_hook(self):
        # TODO: figure out if there's a better place to end night-time stuff than here...

        # also immediately end the phase if voting is completed
        if self.game.phase_name == 'day':
            if len({act for act in self.actions_of_my_type if act.target_user}) >= self.game.num_players_alive:
                self.game.end_current_phase()

    def apply(self):
        # at the end of the phase, the first VoteToKillAction handles this logic for all
        # instances of this action then deletes all instances of VoteToKillAction
        vote_counts, most_voted_user = defaultdict(int), None
        for action in (act for act in self.actions_of_my_type if act.target_user):
            vote_counts[action.target_user] += 1
        vote_counts = sorted(vote_counts.items(), key=lambda x: x[1], reverse=True)

        if len(vote_counts) == 1 or vote_counts[0][1] > vote_counts[1][1]:
            most_voted_user = vote_counts[0][0]
        # at night, with ties, the first yandere to vote for someone other than abstain decides
        elif self.game.phase_name == 'night':
            most_voted_user = next((
                action.target_user for action in self.actions_of_my_type
                if isinstance(action.target_user, User) and (action.target_user in [vote_counts[0][0], vote_counts[1][0]])
            ), None)

        if isinstance(most_voted_user, User) and not self.game.is_protected(most_voted_user):
            if self.game.phase_name == 'night':
                # adding a copy of the KillAction to completed_actions for stalker to see.
                # if a yandere voted for someone who wasn't killed, no record is created.
                for killer in (act.user for act in self.actions_of_my_type if act.target_user == most_voted_user):
                    kill = KillAction(self.game, killer, most_voted_user)
                    self.game.completed_actions.append(kill)
            else:
                kill = KillAction(self.game, None, most_voted_user)
            self.del_actions_of_type(type(self))
            return kill()

        self.del_actions_of_type(type(self))
        if self.game.phase_name == 'night':
            return [(self.game.channel, "...it seems everyone survived the night. it is a brand new day :D")]
        else:
            return [(self.game.channel, "you abstain from killing anyone. you should pray that was the right decision...")]


class UnstoppableKillAction(Action):
    # A kill that shouldn't be eliminated from the action list
    apply = KillAction.apply


class GuardAction(Action):
    action_verb = 'guarding'
    def apply(self):
        if not self.target_user.role.safe_to_guard:
            self.game.phase_actions.append(UnstoppableKillAction(self.game, None, self.user))
        return []


class HideAction(Action):
    def _get_init_messages(self):
        return [(self.user.uid, "you're hiding from the scary yanderes :D")]

    def apply(self):
        return []


class StalkAction(Action):
    action_verb = 'stalking'
    def apply(self):
        # need voting to resolve first, as a yandere might not visit the target they voted for
        # as the yandere may be voting for someone who isn't most_voted_user
        # so we delay the execution of this until all votes have been completed
        if any(isinstance(action, VoteToKillAction) for action in self.game.phase_actions):
            self.game.phase_actions.append(self)
            return []
        messages = list()
        for action in self.game.phase_actions + self.game.completed_actions:
            if self.target_user == action.user:
                messages += [(self.user.uid, f"just what exactly was {action.user.nick} doing, visiting {action.target_user.nick} last night?!")]
        if messages:
            return messages
        return [(self.user.uid, f"{self.target_user.nick} stayed at home last night. boring!")]


class CheckAction(Action):
    action_verb = 'checking'
    def apply(self):
        if self.target_user.alignment:
            return [(self.user.uid, f"{self.target_user.nick} appears to be {self.target_user.alignment}")]
        return [(self.user.uid, f"{self.target_user.nick} appears to be {self.target_user.role.default_alignment.name}")]


class SpyAction(Action):
    action_verb = 'spying on'
    def apply(self):
        messages = list()
        if self.target_user.appear_as:
            return [(self.user.uid, f"{self.target_user.nick} appears to be a {self.target_user.appear_as}")]
        return [(self.user.uid, f"{self.target_user.nick} appears to be a {self.target_user.role.name}")]


class UpgradeAction(Action):
    def apply(self):
        messages = [(self.user.uid, f"you've upgraded {self.target_user.nick}, hopefully that was the right thing to do...")]
        if self.role.upgrade_to.new_role_choices:
            self.target_user.role = random.choice(self.role.upgrade_to.new_role_choices)()
            messages += [(self.target_user.uid, f"you've been upgraded to a {self.target_user.role.name}. {self.target_user.role.description}")]
        else:
            self.target_user.role.abilities += self.role.upgrade_to.add_abilities
            # TODO: message
        return messages

class RevealAction(Action):
    def apply(self):
        return []
