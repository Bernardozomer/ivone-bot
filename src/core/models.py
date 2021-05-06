"""Determine the logical structure of the database."""

import asyncio
import datetime
import datetime as dt
import sys
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List, Optional

import discord
import unidecode
from discord.ext import tasks as disc_tasks
from discord.ext import commands
from discord_slash import SlashContext

sys.path.append('..')
from . import constants
from utils import iter_utils, dt_utils

class Guild:
    """Represent a Discord guild."""

    # In days.
    AUTO_BATCH_INTERVAL = 1
    # In 24h format.
    BATCH_TIME = dt.time(hour=6)

    def __init__(self,
                 disc_guild_obj: discord.Guild,
                 target_channel: discord.TextChannel = None,
                 receive_announcements: bool = True,
                 teams: List['Team'] = None,
                 control_roles: List['ControlRole'] = None,
                 locale: str = None,
                 tz_offset: int = None):
        # Associate a Discord Guild object with this guild.
        self.disc_guild_obj = disc_guild_obj

        # Set the channel where the bot will send all its announcements.
        if not target_channel:
            target_channel = self.search_for_target_channel()
        self._target_channel = target_channel

        self.receive_announcements = receive_announcements

        if not teams:
            teams = []
        self.teams = teams

        if not control_roles:
            control_roles = []
        self.control_roles = control_roles

        if not locale:
            locale = 'en-US'
        self.locale = locale

        # Guild admins have to manually adjust this for daylight savings and etc.
        if not tz_offset:
            tz_offset = -5  # EST
        self._tz = timezone(timedelta(hours=tz_offset))

        # Start background tasks.
        self.auto_batch_notify.start()

    @property
    def target_channel(self):
        can_use_target_channel = (self._target_channel.permissions_for(self.disc_guild_obj.me)
                                  .send_messages)

        if not self._target_channel or not can_use_target_channel:
            self.search_for_target_channel()

        return self._target_channel

    @target_channel.setter
    def target_channel(self, target_channel):
        self._target_channel = target_channel

    @property
    def tz(self):
        return self._tz

    @tz.setter
    def tz(self, tz: timezone):
        self._tz = tz
        self.auto_batch_notify.restart()

        for team in self.teams:
            team.update_tz(tz)

    def add_team(self, team: 'Team'):
        """Add a team to the guild."""
        team.guild = self
        self.teams.append(team)

    def get_team(self, role: discord.Role) -> Optional['Team']:
        """Return the team tied to a role."""
        return next((i for i in self.teams if i.role == role), None)

    async def del_team(self, team: 'Team'):
        """Delete a team."""
        await team.role.delete()
        self.teams.remove(team)

    async def get_user_team(self, bot: commands.Bot, ctx: SlashContext) -> 'Team':
        """Return every the team a user is in."""
        user_teams = self.get_user_teams(ctx.author)

        if len(user_teams) == 1:
            return user_teams[0]

        # User is in more than one team and will have to choose.
        team = await Guild.team_selector(bot, ctx, user_teams)
        return team

    def get_user_teams(self, user: discord.Member) -> List['Team']:
        """Return all teams a guild member is in."""
        return [i for i in self.teams if i.role in user.roles]

    @staticmethod
    async def team_selector(bot: commands.Bot, ctx: SlashContext, teams) -> Optional['Team']:
        """Show the user an interactive menu to specify which team
        they want to perform an action as a member of.
        """

        message = await ctx.send(embed=discord.Embed(
            title=f'{constants.Emojis.TEAMS.value} Select one of your teams first:',
            description=f'{iter_utils.iter_to_numbered_list([team.role for team in teams])}',
            color=constants.Colors.DEFAULT.value))

        # Use emojis as buttons that correspond to every team they're in.
        for index, team in enumerate(teams):
            await message.add_reaction(iter_utils.DIGIT_EMOJIS[index + 1])

        def check(reaction_, user_):
            return user_ == ctx.author and reaction_.emoji in iter_utils.DIGIT_EMOJIS

        try:
            reaction, _ = await bot.wait_for('reaction_add', timeout=60.0, check=check)
            team = teams[iter_utils.DIGIT_EMOJIS.index(reaction.emoji) - 1]

        except asyncio.TimeoutError:
            await message.delete()
            return None

        await message.delete()
        return team

    def get_control_role(self, role: discord.Role) -> Optional['ControlRole']:
        """Return the control role tied to a role."""
        return next((i for i in self.control_roles if i.role == role), None)

    async def announce(self, embed: discord.Embed):
        """Send an official announcement to the guild's target channel
        if they haven't opted out of receiving them.
        """

        if self.receive_announcements:
            await self.target_channel.send(embed=embed)

    def search_for_target_channel(self) -> Optional[discord.TextChannel]:
        """Return a channel the bot has permissions to send messages in."""
        # Return the system channel if possible.
        if (self.disc_guild_obj.system_channel
                and self.disc_guild_obj.system_channel.permissions_for(
                    self.disc_guild_obj.me).send_messages):
            return self.disc_guild_obj.system_channel

        # Return the first possible channel.
        for channel in self.disc_guild_obj.text_channels:
            if channel.permissions_for(self.disc_guild_obj.me).send_messages:
                return channel

        # No possible channels found.
        return None

    @disc_tasks.loop(seconds=1)
    async def auto_batch_notify(self):
        """Routinely batch notify and delete expired tasks."""
        now = datetime.now(self.tz)

        # Check if it's the correct time of day.
        if now.time().replace(second=0, microsecond=0) == Guild.BATCH_TIME:
            self.delete_expired()

            start = datetime.combine(date=now.date(),
                                     time=Guild.BATCH_TIME,
                                     tzinfo=self.tz)

            stop = datetime.combine(date=now.date() + timedelta(days=Guild.AUTO_BATCH_INTERVAL),
                                    time=Guild.BATCH_TIME,
                                    tzinfo=self.tz)

            await self.batch_notify(start, stop)
            # Wait until the time the next batch notification will take place at.
            await asyncio.sleep(Guild.AUTO_BATCH_INTERVAL * 24 * 3600)

    async def batch_notify(self, start: datetime, stop: datetime):
        """Notify every team of all tasks due on the time period
        between this run and the next.
        """

        for team in self.teams:
            # Jump to the next team if this one has opted out of batch notifications.
            if not team.notify['batch']:
                continue

            # Search for tasks within the specified time range.
            tasks_in_range = team.get_tasks_in_range(start, stop + timedelta(days=1))

            if not tasks_in_range:
                continue

            # Create and send an embed that presents the tasks collected.
            embed = discord.Embed(
                title=f'{constants.Emojis.MORNING.value} Good morning, __{team.role}__!',
                description=f'**__{len(tasks_in_range)}__ task(s)'
                            f' due on the next'
                            f' {Guild.AUTO_BATCH_INTERVAL * 24}h:**',
                color=team.role.color)

            team.tasks_to_embed(tasks_in_range, self.tz, self.locale, embed)
            await self.target_channel.send(f'{team.role.mention}', embed=embed)

    def delete_expired(self):
        """Delete expired tasks in every team."""
        for team in self.teams:
            team.delete_expired()

    def serialize(self) -> Dict[str, Any]:
        """Translate object state to JSON-parsable."""
        serialized_teams = [team.serialize() for team in self.teams]

        serialized_control_roles = [control_role.serialize()
                                    for control_role in self.control_roles]

        return {'id': self.disc_guild_obj.id, 'target_channel_id': self.target_channel.id,
                'receive_announcements': self.receive_announcements,
                'teams': serialized_teams, 'control_roles': serialized_control_roles,
                'locale': self.locale, 'tz_offset': self.tz.utcoffset(None).total_seconds() / 3600}

    @staticmethod
    def deserialize(bot, dict_: Dict[str, Any]) -> Optional['Guild']:
        """Translate JSON-parsable to object state."""
        disc_guild_obj = bot.get_guild(dict_['id'])

        if disc_guild_obj is None:
            return None

        guild = Guild(disc_guild_obj=disc_guild_obj,
                      target_channel=discord.utils.get(disc_guild_obj.channels,
                                                       id=int(dict_['target_channel_id'])),
                      receive_announcements=dict_['receive_announcements'],
                      locale=dict_['locale'],
                      tz_offset=dict_['tz_offset'])

        guild.teams = list(filter(lambda x: x.role is not None,
                                  [Team.deserialize(guild, team) for team in dict_['teams']]))

        guild.control_roles = list(filter(lambda x: x.role is not None,
                                          [ControlRole.deserialize(guild, control_role)
                                           for control_role in dict_['control_roles']]))

        return guild


class ControlRole:
    """Represent a role used to control guild members'
    level of access to the bot.
    """

    DEFAULT_COLOR = discord.Color.greyple()
    PERMS = ['create/edit tasks', 'delete tasks', 'join/leave teams', 'create teams']

    def __init__(self, guild: Guild, role: discord.Role, perms: Dict[str, bool] = None):
        self.guild = guild
        self.role = role
        self.perms = perms

        self.guild.control_roles.append(self)

    def serialize(self) -> Dict[str, Any]:
        """Translate object state to JSON-parsable."""
        return {'role_id': self.role.id, 'perms': self.perms}

    @staticmethod
    def deserialize(guild: Guild, dict_: Dict[str, Any]) -> 'ControlRole':
        """Translate JSON-parsable to object state."""
        role = discord.utils.get(guild.disc_guild_obj.roles, id=int(dict_['role_id']))

        return ControlRole(guild=guild,
                           role=role,
                           perms=dict_['perms'])


class Team:
    """Represent a team."""

    def __init__(self, role: discord.Role, tasks: List['Task'] = None, notify: dict = None):
        # The guild this team belongs to.
        self.guild = None
        # Associate a Discord role object with this team.
        self.role = role

        if tasks is None:
            tasks = []
        self.tasks = tasks

        # Set the team's notification settings.
        if notify is None:
            # Early time is measured in minutes.
            notify = {'batch': True, 'early': True, 'early_time': 60, 'exact': True}
        self.notify = notify

    def add_task(self, task: 'Task'):
        """Write a new task to memory."""
        task.team = self
        self.tasks.append(task)

    def del_task(self, task: 'Task'):
        """Delete a task from memory."""
        self.tasks.remove(task)

    def get_tasks_in_range(self, start: datetime, stop: datetime) -> List['Task']:
        """Return every task which is due sometime within a time range."""
        dates_in_range = [start + timedelta(days=i)
                          for i in range((stop - start).days)]

        tasks_by_date = Team.arrange_by_due_date(self.tasks)

        # Get dates within range that have any tasks due on them.
        intersection = set(i.date() for i in dates_in_range).intersection(
            set(tasks_by_date.keys()))

        # Filter out tasks whose due time are out of range.
        tasks_in_range = [i for date in intersection for i in tasks_by_date[date]
                          if dates_in_range[0] < i.due_datetime <= dates_in_range[-1]]

        return tasks_in_range

    def parse_tags(self, tags: str) -> List[str]:
        """Parse user-inputted tags."""
        return self.search_for_tags([i.rstrip(' .') for i in tags.split(';')])

    def search_for_tags(self, tags: List[str]) -> List[str]:
        """Take various tags as a parameter, adapt their spelling to existing ones'
        when adequate, and then return all of them.
        """

        normalized_existing_tags = {unidecode.unidecode(tag.lower()): tag
                                    for task in self.tasks for tag in task.tags}

        adapted_tags = []

        for tag in tags:
            normalized_tag = unidecode.unidecode(tag.lower())
            adapted_tags.append(normalized_tag if normalized_tag in normalized_existing_tags.keys()
                                else tag)

        return adapted_tags

    def delete_expired(self):
        """Delete every task due on a past date."""
        tasks_by_date = Team.arrange_by_due_date(self.tasks)

        for date in tasks_by_date:
            # If a past date is found, delete every task due on it.
            if date < datetime.now(self.guild.tz).date():
                for task in tasks_by_date[date]:
                    self.del_task(task)

            # In case of the current day, delete tasks by past due time.
            elif date == datetime.now(self.guild.tz).date():
                for task in tasks_by_date[date]:
                    if task.due_datetime < datetime.now(self.guild.tz):
                        self.del_task(task)

    @staticmethod
    def tasks_to_embed(tasks: List['Task'], tz: timezone, locale: str,
                       embed: discord.Embed):
        """Format tasks for user viewing in an embed, separating them by date."""
        tasks_by_due_date = Team.arrange_by_due_date(tasks)

        for date in tasks_by_due_date:
            field_content = Team.format_tasks_due_on_date(tasks_by_due_date[date], locale)

            embed.add_field(
                name=f'• {dt_utils.date_to_relative_name(date, tz, locale).title()}:',
                value=field_content)

    @staticmethod
    def format_tasks_due_on_date(tasks: List['Task'], locale: str) -> str:
        """Format tasks due on the same date for user viewing.
        Can be used for any given collection of tasks,
        but is meant for this specific purpose because it omits their due date.
        """

        output = ''

        for task in tasks:
            output += ('\n**{index}.** {content}'
                       '\n⠀ {due_time}'
                       '\n⠀ {tags}'
                       '\n').format(
                index=tasks.index(task) + 1,
                content=task.content,
                due_time=task.due_datetime.strftime(dt_utils.TIME_FORMATS[locale]),
                tags=iter_utils.format_iter(task.tags) if task.tags else Task.NO_TAGS_TEXT)

        return output

    @staticmethod
    def arrange_by_due_date(tasks: List['Task'] = None) -> Dict[dt.date, List['Task']]:
        """Arrange tasks by their due date."""
        tasks_by_date = {}

        for task in sorted(tasks, key=lambda x: x.due_datetime):
            tasks_by_date.setdefault(task.due_datetime.date(), [])
            tasks_by_date[task.due_datetime.date()].append(task)

        return tasks_by_date

    def update_tz(self, tz: timezone):
        """Update timezone."""
        for task in self.tasks:
            task.update_tz(tz)

    def serialize(self) -> Dict[str, Any]:
        """Translate object state to JSON-parsable."""
        serialized_tasks = [task.serialize() for task in self.tasks]
        return {'role_id': self.role.id, 'notify': self.notify, 'tasks': serialized_tasks}

    @staticmethod
    def deserialize(guild: Guild, dict_: Dict[str, Any]) -> 'Team':
        """Translate JSON-parsable to object state."""
        team = Team(role=discord.utils.get(guild.disc_guild_obj.roles, id=int(dict_['role_id'])),
                    notify=dict_['notify'])

        team.tasks = [Task.deserialize(team, task) for task in dict_['tasks']]
        guild.add_team(team)
        return team


class Task:
    """Represent a task."""

    NO_TAGS_TEXT = '[*No Tags*]'
    SERIALIZED_DT_FMT = '%Y/%m/%d %H:%M'

    def __init__(self, content: str, tags: List[str], due_datetime: datetime):
        # The team this task belongs to.
        self._team = None
        self.content = content
        self.tags = tags
        self.due_datetime = due_datetime

    @property
    def team(self) -> Team:
        """Getter method."""
        return self._team

    @team.setter
    def team(self, team: Team):
        self._team = team
        asyncio.create_task(self.schedule_early_notification())
        asyncio.create_task(self.schedule_notification())

    def to_formatted_string(self) -> str:
        """Return a user-readable description of the task."""
        return ('**Content:** {content}'
                '\n**Due date:** {due_date}'
                '\n**Due time:** {due_time}'
                '\n**Tags:** {tags}'
                ).format(
            content=self.content,
            due_date=dt_utils.format_date(self.due_datetime.date(), self.team.guild.tz,
                                          self.team.guild.locale),
            due_time=self.due_datetime.strftime(dt_utils.TIME_FORMATS
                                                [self.team.guild.locale]),
            tags=iter_utils.format_iter(self.tags)
            if self.tags else Task.NO_TAGS_TEXT)

    async def schedule_early_notification(self):
        """Schedule a notification which reminds users
        this task will be due in an x amount of time.
        """

        # Don't schedule early notification if the team has opted out of them
        # or if there isn't enough time until this task is due.
        #
        # The first check could be made after waiting for the time left,
        # but that wasn't made by design so that, barring the bot restarting,
        # changing team notification settings will never affect active tasks.
        if (not self.team.notify['early']
                or self.due_datetime - timedelta(minutes=self.team.notify['early_time'])
                < datetime.now(self.team.guild.tz)):
            return

        time_left = ((self.due_datetime - datetime.now(self.team.guild.tz))
                     - timedelta(minutes=self.team.notify['early_time'])).total_seconds()

        await asyncio.sleep(time_left)

        # Cancel notification if task has been deleted.
        if self not in self.team.tasks:
            return

        await self.notify(title='Reminder: task due by __{due_date}__ __{due_time}__:'
                          .format(due_date=dt_utils
                                  .date_to_relative_name(self.due_datetime.date(),
                                                         self.team.guild.tz,
                                                         self.team.guild.locale),
                                  due_time=self.due_datetime.strftime('%H:%M')),
                          description=f'{self.content}')

    async def schedule_notification(self):
        """Schedule a notification which tells users this task is due."""
        # This check could be made after waiting for the time left,
        # but that wasn't made by design so that, barring the bot restarting,
        # changing team notification settings will never affect active tasks.
        if self.due_datetime < datetime.now(self.team.guild.tz) or not self.team.notify['exact']:
            return

        time_left = (self.due_datetime - datetime.now(self.team.guild.tz)).total_seconds()
        await asyncio.sleep(time_left)

        # Cancel notification if task has been deleted.
        if self not in self.team.tasks:
            return

        await self.notify(title=self.content, description='')

    async def notify(self, title: str, description: str):
        """Format and send a notification message."""
        embed = discord.Embed(
            title=f'{constants.Emojis.NOTIFICATION.value} {title}',
            description=description,
            color=self.team.role.color
        ).set_footer(text=f'{self.team.role.name.upper()} |'
                          f' Didn\'t want to receive this? use /edit_notifications.')

        if self.tags:
            embed.description += (f'\n{constants.Emojis.TAGS.value}'
                                  f' {iter_utils.format_iter(self.tags)}')

        channel = self.team.guild.target_channel
        await channel.send(f'{self.team.role.mention}', embed=embed)

    def update_tz(self, tz: timezone):
        """Update timezone."""
        self.due_datetime = self.due_datetime.astimezone(tz)

    def serialize(self) -> Dict[str, Any]:
        """Translate object state to JSON-parsable."""
        serialized_tz = self.due_datetime.utcoffset().total_seconds() / 3600
        serialized_dt = self.due_datetime.strftime(Task.SERIALIZED_DT_FMT) + f' {serialized_tz}'

        return {'content': self.content, 'tags': self.tags, 'due_datetime': serialized_dt}

    @staticmethod
    def deserialize(team, dict_: Dict[str, Any]) -> 'Task':
        """Translate JSON-parsable to object state."""
        # Split due datetime from timezone offset.
        split_dt = dict_['due_datetime'].rsplit(' ', 1)
        # Deserialize the due datetime.
        due_datetime = datetime.strptime(split_dt[0], Task.SERIALIZED_DT_FMT)
        # Apply the timezone.
        due_datetime = due_datetime.replace(tzinfo=timezone(timedelta(hours=float(split_dt[1]))))
        # Now that it's timezone-aware, convert it to the guild timezone,
        # just in case they differ.
        due_datetime = due_datetime.astimezone(team.guild.tz)

        # Create the task and assign it to its team.
        task = Task(content=dict_['content'],
                    tags=dict_['tags'],
                    due_datetime=due_datetime)

        task.team = team
        return task
