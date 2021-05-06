"""Miscellaneous commands."""

import sys

import discord
from discord.ext import commands
import discord_slash
from discord_slash import cog_ext, SlashContext
from discord_slash.utils.manage_commands import create_option

sys.path.append('..')
from core import constants
from core.hidden import FEEDBACK_CHANNEL_ID


class Other(commands.Cog):
    """Miscellaneous commands."""

    def __init__(self, bot):
        self.bot = bot

    @cog_ext.cog_slash(
        name='feedback',
        description='Send user feedback to the bot developer. Not anonymous!',
        options=[
            create_option(
                name='text',
                description='Type your feedback.',
                option_type=3,
                required=True
            )
        ]
    )
    async def _feedback(self, ctx: SlashContext, text: str):
        """Send user feedback to the Ivone developer."""
        feedback = f'**{ctx.author}** ({ctx.author.id}) sent in **{ctx.guild}**: {text}'
        await self.bot.get_channel(FEEDBACK_CHANNEL_ID).send(feedback)

        await ctx.send(embed=discord.Embed(
            title=f'{constants.Emojis.SPEECH.value} Thank you for the feedback, __{ctx.author}__!',
            color=constants.Colors.DEFAULT.value))

    @cog_ext.cog_slash(
        name='help',
        description='Get help on how to use the bot.',
    )
    async def _help(self, ctx: SlashContext):
        """Send a PM to a user with every public command."""
        embed = discord.Embed(
            title=':grey_question: Help:',
            description='• **Ivone** is a task management bot for teams using Discord.'
                        '\n• [Click here to invite her to your server.]({invite_link})'
                        '\n• To get the bot up and running, create a team and make sure'
                        ' to set your server\'s locale (for date and time formattting)'
                        ' and timezone.'
                        '\n• Below are listed all commands.'
                        ' You can use them by pressing / in your server.'
                        '\n⠀'
            .format(invite_link=constants.INVITE_LINK),
            color=constants.Colors.DEFAULT.value)

        embed.add_field(
            name=f'{constants.Emojis.TASKS.value} TASKS:',
            value='`/tasks`: View all your tasks.'
                  '\n`/summary`: View all your tasks in a summed up manner.'
                  '\n`/due_on`: View tasks due on a certain date.'
                  '\n`/tagged_with`: View tasks tagged with every tag selected.'
                  '\n`/new_task`: Create a new task.'
                  '\n`/edit_task`: Edit a task.'
                  '\n`/delete_tasks`: Delete one or more tasks.'
                  '\n⠀',
            inline=False)

        embed.add_field(
            name=f'{constants.Emojis.TEAMS.value} TEAMS:',
            value='`/teams`: View every team in the server.'
                  '\n`/team`: Join or leave a team.'
                  '\n`/new_team`: Crete a new team in the server.'
                  '\n`/delete_team`: Delete a team. Irreversible!'
                  '\n`/edit_notifications`: Edit when the bot should send'
                  ' task notifications to your team.'
                  '\n⠀',
            inline=False)

        embed.add_field(
            name=f'{constants.Emojis.OTHER.value} OTHER:',
            value='`/help`: View this message.'
                  '\n`/ping`: View the bot\'s latency.'
                  '\n`/feedback`: Send user feedback to the bot developer. Not anonymous!'
                  '\n`/version`: View the bot\'s latest version number and changelog.'
                  '\n`/info`: View some information about the bot.'
                  '\n⠀',
            inline=False)

        embed.add_field(
            name=f'{constants.Emojis.CONFIG.value} CONFIGURATION:',
            value='`/control_roles`: View all control roles in the server.'
                  '\n`/new_control_role`: Create a role that controls guild members\''
                  ' level of access to the bot.'
                  '\n`/edit_control_role`: Edit the level of access users with a control'
                  ' role have to the bot.'
                  '\n`/change_timezone`: Change the server timezone.'
                  '\n`/change_locale`: Change the server locale (for date and time formatting).'
                  '\n`/set_channel`: Change the channel where the bot will send notifications'
                  ' and announcements.'
                  '\n`/do_receive_announcements`: Change whether the server'
                  ' wants to receive official announcements or not.',
            inline=False)

        await ctx.author.send(embed=embed)

    @cog_ext.cog_slash(
        name='info',
        description='View some information about the bot.',
    )
    async def _info(self, ctx: SlashContext):
        """Show some information about the bot."""
        await ctx.send(embed=discord.Embed(
            title=':information_source: Ivone info',
            description='2019 - 2021, Bernardo Barzotto Zomer.'
                        '\nbernardobarzottoz@gmail.com'
                        '\n\n[Click here to invite the bot.]({invite})'
                        '\nSource code: {src}'
                        '\nIvone {version}'
                        '\ndiscord.py {discordpy}'
                        '\ndiscord-py-slash-command {slash}'
            .format(invite=constants.INVITE_LINK,
                    src=constants.SOURCE,
                    version=constants.VERSION,
                    discordpy=discord.__version__,
                    slash=discord_slash.__version__),
            color=constants.Colors.DEFAULT.value))

    @cog_ext.cog_slash(
        name='ping',
        description='View the bot\'s latency.',
    )
    async def _ping(self, ctx: SlashContext):
        """Show the bot's latency."""
        await ctx.send(embed=discord.Embed(
            title=':ping_pong: Pong! ({} ms)'.format(round(self.bot.latency * 1000)),
            color=constants.Colors.DEFAULT.value))

    @cog_ext.cog_slash(
        name='version',
        description='View the bot\'s latest version number and changelog.',
    )
    async def _version(self, ctx: SlashContext):
        """Show the latest version number and changelog."""
        await ctx.send(embed=constants.CHANGELOG)


def setup(bot):
    """Add the cog to the bot."""
    bot.add_cog(Other(bot))
