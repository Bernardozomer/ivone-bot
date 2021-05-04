"""Set up the bot and run it."""

# -------------------------------------------------------------------------------------------------
# Ivone
#
# Ivone is a task management bot for teams using Discord.
# Works using discord.py and discord-py-slash-command.
#
# 2019 - 2021, Bernardo B. Zomer
#
# Source code: https://github.com/Bernardozomer/ivone-bot/
# -------------------------------------------------------------------------------------------------

import os

from discord.ext import commands
from discord_slash import SlashCommand

import constants
import hidden

# Set up the bot.
bot = commands.Bot(command_prefix=constants.PREFIX)
slash = SlashCommand(bot, sync_commands=True)
bot.remove_command('help')

# Load cogs.
for filename in os.listdir('src/cogs'):
    if not filename.startswith('__') and filename.endswith('.py'):
        bot.load_extension(f'src.cogs.{filename[:-3]}')
        print(f'Loaded cog: {filename}')
print()

# Run.
if __name__ == '__main__':
    bot.run(hidden.TOKEN)
