"""Set up the bot."""

import os
import sys

from discord.ext import commands
from discord_slash import SlashCommand

sys.path.append('..')
from . import constants, hidden
from utils import dt_utils

# Set up the bot.
bot = commands.Bot(command_prefix=constants.PREFIX)
slash = SlashCommand(bot, sync_commands=True)
bot.remove_command('help')

# Load cogs.
for filename in os.listdir('src/cogs'):
    if not filename.startswith('__') and filename.endswith('.py'):
        print(f'cogs.{filename[:-3]}')
        bot.load_extension(f'cogs.{filename[:-3]}')
        print(f'Loaded cog: {filename}')
print()
