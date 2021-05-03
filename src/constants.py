"""Store constants that are used throughout the package."""

import enum

import discord

VERSION = '2.0.0-rc1'
PREFIX = 'i.'
# Scopes: bot and applications.commands
# Bot permissions: Manage Roles, Add Reactions and Use Slash Commands
INVITE_LINK = ('https://discord.com/api/oauth2/authorize?'
               'client_id=578039213287538701&permissions=2415919168&'
               'scope=bot%20applications.commands')

CHANGELOG = discord.Embed(
    title=':woman_technologist: Ivone __{}__'.format(VERSION),
    description='• TODO',  # TODO
    color=discord.Color.blue())


class Colors(enum.Enum):
    """Standardize color use across the bot."""

    DEFAULT = discord.Color.blue()
    ERROR = discord.Color.red()


class Emojis(enum.Enum):
    """Standardize emoji use across the bot."""

    SUCCESS = ':white_check_mark:'
    ERROR = ':negative_squared_cross_mark:'
    WARNING = ':warning:'

    DEV = ':robot:'
    SPEECH = ':loudspeaker:'

    CONFIG = ':wrench:'
    LOCALE = ':earth_americas:'
    TIMEZONE = ':clock3:'

    NOTIFICATION = ':alarm_clock:'
    MORNING = ':sunrise_over_mountains:'

    TEAMS = ':busts_in_silhouette:'
    JOIN = ':arrow_right:'
    LEAVE = ':arrow_left:'

    CREATE = ':pencil:'
    EDIT = ':pencil2:'
    DELETE = ':wastebasket:'

    DATE = ':calendar_spiral:'
    TAGS = ':label:'
    TASKS = ':bookmark:'

    OTHER = ':mag:'
