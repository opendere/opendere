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

@rule(f"{command_prefix}({'|'.join([channel.lstrip('#') for channel in allowed_channels])})")
@example('!opendere - join an existing (or start a new) game in #opendere')
def join_game(bot, trigger):
    """
    join an existing (or start a new) opendere instance
    """
    if trigger.sender not in bot.memory['allowed_channels']:
        # bot.say(f"you can only join or start a game from {' or '.join(bot.memory['allowed_channels'])}")
        return
    if trigger.sender not in bot.memory['games']:
        bot.memory['games'][trigger.sender] = opendere.game.Game(trigger.sender, bot.nick, command_prefix)
    for msg in bot.memory['games'][trigger.sender].join_game(trigger.hostmask, trigger.nick):
        recipient, text = msg
        if recipient in bot.memory['allowed_channels']:
            bot.say(bold(text), recipient)
        else:
            recipient = recipient.split('!')[0]
            bot.notice(text, recipient)

@commands('end|reset|restart')
@example('!end - end the current game')
def reset(bot, trigger):
    if trigger.sender not in bot.memory['allowed_channels']:
        return
    if trigger.sender not in bot.memory['games']:
        bot.say(f"there isn't a running game in {trigger.sender} to end.")
        return
    bot.memory['games'][trigger.sender].reset()
    del bot.memory['games'][trigger.sender]
    bot.say(f"the current game in {trigger.sender} has been ended.")

# can likely replace all of these below commands with a single regex
@commands('hurry')
@example('!hurry - hurry the current phase')
def hurry(bot, trigger):
    if trigger.sender not in bot.memory['games']:
        return
    for msg in bot.memory['games'][trigger.sender].user_hurry(trigger.hostmask):
        recipient, text = msg
        if recipient in bot.memory['allowed_channels']:
            bot.say(bold(text), recipient)
        else:
            recipient = recipient.split('!')[0]
            bot.notice(text, recipient)

@commands('vote')
@example('!vote <target> - vote to kill someone')
def vote(bot, trigger):
    if trigger.sender not in bot.memory['games']:
        return
    for msg in bot.memory['games'][trigger.sender].user_action(trigger.hostmask, 'vote'):
        recipient, text = msg
        if recipient in bot.memory['allowed_channels']:
            bot.say(bold(text), recipient)
        else:
            recipient = recipient.split('!')[0]
            bot.notice(text, recipient)
