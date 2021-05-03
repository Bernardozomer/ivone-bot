"""Create, delete and show teams in a guild."""

import discord
from discord.ext import commands
from discord_slash import cog_ext, SlashContext
from discord_slash.utils.manage_commands import create_option

from src import constants, checks, models
from src.data_management import data_manager
from src.utils import iter_utils


class Teams(commands.Cog):
    """Create, delete and show teams in a guild."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.check(checks.does_guild_have_teams)
    @commands.check(checks.is_admin)
    @cog_ext.cog_slash(
        name='delete_team',
        description='Delete a team. Irreversible!',
        options=[
            create_option(
                name='team_role',
                description='The role used for the team you wish to delete.',
                option_type=8,
                required=True
            ),
            create_option(
                name='confirmation',  # The id of the guild to be deleted.
                description='Type here the confirmation number sent by the bot.',
                option_type=3,  # Discord doesn't recognize 18-char long numbers as integers.
                required=False
            )
        ]
    )
    async def _delete_team(self, ctx: SlashContext, team_role: discord.Role,
                           confirmation: str = None):
        """Delete a team.
        After selecting a team, the user will be asked to repeat the command with its role ID
        to ensure they're aware of the action they're performing and of its consequences.
        """

        guild = data_manager.get_guild(ctx.guild)
        team = checks.is_role_tied_to_team(guild, team_role)

        if confirmation is not None and int(confirmation) == team_role.id:
            await guild.del_team(guild.get_team(team_role))

            embed = discord.Embed(
                title=f'{constants.Emojis.DELETE.value} __{team_role}__ and all its data'
                      f' was deleted.',
                color=constants.Colors.ERROR.value)

        else:
            embed = discord.Embed(
                title=f'{constants.Emojis.WARNING.value} Are you sure'
                      f' you want to delete __{team.role}__?',
                description=f'This action is irreversible and will erase all your data.'
                            f'\nTo confirm, use `/delete_team {team_role} {team_role.id}`.',
                color=constants.Colors.ERROR.value)

        await ctx.send(embed=embed)

    @commands.check(checks.is_admin)
    @commands.check(checks.is_user_in_a_team)
    @cog_ext.cog_slash(
        name='edit_notifications',
        description='Edit when the bot should send task notifications to your team.',
        options=[
            create_option(
                name='batch',
                description='Batch notifications are sent early in the morning'
                            ' and detail the whole day.',
                option_type=5,
                required=True
            ),
            create_option(
                name='early',
                description='Early notifications are reminders sent an x amount of time'
                            ' before a task is due.',
                option_type=5,
                required=True
            ),
            create_option(
                name='early_time',
                description='In minutes, how many time before a task is due an early notification'
                            'will be sent. Default is 60.',
                option_type=4,
                required=True
            ),
            create_option(
                name='exact',
                description='Exact notifications are sent when a task is due.',
                option_type=5,
                required=True
            ),
        ]
    )
    async def _edit_notifications(self, ctx: SlashContext, batch: bool, early: bool,
                                  early_time: int, exact: bool):
        """Edit when the bot should send task notifications to a team."""
        guild = data_manager.get_guild(ctx.guild)
        team = await guild.get_user_team(self.bot, ctx)

        team.notify.update({'batch': batch, 'early': early,
                            'early_time': early_time, 'exact': exact})

        embed = discord.Embed(
            title=f'{constants.Emojis.CONFIG.value} Notification settings'
                  f' updated for __{team.role}__:',
            description=f'Note: this will not affect tasks already created.'
                        f'\n{iter_utils.format_dict(team.notify)}',
            color=team.role.color
        ).set_footer(text=team.role.name.upper())

        await ctx.send(embed=embed)

    @commands.check(checks.is_admin)
    @cog_ext.cog_slash(
        name='new_team',
        description='Crete a new team in the server.',
        options=[
            create_option(
                name='name',
                description='What your new team will be named.',
                option_type=3,
                required=True
            )
        ]
    )
    async def _new_team(self, ctx: SlashContext, name: str):
        """Create a new team in the guild."""
        guild = data_manager.get_guild(ctx.guild)
        checks.does_user_have_permission(guild, ctx.author, 'create teams')

        role = await discord.Guild.create_role(ctx.guild, name=name,
                                               color=constants.Colors.DEFAULT.value)

        role.position = 0
        team = models.Team(role=role)
        guild.add_team(team)

        embed = discord.Embed(
            title=f'{constants.Emojis.TEAMS.value} New team created: \"__{role}__\"',
            description=f'Join the team with `/team`.'
                        f'\n\nUsers who are granted the {role.mention} role'
                        f' will automatically join it.',
            color=constants.Colors.DEFAULT.value)

        await ctx.send(embed=embed)

    @commands.check(checks.does_guild_have_teams)
    @cog_ext.cog_slash(
        name='team',
        description='Join or leave a team.',
        options=[
            create_option(
                name='team_role',
                description='The team you want to join or leave.',
                option_type=8,
                required=True
            )
        ]
    )
    async def _team(self, ctx: SlashContext, team_role: discord.Role):
        """Join or leave a team."""
        guild = data_manager.get_guild(ctx.guild)
        checks.does_user_have_permission(guild, ctx.author, 'join/leave teams')
        team = checks.is_role_tied_to_team(guild, team_role)

        if team in guild.get_user_teams(ctx.author):
            await ctx.author.remove_roles(team.role)
            title = f'{constants.Emojis.LEAVE.value} __{ctx.author}__ has left __{team.role}__.'
            desc = f'Rejoin with `/team {team.role}`.'

        else:
            await ctx.author.add_roles(team.role)
            title = f'{constants.Emojis.JOIN.value} __{ctx.author}__ has joined __{team.role}__.'
            desc = f'Leave it with `/team {team.role}`.'

        embed = discord.Embed(title=title, description=desc, color=team.role.color)
        await ctx.send(embed=embed)

    @commands.check(checks.does_guild_have_teams)
    @cog_ext.cog_slash(
        name='teams',
        description='View every team in the server.',
    )
    async def _teams(self, ctx: SlashContext):
        """Show every team in the guild."""
        guild = data_manager.get_guild(ctx.guild)
        sorted_teams = sorted(guild.teams, key=lambda x: x.role.name)
        desc = ''

        for team in sorted_teams:
            desc += '• ' + ('**(Joined)** ' if team.role in ctx.author.roles else ''
                            ) + f'{team.role}\n'

        desc += '\nJoin or leave a team with `/team`.'

        embed = discord.Embed(title=f'{constants.Emojis.TEAMS.value} Teams in __{ctx.guild}__:',
                              description=desc,
                              color=constants.Colors.DEFAULT.value)

        await ctx.send(embed=embed)


def setup(bot):
    """Add the cog to the bot."""
    bot.add_cog(Teams(bot))
