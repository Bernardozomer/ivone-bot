"""Start the bot."""

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

from core import bot, hidden

bot.bot.run(hidden.TOKEN)