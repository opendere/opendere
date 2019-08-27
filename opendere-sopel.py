#!/usr/bin/env python3
# coding=utf-8
"""opendere sopel frontend module"""

from sopel import tools
from sopel.module import commands, interval, rule, example

import sys
sys.path.append('/home/libbies/.sopel/modules')

import opendere.game
import opendere.roles

allowed_channels = ['#opendere']
command_prefix = '!'

def bold(msg):
    return f"\x02{msg}\x0f"

def setup(bot=None):
    if not bot:
        return
    bot.memory['allowed_channels'] = allowed_channels
    bot.memory['games'] = dict()

@interval(1)
def tick(bot):
    """
    tick down the timer for game state, i.e. the start timer or hurry timer
    """
    for channel in bot.channels:
        if channel not in bot.memory['games']:
            return

        messages = bot.memory['games'][channel].tick()
        if not messages:
            return

        for msg in messages:
            recipient, text = msg
            if recipient in bot.memory['allowed_channels']:
                bot.say(bold(text), recipient)
            else:
                recipient = recipient.split('!')[0]
                bot.notice(text, recipient)

        # if the game has ended or been reset
        if bot.memory['games'][channel].channel == None:
            del bot.memory['games'][channel]

@rule(f"{command_prefix}[^$]+")
def actions(bot, trigger):
    # 
    if trigger.sender in bot.memory['allowed_channels'] and trigger.sender not in bot.memory['games']:
        if trigger.match.string.split()[0][len(command_prefix):] in [channel.lstrip('#') for channel in allowed_channels]:
            bot.memory['games'][trigger.sender] = opendere.game.Game(trigger.sender, bot.nick, trigger.sender.lstrip('#'), command_prefix)
        else:
            return

    # an action that occurs in a channel, e.g. 'vote' or 'hurry'
    if trigger.sender in bot.memory['games']:
        messages = bot.memory['games'][trigger.sender].user_action(trigger.hostmask, trigger.match.string, trigger.sender, trigger.nick)

    # an action that occurs in a privmsg or notice[?], e.g. 'kill' or 'check'
    # TODO: test this, lol.
    # TODO: this probably breaks down if a user is somehow in multiple games, so we need to prevent that later...
    elif trigger.sender in [bot.memory['games'][game].users[user].nick for game in bot.memory['games'] for user in bot.memory['games'][game].users]:
        game = [bot.memory['games'][game].channel for game in bot.memory['games'] for user in bot.memory['games'][game].users][0]
        if not game:
            return
        messages = bot.memory['games'][game].user_action(trigger.hostmask, trigger.match.string)

    # otherwise ignore the message because it's not in a game channel or it's not sent by a player in an active game
    else:
        return

    for msg in messages:
        recipient, text = msg
        if recipient in bot.memory['allowed_channels']:
            bot.say(bold(text), recipient)
        else:
            recipient = recipient.split('!')[0]
            bot.notice(text, recipient)

    # if the game has ended or been reset
    if bot.memory['games'][trigger.sender].channel == None:
        del bot.memory['games'][trigger.sender]
