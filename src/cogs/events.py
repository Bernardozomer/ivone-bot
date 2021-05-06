"""Listen for events and react to them."""

import datetime as dt
import sys
import traceback
from datetime import datetime

import discord
from discord.ext import commands
from discord_slash import SlashContext

sys.path.append('..')
from core import constants, checks
from core.data_management import data_manager
from utils import dt_utils, iter_utils
from utils.dt_utils import DATE_FORMATS, TIME_FORMATS


class Events(commands.Cog):
    """Listen for events and react to them."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_slash_command_error(self, ctx: SlashContext, error: commands.CommandError):
        """Handle failed checks."""
        if isinstance(error, checks.DateHasAlreadyPassedError):
            await ctx.send(embed=discord.Embed(
                title=f'{constants.Emojis.ERROR.value} This date has already passed.',
                description='If you have a future year in mind, add it to the end of the date.',
                color=constants.Colors.ERROR.value))

        elif isinstance(error, checks.GuildHasNoControlRolesError):
            await ctx.send(embed=discord.Embed(
                title=f'{constants.Emojis.ERROR.value} There are no control roles in this server.',
                description='Create a control role with `/new_control_role`.',
                color=constants.Colors.ERROR.value))

        elif isinstance(error, checks.GuildHasNoTeamsError):
            await ctx.send(embed=discord.Embed(
                title=f'{constants.Emojis.ERROR.value} There are no teams in this server.',
                description='Create a new team with `/new_team`.',
                color=constants.Colors.ERROR.value))

        elif isinstance(error, checks.InvalidRoleError):
            await ctx.send(embed=discord.Embed(
                title=f'{constants.Emojis.ERROR.value} Invalid role.',
                color=constants.Colors.ERROR.value))

        elif isinstance(error, checks.NoActiveTasksError):
            await ctx.send(embed=discord.Embed(
                title=f'{constants.Emojis.SUCCESS.value} There are no active tasks.',
                color=error.team.role.color
            ).set_footer(text=error.team.role.name.upper()))

        elif isinstance(error, checks.NoTasksDueOnDateError):
            if error.was_expected:
                emoji = constants.Emojis.SUCCESS.value
                color = error.team.role.color

            else:
                emoji = constants.Emojis.ERROR.value
                color = constants.Colors.ERROR.value

            date = dt_utils.date_to_relative_name(error.date, error.team.guild.tz,
                                                  error.team.guild.locale)

            await ctx.send(embed=discord.Embed(
                title=f'{emoji} There are no tasks due on __{date}__.',
                color=color
            ).set_footer(text=error.team.role.name.upper()))

        elif isinstance(error, checks.NoTasksTaggedWithError):
            await ctx.send(embed=discord.Embed(
                title=f'{constants.Emojis.TAGS.value} There aren\'t any tasks tagged'
                      f' with __{iter_utils.format_iter(error.tags)}__',
                color=error.team.role.color))

        elif isinstance(error, checks.UserDoesNotHavePermission):
            await ctx.send(embed=discord.Embed(
                title=f'{constants.Emojis.ERROR.value} You don\'t have permission'
                      f' to perform this action.',
                color=constants.Colors.ERROR.value))

        elif isinstance(error, checks.UserIsNotAnAdminError):
            await ctx.send(embed=discord.Embed(
                title=f'{constants.Emojis.ERROR.value} You need administrator rights'
                      f' within the server to do that.',
                color=constants.Colors.ERROR.value))

        elif isinstance(error, checks.UserIsNotInATeamError):
            await ctx.send(embed=discord.Embed(
                title=f'{constants.Emojis.ERROR.value} You need to be in a team to do that.',
                description='View the server\'s teams with `/teams`.',
                color=constants.Colors.ERROR.value))

        else:
            print('Ignoring exception in command {}:'.format(ctx.command), file=sys.stderr)
            traceback.print_exception(type(error), error, error.__traceback__, file=sys.stderr)

    @commands.Cog.listener()
    async def on_guild_join(self, disc_guild_obj: discord.Guild):
        """Send greetings when entering a guild."""

        print('>> {time}: Ivone has entered {guild}'
              .format(time=datetime.strftime(datetime.now(), '%H:%M'),
                      guild=disc_guild_obj))

        guild = data_manager.get_guild(disc_guild_obj)

        await guild.target_channel.send(
            embed=discord.Embed(
                title=f':grinning: Hello, __{guild.disc_guild_obj.name}__!',
                description='• **Ivone** is a task management bot for teams using Discord.'
                            ' Be it at school, work or anywhere else, Ivone keeps you organized.'
                            '\n• To start, create a team with `/new_team`.'
                            '\n• For more information, use `/help`.'
                            '\n• Problems? Suggestions? Use `/feedback`!',
                color=constants.Colors.DEFAULT.value))

        # Warn the guild about their current (probably default) timezone and locale.
        example_date = dt.date(year=1970, month=12, day=1)
        example_time = dt.time(hour=12, minute=0)
        tz_offset = guild.tz.utcoffset(None).total_seconds() / 3600

        await guild.target_channel.send(
            embed=discord.Embed(
                title=f'{constants.Emojis.WARNING.value} Warning: check timezone and locale',
                description=f'Right now, this server\'s locale is set to {guild.locale}.'
                            f' That means midday of december 1st will be formatted as'
                            f' {example_date.strftime(DATE_FORMATS[guild.locale])}'
                            f' {example_time.strftime(TIME_FORMATS[guild.locale])},'
                            f' for example.'
                            f'\nAlso, the timezone is set to'
                            f' UTC {"+" if tz_offset > 0 else ""}{tz_offset}.'
                            f'\nTo change these settings, use `/change_timezone`'
                            f' and `/change_locale`.',
                color=constants.Colors.ERROR.value))

    @commands.Cog.listener()
    async def on_guild_role_delete(self, role: discord.Role):
        """Delete data that relied on a role that no longer exists."""
        guild = data_manager.get_guild(role.guild)

        if team := guild.get_team(role):
            guild.teams.remove(team)

        elif control_role := guild.get_control_role(role):
            guild.control_roles.remove(control_role)

    @commands.Cog.listener()
    async def on_ready(self):
        """Load data."""
        await self.bot.change_presence(activity=discord.Activity(
            type=discord.ActivityType.listening, name='/help'))

        if not data_manager.HAS_LOADED_DATA:
            await data_manager.load_data(self.bot)
            data_manager.HAS_LOADED_DATA = True
            data_manager.autosave.start()


def setup(bot: commands.Bot):
    """Add the cog to the bot."""
    bot.add_cog(Events(bot))
