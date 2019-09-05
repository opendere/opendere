from collections import defaultdict


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
        # TODO: the game should immediately end if all the yanderes are dead
        self.target_user.is_alive = False
        if self.game.phase_name == 'day':
            return [(self.game.channel,
                f"{self.target_user.nick} was lynched, and it turns out they were{'' if self.target_user.role.is_yandere else ' NOT'} a yandere!")]
        else:
            return [(self.game.channel, f"{self.target_user.nick} was brutally murdered! who could've done this {self.game.random_emoji}")]


class VoteToKillAction(Action):
    def __init__(self, game, user, target_user):
        self.game, self.user, self.target_user, self.messages = game, user, target_user, list()

        reply_to = [self.game.channel] \
            if self.game.phase_name == 'day' \
            else [user.uid for user in self.game.users.values() if user.role.is_yandere]

        previous_vote = next((action for action in self.actions_of_my_type if action != self and action.user == self.user), None)

        # player hasn't voted yet
        if not previous_vote and type(self.target_user) != str:
            self.messages += [(uid, f"{self.user.nick} has voted for {self.target_user.nick}") for uid in reply_to]

        # TODO: "abstain" is bad, it should probably be a constant
        elif not previous_vote and self.target_user == 'abstain':
            self.messages += [(uid, f"{self.user.nick} has abstained from voting") for uid in reply_to]

        # TODO: ditto for 'undecided'
        elif not previous_vote and self.target_user == 'undecided':
            self.messages += [(self.user.uid, "you were already undecided and are still undecided >:(")]

        # if the player hasn't actually changed their vote at all
        elif previous_vote.target_user == self.target_user:
            self.messages += [(self.user.uid, "you've already {}".format(
                'abstained' if type(previous_vote.target_user) == str else f"voted for {self.target_user.nick}"
            ))]
            # since the player's vote didn't actually change, to preserve order, we invalidate the new vote
            self.game, self.user, self.target_user = None, None, None

        # if the player has changed their vote from something to anything else
        else:
            self.messages += [(uid, "{} has changed their vote from {} to {}".format(
                self.user.nick,
                previous_vote.target_user if type(previous_vote.target_user) == str else previous_vote.target_user.nick,
                self.target_user if type(self.target_user) == str else self.target_user.nick
            )) for uid in reply_to]
            # removing the previous vote here, so that there aren't two votes from the player
            self.game.phase_actions.pop(previous_vote)
            # if the player voted for undecided, we should invalidate the new vote too
            if self.target_user == 'undecided':
                self.game, self.user, self.target_user = None, None, None

        # tally the votes here
        vote_tally = "current_votes are: "
        for target in set([
                action.target_user for action in self.actions_of_my_type
                if action.target_user is not None and type(action.target_user) != str
            ]):
            vote_tally += f"{target.nick}: {len([action for action in self.actions_of_my_type if action.target_user == target])}, "
        vote_tally += f"abstain: {len([action for action in self.actions_of_my_type if action.target_user == 'abstain'])}, "
        if self.game.phase_name == 'day':
            vote_tally += f"undecided: {self.game.num_players_alive - len([act for act in self.actions_of_my_type if act.target_user != None])}"
        else:
            vote_tally += f"undecided: {self.game.num_yanderes_alive - len([act for act in self.actions_of_my_type if act.target_user != None])}"
        self.messages += [(uid, vote_tally) for uid in reply_to]

        # also immediately end the phase if voting is completed
        if self.game.phase_name == 'day' and len([act for act in self.actions_of_my_type if act.user != None]) >= self.game.num_players_alive:
            self.game.end_phase()

        # TODO: figure out if there's a better place to end night-time stuff than here...

    def __call__(self):
        messages = list()

        reply_to = [self.game.channel] if self.game.phase_name == 'day' \
            else [user.uid for user in self.game.users.values() if user.role.is_yandere]

        # at the end of the phase, the first VoteToKillAction handles this logic for all
        # instances of this action then deletes all instances of VoteToKillAction
        vote_counts = defaultdict(int)
        for action in self.actions_of_my_type:
            vote_counts[action.target_user] += 1

        vote_counts = sorted(vote_counts.items(), key=lambda x: x[1], reverse=True)


        most_voted_user = None

        if len(vote_counts) == 1 or vote_counts[0][1] > vote_counts[1][1]:
            most_voted_user = vote_counts[0][0]

        # at night, with ties, the first yandere to vote for someone other than abstain decides
        elif self.game.phase_name == 'night':
            most_voted_user = next((
                action.target_user for action in self.actions_of_my_type
                if type(action.target_user) != str and (action.target_user in [ vote_counts[0][0], vote_counts[1][0] ])
            ), None)

        # also at at nigth, the first yandere to vote that person is the person who does the killing
        if self.game.phase_name == 'night':
            killer = next((action.user for action in self.actions_of_my_type if action.target_user == most_voted_user), None)

        # ensure VoteToKillAction isn't processed twice
        self.del_actions_of_type(type(self))

        if most_voted_user is not None:
            # a return message is unnecessary imo because the kill action should handle that imo
            # should we have the person executing the killaction be a yandere if it's night?
            self.game.phase_actions.append(
                KillAction(self.game, killer if self.game.phase_name == 'night' else None, most_voted_user)
            )
            # the kill message should be handled by KillAction
            return [ ]
        else:
            return [(self.game.channel, "...it seems everyone survived the night. it is a brand new day :D") \
                if self.game.phase_name == 'night' \
                else (self.game.channel, "you abstain from killing anyone. you should pray that was the right decision...")]


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
