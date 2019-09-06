from collections import defaultdict
import opendere.game

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
    def __init__(self, game, user, target_user):
        self.game = game
        self.user = user
        self.target_user = target_user
        self.messages = []

    def __call__(self):
        # apply the Action. Actions either update game state by changing the
        # Actions to be evaluated, or it updates the game in another way
        # returns messages resulting from the action
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
    def __call__(self):
        # kill the target
        if isinstance(self, UnstoppableKillAction) or not next((
                action for action in self.game.completed_actions
                if (isinstance(action, HideAction) and action.user == self.target_user)
                or (isinstance(action, GuardAction) and action.target_user == self.target_user)
            ), None):
            self.target_user.is_alive = False
        else:
            return [] 

        if isinstance(self, UnstoppableKillAction):
            self.target_user.is_alive = False

        if self.game.phase_name == 'night':
            return [(self.game.channel, f"{self.target_user.nick} was brutally murdered! who could've done this {self.game.random_emoji}")]

        elif self.game.phase_name == 'day' and self.user:
            return [(self.game.channel, "{} runs {} through with a katana, and it turns out they were{}a yandere!".format(
                self.user.nick,
                self.target_user.nick,
                ' ' if self.target_user.role.is_yandere else ' NOT '
            ))]

        else:
            return [(self.game.channel, "{} was lynched, and it turns out they were{}a yandere!".format(
                self.target_user.nick,
                ' ' if self.target_user.role.is_yandere else ' NOT '
            ))]


class VoteToKillAction(Action):
    def __init__(self, game, user, target_user):
        self.game, self.user, self.target_user, self.messages = game, user, target_user, list()

        if self.game.phase_name == 'day':
            reply_to = [self.game.channel]
        else:
            reply_to = [user.uid for user in self.game.users.values() if user.role.is_yandere]

        previous_vote = next((act for act in self.actions_of_my_type if act != self and act.user == self.user and act.target_user != None),
            Action(game=self.game, user=self.user, target_user='undecided'))

        if previous_vote.target_user == self.target_user:
            self.messages += [(self.game.channel, f"{self.user.nick}: your vote is still the same as before >:(")]
            # since the player's vote didn't actually change, to preserve order, we invalidate the new vote
            self.target_user = None

        else:
            self.messages += [(uid, "{} has changed their vote from {} to {}".format(
                self.user.nick,
                previous_vote.target_user.nick if isinstance(previous_vote.target_user, opendere.game.User) else previous_vote.target_user,
                self.target_user.nick if isinstance(self.target_user, opendere.game.User) else self.target_user
            )) for uid in reply_to]

            if previous_vote in self.game.phase_actions:
                self.game.phase_actions.remove(previous_vote)
            if self.target_user == 'undecided':
                self.target_user = None

        # tally the votes here
        vote_tally = "current_votes are: "
        for target in {act.target_user for act in self.actions_of_my_type if isinstance(act.target_user, opendere.game.User)}:
            vote_tally += f"{target.nick}: {len([act for act in self.actions_of_my_type if act.target_user == target])}, "
        vote_tally += f"abstain: {len([act for act in self.actions_of_my_type if act.target_user == 'abstain'])}, "
        if self.game.phase_name == 'day':
            vote_tally += f"undecided: {self.game.num_players_alive - len([act for act in self.actions_of_my_type if act.target_user])}"
        else:
            vote_tally += f"undecided: {self.game.num_yanderes_alive - len([act for act in self.actions_of_my_type if act.target_user])}"
        self.messages += [(uid, vote_tally) for uid in reply_to]

        # also immediately end the phase if voting is completed
        if self.game.phase_name == 'day' and len({act for act in self.actions_of_my_type if act.target_user}) >= self.game.num_players_alive:
            self.game.end_current_phase()

        # TODO: figure out if there's a better place to end night-time stuff than here...

    def __call__(self):
        # at the end of the phase, the first VoteToKillAction handles this logic for all
        # instances of this action then deletes all instances of VoteToKillAction
        vote_counts = defaultdict(int)
        for action in {act for act in self.actions_of_my_type if act.target_user}:
            vote_counts[action.target_user] += 1
        vote_counts = sorted(vote_counts.items(), key=lambda x: x[1], reverse=True)
        most_voted_user = None

        if len(vote_counts) == 1 or vote_counts[0][1] > vote_counts[1][1]:
            most_voted_user = vote_counts[0][0]
        # at night, with ties, the first yandere to vote for someone other than abstain decides
        elif self.game.phase_name == 'night':
            most_voted_user = next((
                action.target_user for action in self.actions_of_my_type
                if isinstance(action.target_user, opendere.game.User) and (action.target_user in [vote_counts[0][0], vote_counts[1][0]])
            ), None)

        # ensure VoteToKillAction isn't processed twice
        self.del_actions_of_type(type(self))

        if most_voted_user:
            if self.game.phase_name == 'night':
                # every yandere who voted for the most_voted_user is a damn murderer >:(
                for killer in (act.user for act in self.actions_of_my_type if act.target_user == most_voted_user):
                    self.game.phase_actions.append(KillAction(self.game, killer, most_voted_user))
            else:
                self.game.phase_actions.append(KillAction(self.game, None, most_voted_user))
            return []
        if self.game.phase_name == 'night':
            return [(self.game.channel, "...it seems everyone survived the night. it is a brand new day :D")]
        else:
            return [(self.game.channel, "you abstain from killing anyone. you should pray that was the right decision...")]


class UnstoppableKillAction(Action):
    # A kill that shouldn't be eliminated from the action list
    __call__ = KillAction.__call__


class GuardAction(Action):
    def __init__(self, game, user, target_user):
        self.game, self.user, self.target_user = game, user, target_user
        self.messages = [(self.user.uid, f"you're guarding {target_user.nick} from the scary yanderes <3")]

    def __call__(self):
        # i don't think user should be target_user bc of witnesses...
        if not self.target_user.role.safe_to_guard:
            self.game.phase_actions.append(UnstoppableKillAction(self.game, None, self.user))
        return []


class HideAction(Action):
    def __init__(self, game, user, target_user=None):
        self.game, self.user, self.target_user = game, user, target_user
        self.messages = [(self.user.uid, "you're hiding from the scary yanderes :D")]

    def __call__(self):
        return []
