from collections import defaultdict
from opendere import game


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
        # TODO: the game should immediately end if all the yanderes are dead
        self.target_user.is_alive = False
        return [(self.game.channel, f"{self.target_user.nick} was brutally murdered! who could've done this {self.game.random_emoji}")]


class VoteToKillAction(Action):
    def __call__(self):
        messages = list()

        reply_to = [self.game.channel] if self.game.phase_name == 'day' \
            else [user.uid for user in self.game.users.values() if user.role.is_yandere]

        # at the end of the phase, the first VoteToKillAction handles this logic for all
        # instances of this action then deletes all instances of VoteToKillAction
        if self.game.phase_seconds_left <= 0:
            # this should only proc if we're at the end of the phase :X
            vote_counts = defaultdict(int)
            for action in self.actions_of_my_type:
                vote_counts[action.target_user] += 1
            vote_counts = sorted(vote_counts.items(), key=lambda x: x[1], reverse=True)
            if not vote_counts:
                most_voted_user = None
            elif len(vote_counts) == 1 or vote_counts[0][1] > vote_counts[1][1]:
                most_voted_user = vote_counts[0][0]
            elif self.game.phase_name == 'night':
                # at night, with ties, the first yandere to vote for someone other than abstain decides
                most_voted_user = next((target for target, _ in votes if type(target) != str), None)
            else:
                most_voted_user = None

            # ensure VoteToKillAction isn't processed twice
            self.del_actions_of_type(type(self))

            if type(most_voted_user) == game.User:
                # a return message is unnecessary imo because the kill action should handle that imo
                # should we have the person executing the killaction be a yandere if it's night?
                self.game.phase_actions.append(
                    KillAction(self.game, None if self.game.phase_name == 'day' else self.user, most_voted_user)
                )

            else:
                return [(self.game.channel, "...it seems everyone survived the night. it is a brand new day :D") \
                    if self.game.phase_name == 'night' \
                    else (self.game.channel, "you abstain from killing anyone. you should pray that was the right decision...")]

        # if we're not at the end of the phase, then we need to display who was voted for
        # and then put the vote into phase_actions queue for counting at the end of the phase
        else:
            previous_vote = next((action for action in self.actions_of_my_type if action != self and action.user == self.user), None)

            # player hasn't voted yet
            if not previous_vote and type(self.target_user) == game.User:
                messages += [(uid, f"{self.user.nick} has voted for {self.target_user.nick}") for uid in reply_to]

            # TODO: "abstain" is bad, it should probably be a constant
            elif not previous_vote and self.target_user == 'abstain':
                messages += [(uid, f"{self.user.nick} has abstained from voting") for uid in reply_to]

            # TODO: ditto for 'undecided'
            elif not previous_vote and self.target_user == 'undecided':
                return [(self.user.uid, "you were already undecided and are still undecided >:(")]

            # if the player hasn't actually changed their vote at all
            elif previous_vote.target_user == self.target_user:
                return [(self.user.uid, "you've already {}".format(
                    f"voted for {self.target_user.nick}" if type(previous_vote.target_user) == game.User else 'abstained'
                ))]

            # if the player has changed their vote from something to anything else
            else:
                messages += [(uid, "{} has changed their vote from {} to {}".format(
                    self.user.nick,
                    previous_vote.target_user.nick if type(previous_vote.target_user) == game.User else previous_vote.target_user,
                    self.target_user.nick if type(self.target_user) == game.User else self.target_user)
                ) for uid in reply_to]

            # modify the previous vote if one exists
            if previous_vote and self.target_user == 'undecided':
                self.game.phase_actions.remove(previous_vote)
            elif previous_vote:
                previous_vote.target_user = self.target_user

            # otherwise stick it in the queue
            else:
                self.game.phase_actions.append(VoteToKillAction(self.game, self.user, self.target_user))

            # immediately end the phase if voting is completed
            if len(self.actions_of_my_type) >= self.game.num_players_alive:
                self.game.end_phase()

            return messages


class UnstoppableKillAction(Action):
    # A kill that shouldn't be eliminated from the action list
    __call__ = KillAction.__call__


class GuardAction(Action):
    def __call__(self):
        # eliminate any actions that kill self.target_user
        self.game.phase_actions = [
            action for action in self.game.phase_actions
            if not (isinstance(action, KillAction) and action.target_user == self.target_user)
        ]
        # kill self if the guarded role isn't safe to guard
        if not self.target_user.role.safe_to_guard:
            self.game.phase_actions.append(
                UnstoppableKillAction(self.game, self.target_user, self.user)
            )
        return []


class HideAction(Action):
    is_legal_during_day = False
    def __call__(self):
        # FIXME: need to rewrite this, hide action shouldn't be *deleting* actions
        # because they should still be observeable by a witness...
        self.game.phase_actions = [
            action for action in self.game.phase_actions
            if not (isinstance(action, KillAction) and action.target_user == self.user)
        ]
        return [(self.user.uid, "you're hiding from the scary yanderes :D")]
