#!/usr/bin/env python3
# coding=utf-8
"""nekodere sopel module, running opendere"""

from sopel import tools
from sopel.module import commands, interval, rule, example

import sys
sys.path.append('/home/libbies/.sopel/modules')

import opendere.game
import opendere.roles

def setup(bot=None):
    if not bot:
        return
    bot.memory['allowed_channels'] = ['#opendere']
    bot.memory['nekodere'] = None

@interval(1)
def tick(bot):
    """
    tick down the timer for game state, i.e. the start timer or hurry timer
    """
    if not bot.memory['nekodere']:
        return
    messages = bot.memory['nekodere'].tick()
    if not messages:
        return
    for msg in messages:
        recipient, text = msg
        if recipient in bot.memory['allowed_channels']:
            bot.say('\x02' + text + '\x0f', recipient)
        else:
            recipient = recipient.split('!')[0]
            bot.notice(text, recipient)

@commands('nekodere')
@example('!nekodere - start a new game')
def join_game(bot, trigger):
    """
    join an existing (or create a new) nekodere instance
    """
    if trigger.sender not in bot.memory['allowed_channels']:
        bot.say(f"you can only join or start a game from {' or '.join(bot.memory['allowed_channels'])}") 
        return
    if not bot.memory['nekodere']:
        bot.memory['nekodere'] = opendere.game.Game('nekodere', trigger.sender, prefix='!')
    for msg in bot.memory['nekodere'].join_game(trigger.hostmask, trigger.nick):
        recipient, text = msg
        if recipient in bot.memory['allowed_channels']:
            bot.say('\x02' + text + '\x0f', recipient)
        else:
            recipient = recipient.split('!')[0]
            bot.notice(text, recipient)

# can likely replace all of these below commands with a single regex
@commands('hurry|nekodere hurry')
@example('!hurry - hurry the current phase')
def hurry(bot, trigger):
    if not bot.memory['nekodere']:
        return
    for msg in bot.memory['nekodere'].user_hurry(trigger.hostmask):
        recipient, text = msg
        if recipient in bot.memory['allowed_channels']:
            bot.say('\x02' + text + '\x0f', recipient)
        else:
            recipient = recipient.split('!')[0]
            bot.notice(text, recipient)

@commands('vote|nekodere vote')
@example('!vote <target> - vote to kill someone')
def vote(bot, trigger):
    if not bot.memory['nekodere']:
        return
    for msg in bot.memory['nekodere'].user_action(trigger.hostmask, 'vote'):
        recipient, text = msg
        if recipient in bot.memory['allowed_channels']:
            bot.say('\x02' + text + '\x0f', recipient)
        else:
            recipient = recipient.split('!')[0]
            bot.notice(text, recipient)
