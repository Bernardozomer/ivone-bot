"""Manage data generated by the bot."""

import json

import discord
from discord.ext import tasks as disc_tasks
from discord.ext import commands

from src import models


# Java-esque implementation that I'm not too happy with.
# Tried to use static methods and functions outside a class
# but ran into trouble with autosaving.
class DataManager:
    """Manage data generated by the bot."""

    # Avoid reloading data automatically unless the bot is restarted.
    HAS_LOADED_DATA = False
    # In seconds.
    AUTOSAVE_INTERVAL = 3600
    # Path to the JSON file that stores the seralized data.
    JSON_PATH = 'src/data/guilds.json'

    def __init__(self):
        self.guilds = []

    def get_guild(self, disc_guild_obj: discord.Guild) -> 'models.Guild':
        """Get the Guild object associated with a given Discord guild."""
        try:
            guild = next(i for i in self.guilds if i.disc_guild_obj == disc_guild_obj)

        except StopIteration:
            self.guilds.append(guild := models.Guild(disc_guild_obj))

        return guild

    @disc_tasks.loop(seconds=AUTOSAVE_INTERVAL)
    async def autosave(self):
        """Save data periodically."""
        self.save_data()

    async def delete_expired_tasks(self):
        """Delete all expired tasks."""
        for teams in [guild.teams for guild in self.guilds]:
            for team in teams:
                team.delete_expired()

    def save_data(self):
        """Save data from memory to JSON."""
        serialized_guilds = [guild.serialize() for guild in self.guilds]

        with open(DataManager.JSON_PATH, 'w') as fp:
            json.dump(serialized_guilds, fp)

        print(f'Data saved: {serialized_guilds}')

    async def load_data(self, bot: commands.Bot):
        """Load data from JSON to memory."""
        await bot.wait_until_ready()

        try:
            with open(DataManager.JSON_PATH, 'rb') as fp:
                serialized_guilds = json.load(fp)

        except FileNotFoundError:
            return

        self.guilds = list(filter(lambda x: x is not None,
                                  [models.Guild.deserialize(bot, guild)
                                   for guild in serialized_guilds]))

        print(f'Data loaded: {self.guilds}')


data_manager = DataManager()
