"""Customize how the bot behaves in a guild."""

import asyncio
from datetime import timedelta, timezone
from typing import Dict

import discord
from discord.ext import commands
from discord_slash import cog_ext, SlashContext
from discord_slash.utils.manage_commands import create_option, create_choice

from src import constants, checks, models
from src.data_management import data_manager
from src.utils import iter_utils


class Configuration(commands.Cog):
    """Customize how the bot behaves in a guild."""

    def __init__(self, bot):
        self.bot = bot

    @commands.check(checks.is_admin)
    @cog_ext.cog_slash(
        name='change_locale',
        description='Change the server locale (for date and time formatting).',
        options=[
            create_option(
                name='locale',
                description='Choose.',
                option_type=3,
                required=True,
                choices=[
                    create_choice(
                        value='en-US',
                        name='English (USA)'
                    ),
                    create_choice(
                        value='other',
                        name='Other'
                    )
                ]
            )
        ]
    )
    async def _change_locale(self, ctx, locale: str):
        """Change the guild locale."""
        guild = data_manager.get_guild(ctx.guild)
        guild.locale = locale

        await ctx.send(embed=discord.Embed(
            title=f'{constants.Emojis.LOCALE.value} Server locale set: __{locale}__',
            description='Note: this will only change how date and time are formatted.',
            color=constants.Colors.DEFAULT.value))

    @commands.check(checks.is_admin)
    @cog_ext.cog_slash(
        name='change_timezone',
        description='Change the server timezone.',
        options=[
            create_option(
                name='offset',
                description='Relative to UTC. For example, EST would be "-5".'
                            ' For non-exact values: -09:30 = "-9.5".',
                option_type=3,
                required=True
            )
        ]
    )
    async def _change_tz(self, ctx, offset: float):
        """Change the guild locale."""
        offset = float(offset)
        guild = data_manager.get_guild(ctx.guild)
        guild.tz = timezone(timedelta(hours=offset))

        await ctx.send(embed=discord.Embed(
            title=constants.Emojis.TIMEZONE.value + ' Server timezone set: __UTC {offset}__'
            .format(offset=f'+{offset}' if offset >= 0 else offset),
            description='Note: will not adapt to daylight savings and etc. automatically.',
            color=constants.Colors.DEFAULT.value))

    @commands.check(checks.is_admin)
    @commands.check(checks.does_guild_have_control_roles)
    @cog_ext.cog_slash(
        name='control_roles',
        description='View all control roles in the server.',
    )
    async def _control_roles(self, ctx: SlashContext):
        """Show all control roles in a guild and their permissions."""
        guild = data_manager.get_guild(ctx.guild)

        # Using helper functions, format a dictionary of roles and their formatted permissions.
        desc = iter_utils.format_dict({f'**{i.role}**': iter_utils.format_dict(i.perms) + '\n'
                                       for i in guild.control_roles})

        desc += ('\nGrant these roles to apply users their permissions.'
                 '\nYou can delete them through Server Settings like any other role.')

        await ctx.send(embed=discord.Embed(
            title=f'{constants.Emojis.CONFIG.value} Control roles in __{ctx.guild}__:',
            description=f'{desc}',
            color=constants.Colors.DEFAULT.value))

    @commands.check(checks.is_admin)
    @commands.check(checks.does_guild_have_control_roles)
    @cog_ext.cog_slash(
        name='edit_control_role',
        description='Edit the level of access users with a control role have to the bot.',
        options=[
            create_option(
                name='role',
                description='Specify the role you wish to edit.',
                option_type=8,
                required=True
            )
        ]
    )
    async def _edit_control_role(self, ctx: SlashContext, role: discord.Role):
        """Edit what users with a control role have permission to do."""
        guild = data_manager.get_guild(ctx.guild)
        control_role = checks.is_role_tied_to_control_role(guild, role)
        control_role.perms = await Configuration.configure_perms(self.bot, ctx, role.name)

    @commands.check(checks.is_admin)
    @cog_ext.cog_slash(
        name='do_receive_announcements',
        description='Change whether the server wants to receive official announcements or not.',
        options=[
            create_option(
                name='receive',
                description='Choose an option.',
                option_type=5,
                required=True
            )
        ])
    async def _do_receive_announcements(self, ctx: SlashContext, receive: bool):
        """Set whether the guild wants to receive official announcements or not."""
        guild = data_manager.get_guild(ctx.guild)
        guild.receive_announcements = receive

        title = (f'{constants.Emojis.CONFIG.value} This server will now'
                 + ('' if receive else ' not') + ' receive announcements.')

        embed = discord.Embed(
            title=title,
            color=constants.Colors.DEFAULT.value)

        await ctx.send(embed=embed)

    @commands.check(checks.is_admin)
    @cog_ext.cog_slash(
        name='new_control_role',
        description='Create a role that controls guild members\''
                    ' level of access to the bot.',
        options=[
            create_option(
                name='name',
                description='Name the new role.',
                option_type=3,
                required=True
            ),
        ]
    )
    async def _new_control_role(self, ctx: SlashContext, name: str):
        """Create a new control role."""
        role = await discord.Guild.create_role(ctx.guild,
                                               name=name,
                                               color=models.ControlRole.DEFAULT_COLOR)

        guild = data_manager.get_guild(ctx.guild)
        control_role = models.ControlRole(guild, role)
        control_role.perms = await Configuration.configure_perms(self.bot, ctx, name)

    @commands.check(checks.is_admin)
    @cog_ext.cog_slash(
        name='set_channel',
        description='Change the channel where the bot will send notifications and announcements.',
        options=[
            create_option(
                name='channel',
                description='Choose an option.',
                option_type=7,
                required=True
            ),
        ]
    )
    async def _set_channel(self, ctx, channel: discord.TextChannel):
        """Set the guild target channel."""
        if isinstance(channel, discord.CategoryChannel):
            return

        guild = data_manager.get_guild(ctx.guild)
        guild.target_channel = channel

        await ctx.send(embed=discord.Embed(
            title=f'{constants.Emojis.CONFIG.value} Channel set: __{guild.target_channel.name}__',
            color=constants.Colors.DEFAULT.value))

    @staticmethod
    async def configure_perms(bot, ctx: SlashContext, name: str) -> Dict[str, bool]:
        title = f'{constants.Emojis.CONFIG.value} Control role configuration'
        description = f'Grant the **__{name}__** role permission to **__{{}}__**?'

        message = await ctx.send(embed=discord.Embed(
            title=title,
            color=constants.Colors.DEFAULT.value))

        # Map emoji reactions to logical values for user input.
        emojis = {'✅': True, '❎': False}

        def check(reaction_: discord.Reaction, user_: discord.Member) -> bool:
            return (user_ == ctx.author and reaction_.emoji in emojis
                    and reaction_.message.id == message.id)

        perms = {}

        for permission in models.ControlRole.PERMS:
            # Prompt user to set control role permission.
            await message.edit(embed=discord.Embed(title=title,
                                                   description=description.format(permission),
                                                   color=constants.Colors.DEFAULT.value))

            # Present the options.
            for emoji in emojis:
                await message.add_reaction(emoji)

            # Wait for user input.
            try:
                reaction, _ = await bot.wait_for('reaction_add', timeout=60, check=check)
                perms[permission] = emojis[reaction.emoji]

            except asyncio.TimeoutError:
                await message.delete()
                raise asyncio.TimeoutError

            await message.clear_reactions()

        # Send confirmation and return.
        await message.edit(embed=discord.Embed(
            title=f'{constants.Emojis.CONFIG.value} Control role configured: \"__{name}__\"',
            description=f'Members who are granted this role will be able to:'
                        f'\n{iter_utils.format_dict(perms)}',
            color=constants.Colors.DEFAULT.value))

        return perms


def setup(bot):
    """Add the cog to the bot."""
    bot.add_cog(Configuration(bot))
