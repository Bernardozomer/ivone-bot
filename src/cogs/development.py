"""Developer-only commands."""

import discord
from discord.ext import commands
from discord.ext.commands import Context

from src import constants, checks
from src.data_management import data_manager


class Development(commands.Cog):
    """Developer-only commands."""

    CMD_EXECUTED = 'Command executed.'

    DEV_HELP_EMBED = discord.Embed(
        title=f'{constants.Emojis.DEV.value} Developer commands:',
        description='`{p}devannounce` (`{p}da`)\n'
                    '`{p}devchangelog` (`{p}dch`)\n'
                    '`{p}devclose` (`{p}dc`)\n'
                    '`{p}devdeleteexpired` (`{p}dde`)\n'
                    '`{p}devhelp` (`{p}dh`)\n'
                    '`{p}devload` (`{p}dl`)\n'
                    '`{p}devsave` (`{p}ds`)\n'
                    '`{p}devtest` (`{p}dt`)'
        .format(p=constants.PREFIX),
        color=constants.Colors.DEFAULT.value)

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    def cog_check(self, ctx: Context) -> bool:
        return checks.is_developer(ctx)

    @commands.command(aliases=['da'])
    async def devannounce(self, ctx: Context, *, message: str):
        """Send a public announcement to every guild."""
        for guild in data_manager.guilds:
            try:
                await guild.announce(embed=discord.Embed(
                    title=f'{constants.Emojis.SPEECH.value} Official announcement:',
                    description=f'{message}',
                    color=constants.Colors.DEFAULT.value))

            # Ignore guild if it has been deleted.
            except commands.errors.CommandInvokeError:
                pass

        await ctx.send(Development.CMD_EXECUTED)

    @commands.command(aliases=['dch'])
    async def devchangelog(self, ctx: Context):
        """Shows to all guilds the latest changelog."""
        for guild in self.bot.guilds:

            # TODO
            """
            if data.guild_config[guild]['changelog'] is True:
                channel = helpers.skim_channels(guild)
            elif data.guild_config[guild]['changelog']:
                channel = self.bot.get_channel(
                    int(data.guild_config[guild]['changelog']))
            else:
                continue

            if channel is not None:
                await channel.send(embed=helpers.get_changelog()
                                   .set_footer(
                    text='Não quer receber este tipo de mensagem, ou prefere outro canal?'
                         ' Use /receberversao (canal).'))
            """

        await ctx.send(Development.CMD_EXECUTED)

    @commands.command(aliases=['dc'])
    async def devclose(self, ctx: Context):
        """Close the bot."""
        await ctx.send('Closing...')
        await self.bot.close()

    @commands.command(aliases=['dde'])
    async def devdeleteexpired(self, ctx: Context):
        """Delete every expired task."""
        await data_manager.delete_expired_tasks()
        await ctx.send(Development.CMD_EXECUTED)

    @commands.command(aliases=['dh'])
    async def devhelp(self, ctx: Context):
        """Show every developer command."""
        if ctx.channel.type != discord.ChannelType.private:
            await ctx.message.add_reaction('✉')

        await ctx.author.send(embed=Development.DEV_HELP_EMBED)

    @commands.command(aliases=['dl'])
    async def devload(self, ctx: Context):
        """Trigger data loading."""
        await data_manager.load_data(self.bot)
        await ctx.send(Development.CMD_EXECUTED)

    @commands.command(aliases=['ds'])
    async def devsave(self, ctx: Context):
        """Trigger data saving."""
        data_manager.save_data()
        await ctx.send(Development.CMD_EXECUTED)

    @commands.command(aliases=['dt'])
    async def devtest(self, ctx: Context):
        """Edit this whenever a command for testing something is needed."""
        guild = data_manager.get_guild(ctx.guild)
        await guild.announce('target_channel')
        await ctx.send(Development.CMD_EXECUTED)


def setup(bot: commands.Bot):
    """Add the cog to the bot."""
    bot.add_cog(Development(bot))
