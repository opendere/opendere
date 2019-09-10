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
    def __init__(self, game, user, target_user, previous_action=None):
        self.game = game
        self.user = user
        self.target_user = target_user
        self.previous_action = previous_action
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
        if self.game.is_protected(self.target_user) and not isinstance(self, UnstoppableKillAction):
            return []
        else:
            return self.game.kill_user(self.user, self.target_user)


class VoteToKillAction(Action):
    def __init__(self, game, user, target_user, previous_vote=None):
        self.game, self.user, self.target_user, self.messages = game, user, target_user, list()

        self.previous_vote = previous_vote
        if not self.previous_vote:
            self.previous_vote = Action(None, None, 'undecided')

        

        if self.game.phase_name == 'day':
            reply_to = [self.game.channel]
        else:
            reply_to = [user.uid for user in self.game.users.values() if user.role.is_yandere and user.is_alive]

        self.messages += [(uid, "{} has changed their vote from {} to {}".format(
            self.user.nick,
            self.previous_vote.target_user.nick if isinstance(self.previous_vote.target_user, opendere.game.User) else self.previous_vote.target_user,
            self.target_user.nick if isinstance(self.target_user, opendere.game.User) else self.target_user
        )) for uid in reply_to]

        if self.target_user == 'undecided':
            self.user, self.target_user = None, None

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
                if isinstance(action.target_user, opendere.game.User) and (action.target_user in [vote_counts[0][0], vote_counts[1][0]])
            ), None)

        if most_voted_user and not self.game.is_protected(most_voted_user):
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
    __call__ = KillAction.__call__


class GuardAction(Action):
    def __init__(self, game, user, target_user, previous_action=None):
        self.game, self.user, self.target_user, self.previous_action = game, user, target_user, previous_action
        if self.previous_action:
            self.messages = [(self.user.uid, f"you're changed from guarding {previous_action.nick} to guarding {target_user.nick} instead <3")]
        else:
            self.messages = [(self.user.uid, f"you're guarding {target_user.nick} from the scary yanderes <3")]

    def __call__(self):
        if not self.target_user.role.safe_to_guard:
            self.game.phase_actions.append(UnstoppableKillAction(self.game, None, self.user))
        return []


class HideAction(Action):
    def __init__(self, game, user, target_user=None, previous_action=None):
        self.game, self.user, self.target_user, previous_action = game, user, target_user, previous_action
        self.messages = [(self.user.uid, "you're hiding from the scary yanderes :D")]

    def __call__(self):
        return []

class StalkAction(Action):
    def __init__(self, game, user, target_user, previous_action=None):
        self.game, self.user, self.target_user, self.previous_action = game, user, target_user, previous_action
        if self.previous_action:
            self.messages = [(self.user.uid, f"you're changed from stalking {previous_action.nick} to stalking {target_user.nick} instead <3")]
        else:
            self.messages = [(self.user.uid, f"you're stalking {target_user.nick}, gotta make sure they're not visiting anyone but you <3")]

    def __call__(self):
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

def CheckAction(Action):
    def __init__(self, game, user, target_user, previous_action=None):
        self.game, self.user, self.target_user, self.previous_action = game, user, target_user, previous_action
        if self.previous_action:
            self.messages = [(self.user.uid, f"you're changed from checking {previous_action.nick} to checking {target_user.nick} instead")]
        else:
            self.messages = [(self.user.uid, f"you're checking {target_user.nick}")]

    def __call__(self):
        messages = list()
        if self.target_user.alignment:
            return [(self.user.uid, f"{self.target_user.nick} appears to be {self.target_user.alignment}")]
        return [(self.user.uid, f"{self.target_user.nick} appears to be {self.target_user.role.default_alignment.name}")]

def SpyAction(Action):
    def __init__(self, game, user, target_user, previous_action=None):
        self.game, self.user, self.target_user, self.previous_action = game, user, target_user, previous_action
        if self.previous_action:
            self.messages = [(self.user.uid, f"you're changed from spying on {previous_action.nick} to spying on {target_user.nick} instead")]
        else:
            self.messages = [(self.user.uid, f"you're spying on {target_user.nick}")]

    def __call__(self):
        messages = list()
        if self.target_user.appear_as:
            return [(self.user.uid, f"{self.target_user.nick} appears to be a {self.target_user.appear_as}")]
        return [(self.user.uid, f"{self.target_user.nick} appears to be a {self.target_user.role.name}")]

def UpgradeAction(Action):
    def __call__(self):
        messages = [(self.user.uid, f"you've upgraded {self.target_user.nick}, hopefully that was the right thing to do...")]
        if self.target_user.upgrades:
            self.target_user.role = random.choice(self.target_user.upgrades)            
            messages += [(self.target_user.uid, f"you've been upgraded to a {self.target_user.role.name}. {self.target_user.role.description}")]
        return messages
