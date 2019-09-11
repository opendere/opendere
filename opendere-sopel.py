#!/usr/bin/env python3
# coding=utf-8
"""opendere sopel frontend module"""

import os, sys
from sopel.module import commands, interval, rule, example
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
import opendere.game
import opendere.roles

opendere_channels = ['#opendere']
command_prefix = '!'

def bold(msg):
    return f"\x02{msg}\x0f"

def setup(bot=None):
    if not bot:
        return
    bot.memory['opendere_channels'] = opendere_channels
    bot.memory['games'] = dict()

@interval(0.1)
def tick(bot):
    """
    tick down the timer for game state, i.e. the start timer or hurry timer
    """
    for channel in list(bot.memory['games']):
        # if the game has ended or been reset
        if bot.memory['games'][channel].channel is None:
            del bot.memory['games'][channel]

        try:
            messages = bot.memory['games'][channel].tick()
        except KeyError:
            continue
        except opendere.game.InsufficientPlayersError:
            bot.say(bold(f"there aren't enough players to start a game of opendere in {channel}. please try again later."), channel)
            del bot.memory['games'][channel]
            continue

        if not messages:
            continue

        for recipient, text in messages:
            if recipient in bot.memory['opendere_channels']:
                bot.say(bold(text), recipient)
            else:
                bot.notice(text, recipient.split('!')[0])

@rule(f"^{command_prefix}(e$|end|r$|reset|restart)")
@example('!end - end/reset the current game')
def reset(bot, trigger):
    """
    reset the game state if it's borked
    """
    if trigger.sender not in bot.memory['games']:
        return
    bot.memory['games'][trigger.sender].reset()
    del bot.memory['games'][trigger.sender]
    bot.say(bold(f"the current game in {trigger.sender} has been ended or reset."), trigger.sender)

@rule(f"{command_prefix}(!opendere|{'|'.join([channel.lstrip('#') for channel in opendere_channels])})")
@example('!opendere - join an existing (or start a new) game in #opendere')
def join_game(bot, trigger):
    """
    join an existing (or start a new) opendere instance
    """
    if trigger.sender not in bot.memory['opendere_channels']:
        # bot.say(f"you can only join or start a game from {' or '.join(bot.memory['opendere_channels'])}")
        return

    # if no game exists, we need to start one
    if trigger.sender not in bot.memory['games']:
        bot.memory['games'][trigger.sender] = opendere.game.Game(trigger.sender, bot.nick, trigger.sender.lstrip('#'), command_prefix)

    # if one does exist, we can then join the player to it
    for recipient, text in bot.memory['games'][trigger.sender].join_game(trigger.hostmask, trigger.nick):
        if recipient in bot.memory['opendere_channels']:
            bot.say(bold(text), recipient)
        else:
            bot.notice(text, recipient.split('!')[0])

@rule(f"^{command_prefix}(e$|extend)")
@example('!extend - give more time for people to join the game')
def extend(bot, trigger):
    if trigger.sender not in bot.memory['games']:
        return
    for recipient, text in bot.memory['games'][trigger.sender].user_extend(trigger.hostmask):
        if recipient in bot.memory['opendere_channels']:
            bot.say(bold(text), recipient)
        else:
            bot.notice(text, recipient.split('!')[0])

@rule(f"^{command_prefix}(h$|hurry|hayaku)")
@example('!hurry - vote to hurry the current phase')
def hurry(bot, trigger):
    if trigger.sender not in bot.memory['games']:
        return
    for recipient, text in bot.memory['games'][trigger.sender].user_hurry(trigger.hostmask):
        if recipient in bot.memory['opendere_channels']:
            bot.say(bold(text), recipient)
        else:
            bot.notice(text, recipient.split('!')[0])

# alias for 'vote abstain'
@rule(f"^{command_prefix}?(a$|abstain)")
@example('!abstain - abstain from taking an action')
def unvote(bot, trigger):
    if trigger.sender not in bot.memory['games']:
        return
    for recipient, text in bot.memory['games'][trigger.sender].user_abstain(trigger.hostmask):
        if recipient in bot.memory['opendere_channels']:
            bot.say(bold(text), recipient)
        else:
            bot.notice(text, recipient.split('!')[0])

# alias for 'vote undecided'
@rule(f"^{command_prefix}?(u$|unvote)")
@example('!unvote - change your vote to undecided')
def unvote(bot, trigger):
    if trigger.sender not in bot.memory['games']:
        return
    for recipient, text in bot.memory['games'][trigger.sender].user_action(trigger.hostmask,
            "vote undecided",
            channel=trigger.sender if trigger.sender != trigger.nick else None):
        if recipient in bot.memory['opendere_channels']:
            bot.say(bold(text), recipient)
        else:
            bot.notice(text, recipient.split('!')[0])

@rule(f"^{command_prefix}?[^$]+")
@example("!vote <target> - use an ability against a target (e.g. 'vote kitties' or 'kill kitties')")
def actions(bot, trigger):
    # for sopel, trigger.sender is a channel if the message is sent via a channel, and a nick if the message is sent via privmsg
    messages = list()
    if trigger.sender in bot.memory['opendere_channels'] and trigger.sender not in bot.memory['games']:
        if trigger.match.string.lstrip(command_prefix) in ['opendere', trigger.sender.lstrip('#')]:
            bot.memory['games'][trigger.sender] = opendere.game.Game(trigger.sender, bot.nick, trigger.sender.lstrip('#'), command_prefix)
        else:
            # bot.say(trigger.sender, f"you can only start a game from {' or '.join(bot.memory['opendere_channels'])}")
            return

    # an action that occurs in a channel, e.g. 'vote'
    if trigger.sender in bot.memory['games']:
        messages = bot.memory['games'][trigger.sender].user_action(trigger.hostmask, trigger.match.string, trigger.sender)

    # an action that occurs in a privmsg or notice[?], e.g. 'kill' or 'check'
    # TODO: this probably breaks down if a user is somehow in multiple games, so we need to prevent that later...
    elif trigger.hostmask in [user.uid for game in bot.memory['games'].values() for user in game.users.values()]:
        game = next((game.channel for game in bot.memory['games'].values() for user in game.users.values() if user.uid == trigger.hostmask), None)
        if not game:
            return
        messages = bot.memory['games'][game].user_action(trigger.hostmask, trigger.match.string.rstrip())

    if not messages:
        return

    for recipient, text in messages:
        if recipient in bot.memory['opendere_channels']:
            bot.say(bold(text), recipient)
        else:
            bot.notice(text, recipient.split('!')[0])
