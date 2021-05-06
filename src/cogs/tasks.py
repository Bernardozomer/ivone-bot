"""Create, delete and show tasks in a team."""

import sys
from datetime import datetime, timedelta

import discord
from discord.ext import commands
from discord_slash import cog_ext, SlashContext
from discord_slash.utils.manage_commands import create_option, create_choice

sys.path.append('..')
from core import constants, checks, models
from core.data_management import data_manager
from utils import dt_utils, iter_utils
from utils.dt_utils import DATE_FORMATS, TIME_FORMATS


class Tasks(commands.Cog):
    """Create, delete and show tasks in a team."""

    DEFAULT_DUE_TIME = '23:59'

    def __init__(self, bot):
        self.bot = bot

    @commands.check(checks.is_user_in_a_team)
    @cog_ext.cog_slash(
        name='delete_tasks',
        description='Delete one or more tasks.',
        options=[
            create_option(
                name='date',
                description='The date the tasks you wish to delete are due on.',
                option_type=3,
                required=True
            ),
            create_option(
                name='indexes',
                description='The tasks\' indexes on the task list'
                            ' (separate indexes with a semicolon).',
                option_type=3,
                required=False
            )
        ]
    )
    async def _delete_tasks(self, ctx: SlashContext, date: str, indexes: str = None):
        """Delete tasks by their due date and index."""
        # Get the necessary information and check it.
        guild = data_manager.get_guild(ctx.guild)
        checks.does_user_have_permission(guild, ctx.author, 'delete tasks')

        date = dt_utils.string_to_date(date, guild.tz, DATE_FORMATS[guild.locale] + '/%Y')
        checks.has_date_passed(date, guild.tz)

        team = await guild.get_user_team(self.bot, ctx)
        tasks = checks.are_there_tasks_due_on_date(team, date)

        if not indexes:
            # Show every task due on the date, sorted by index.
            embed = discord.Embed(
                title=f'{constants.Emojis.DELETE.value} Which tasks do you wish to delete?',
                description='Use `/delete_tasks {} [indexes]`.\n'
                .format(dt_utils.format_date(date, guild.tz, guild.locale)),
                color=team.role.color)

            embed.description += models.Team.format_tasks_due_on_date(tasks, guild.locale)

        else:
            # Delete the tasks.
            indexes = [int(i) for i in indexes.split(';')]
            tasks_selected = []

            for index in indexes:
                tasks_selected.append(tasks[index - 1])
                team.del_task(tasks_selected[-1])

            embed = discord.Embed(
                title=constants.Emojis.DELETE.value + ' __{}__ task(s) due on'
                                                      ' __{}__ was/were deleted:'
                .format(len(tasks_selected), dt_utils.format_date(date, guild.tz, guild.locale)),
                description=iter_utils.format_iter(list(i.content for i in tasks_selected)),
                color=team.role.color)

        embed.set_footer(text=team.role.name.upper())
        await ctx.send(embed=embed)

    @commands.check(checks.is_user_in_a_team)
    @cog_ext.cog_slash(
        name='due_on',
        description='View taskss due on a certain date.',
        options=[
            create_option(
                name='date',
                description='Defaults to today or tomorrow, depending on time of day.',
                option_type=3,
                required=False
            )
        ]
    )
    async def _due_on(self, ctx: SlashContext, date: str = None):
        """Show every task due on a date by due time."""
        team = await data_manager.get_guild(ctx.guild).get_user_team(self.bot, ctx)
        tasks_by_date = models.Team.arrange_by_due_date(team.tasks)

        if date:
            # Parse date.
            date = dt_utils.string_to_date(date, team.guild.tz,
                                           DATE_FORMATS[team.guild.locale] + '/%Y')
            checks.has_date_passed(date, team.guild.tz)

        else:
            # Default date to today or tomorrow, depending on time of day.
            now = datetime.now(team.guild.tz)
            date = now.date()

            if now.time() >= models.Guild.BATCH_TIME:
                date += timedelta(days=1)

        if date not in tasks_by_date:
            raise checks.NoTasksDueOnDateError(team, date, was_expected=True)

        # Format and send message.
        embed = discord.Embed(
            title=constants.Emojis.DATE.value + ' Tasks due on __{}__:'
            .format(dt_utils.date_to_relative_name(date, team.guild.tz, team.guild.locale)),
            color=team.role.color)

        for task in tasks_by_date[date]:
            formatted_time = date.strftime(task.due_datetime.strftime
                                           (TIME_FORMATS[team.guild.locale]))

            embed.add_field(
                name=f'• {formatted_time}:',
                value=('\n⠀ **{content}**'
                       '\n⠀ {tags}'
                       '\n'
                       ).format(
                    content=task.content,
                    tags=iter_utils.format_iter(task.tags)
                    if task.tags else models.Task.NO_TAGS_TEXT))

        embed.set_footer(text=team.role.name.upper())
        await ctx.send(embed=embed)

    @commands.check(checks.is_user_in_a_team)
    @cog_ext.cog_slash(
        name='edit_task',
        description='Edit a task.',
        options=[
            create_option(
                name='date',
                description='The date your task is due on.',
                option_type=3,
                required=True
            ),
            create_option(
                name='task_index',
                description='The task index on the task list.',
                option_type=4,
                required=False
            ),
            create_option(
                name='attribute',
                description='The attribute you wish to edit.',
                option_type=3,
                required=False,
                choices=[
                    create_choice(
                        value='content',
                        name='Content'
                    ),
                    create_choice(
                        value='due date',
                        name='Due date'
                    ),
                    create_choice(
                        value='due time',
                        name='Due time'
                    ),
                    create_choice(
                        value='tags',
                        name='Tags'
                    )
                ]
            ),
            create_option(
                name='new_value',
                description='The new value you wish to assign to the attribute'
                            ' you are editing.',
                option_type=3,
                required=False
            )
        ]
    )
    async def _edit_task(self, ctx: SlashContext, date: str, task_index: int = None,
                         attribute: str = None, new_value: str = None):
        """Edit a single attribute in a task."""
        # Get the necessary information and check it.
        guild = data_manager.get_guild(ctx.guild)
        checks.does_user_have_permission(guild, ctx.author, 'create/edit tasks')

        date = dt_utils.string_to_date(date, guild.tz, DATE_FORMATS[guild.locale] + '/%Y')
        checks.has_date_passed(date, guild.tz)

        team = await guild.get_user_team(self.bot, ctx)
        tasks = checks.are_there_tasks_due_on_date(team, date)

        if not task_index:
            # Show every task due on the selected date.
            embed = discord.Embed(
                title=f'{constants.Emojis.EDIT.value} Which task do you wish to edit?',
                description='Use `/edit_task {} [index]`.\n'
                .format(dt_utils.format_date(date, guild.tz, guild.locale)),
                color=team.role.color)

            embed.description += models.Team.format_tasks_due_on_date(tasks, guild.locale)

        else:
            # Show every attribute of the selected task.
            task = tasks[int(task_index) - 1]

            if not attribute:
                embed = discord.Embed(
                    title=f'{constants.Emojis.EDIT.value} Which attribute of this task'
                          f' do you wish to edit?',
                    description=('Use `/edit_task {date} {task_index} [attribute] [new value]`.'
                                 '\n\n{task}')
                    .format(date=dt_utils.format_date(date, guild.tz, guild.locale),
                            task_index=task_index,
                            task=task.to_formatted_string()),
                    color=team.role.color)

            else:
                # Edit the task.
                if attribute == 'content':
                    task.content = new_value

                elif attribute == 'due date':
                    new_due_date = dt_utils.string_to_date(
                        new_value, guild.tz, DATE_FORMATS[guild.locale] + '/%Y')

                    new_due_datetime = task.due_datetime.replace(
                        day=new_due_date.day,
                        month=new_due_date.month,
                        year=new_due_date.year)

                    # In case the task was edited to be due today and had a
                    # due time now already in the past, change it to 23:59.
                    try:
                        checks.has_datetime_passed(new_due_datetime, guild.tz)

                    except checks.DateHasAlreadyPassedError:
                        new_due_datetime = new_due_datetime.replace(hour=23, minute=59)
                        checks.has_datetime_passed(new_due_datetime, guild.tz)

                    task.due_datetime = new_due_datetime

                elif attribute == 'due time':
                    new_due_time = datetime.strptime(new_value, DATE_FORMATS[guild.locale])

                    new_due_datetime = task.due_datetime.replace(
                        hour=new_due_time.hour, minute=new_due_time.minute)

                    checks.has_datetime_passed(new_due_datetime, guild.tz)
                    task.due_datetime = new_due_datetime

                elif attribute == 'tags':
                    task.tags = team.parse_tags(new_value)

                embed = discord.Embed(
                    title=f'{constants.Emojis.EDIT.value} Task edited successfully:',
                    description=f'{task.to_formatted_string()}',
                    color=team.role.color)

        embed.set_footer(text=team.role.name.upper())
        await ctx.send(embed=embed)

    @commands.check(checks.is_user_in_a_team)
    @cog_ext.cog_slash(
        name='new_task',
        description='Create a new task.',
        options=[
            create_option(
                name='content',
                description='What this task is about.',
                option_type=3,
                required=True
            ),
            create_option(
                name='due_date',
                description='The date this task is due on.',
                option_type=3,
                required=True
            ),
            create_option(
                name='due_time',
                description='The time of day this task is due by.',
                option_type=3,
                required=False
            ),
            create_option(
                name='tags',
                description='What this task will be tagged with'
                            ' (separate tags with a semicolon).',
                option_type=3,
                required=False
            )
        ]
    )
    async def _new_task(self, ctx: SlashContext, content: str, due_date: str,
                        due_time: str = None, tags: str = None):
        """Create a new task."""
        guild = data_manager.get_guild(ctx.guild)
        checks.does_user_have_permission(guild, ctx.author, 'create/edit tasks')

        if due_time:
            # Parse due time.
            due_time = datetime.strptime(due_time.upper(), TIME_FORMATS[guild.locale]).time()

        else:
            # Use default value.
            due_time = datetime.strptime(Tasks.DEFAULT_DUE_TIME, '%H:%M').time()

        due_date = dt_utils.string_to_date(due_date, guild.tz, DATE_FORMATS[guild.locale] + '/%Y')
        due_datetime = datetime.combine(due_date, due_time).replace(tzinfo=guild.tz)
        checks.has_datetime_passed(due_datetime, guild.tz)

        # Parse tags.
        team = await guild.get_user_team(self.bot, ctx)
        tags = team.parse_tags(tags) if tags is not None else []

        # Create the task and add it to the team.
        new_task = models.Task(content, tags, due_datetime)
        team.add_task(new_task)

        # Send confirmation.
        embed = discord.Embed(
            title=constants.Emojis.CREATE.value + ' New task due by'
                                                  ' __{due_date}__ __{due_time}__ created:'
            .format(
                due_date=dt_utils.date_to_relative_name(new_task.due_datetime.date(),
                                                        guild.tz, guild.locale),
                due_time=new_task.due_datetime.strftime(TIME_FORMATS[guild.locale])),
            description=f'{new_task.content}\n',
            color=team.role.color
        ).set_footer(text=team.role.name.upper())

        if tags:
            embed.add_field(
                name=f'{constants.Emojis.TAGS.value} Tags:',
                value=f'{iter_utils.format_iter(new_task.tags)}')

        await ctx.send(embed=embed)

    @commands.check(checks.is_user_in_a_team)
    @cog_ext.cog_slash(
        name='summary',
        description='View all your tasks in a summed up manner.',
    )
    async def _summary(self, ctx: SlashContext):
        """Show by due date how many tasks there are in a team and their tags."""
        team = await data_manager.get_guild(ctx.guild).get_user_team(self.bot, ctx)
        checks.does_team_have_tasks(team)

        tasks_by_due_date = models.Team.arrange_by_due_date(team.tasks)
        description = ''

        for date, tasks in tasks_by_due_date.items():
            formatted_date = dt_utils.format_date(date, team.guild.tz, team.guild.locale)

            description += (f'\n• {formatted_date}:'
                            f' {len(tasks)} task(s)')

            # Cast to set and back to list to remove duplicates.
            tags = list(set(tag for task in tasks for tag in task.tags))

            if tags:
                description += f'\n⠀ *{iter_utils.format_iter(tags)}*'

            description += '\n'

        embed = discord.Embed(
            title=f'{constants.Emojis.TASKS.value} Your tasks (summary):',
            description=description + '\nFor more details, use `/tasks`.',
            color=team.role.color
        ).set_footer(text=team.role.name.upper())

        await ctx.send(embed=embed)

    @commands.check(checks.is_user_in_a_team)
    @cog_ext.cog_slash(
        name='tagged_with',
        description='View tasks tagged with every tag selected.',
        options=[
            create_option(
                name='tags',
                description='Separate tags with a semicolon.',
                option_type=3,
                required=True
            )
        ]
    )
    async def _tagged_with(self, ctx: SlashContext, tags: str):
        """Show all tasks tagged with every tag selected, sorted by due date."""
        team = await data_manager.get_guild(ctx.guild).get_user_team(self.bot, ctx)
        tags = team.parse_tags(tags)
        matching_tasks = checks.are_there_tasks_tagged_with(team.tasks, tags)

        embed = discord.Embed(
            title=f'{constants.Emojis.TAGS.value} {len(matching_tasks)} task(s) tagged'
                  f' with __{iter_utils.format_iter(tags, end=":")}__',
            color=team.role.color)

        team.tasks_to_embed(matching_tasks, team.guild.tz, team.guild.locale, embed)

        embed.set_footer(text=team.role.name.upper())
        await ctx.send(embed=embed)

    @commands.check(checks.is_user_in_a_team)
    @cog_ext.cog_slash(
        name='tasks',
        description='View all your tasks.',
    )
    async def _tasks(self, ctx: SlashContext):
        """Show every task in a team and all of their attributes."""
        team = await data_manager.get_guild(ctx.guild).get_user_team(self.bot, ctx)
        checks.does_team_have_tasks(team)

        embed = discord.Embed(
            title=f'{constants.Emojis.TASKS.value} Your tasks:',
            description='To filter, use `/due_on` or `/tagged_with`.'
                        '\nFor a summed up view, use `/summary`.',
            color=team.role.color
        ).set_footer(text=team.role.name.upper())

        team.tasks_to_embed(team.tasks, team.guild.tz, team.guild.locale, embed)
        await ctx.send(embed=embed)


def setup(bot: commands.Bot):
    """Add the cog to the bot."""
    bot.add_cog(Tasks(bot))
