"""Check if a command is allowed to run."""

import datetime as dt
import sys
from datetime import datetime, timezone
from typing import List

import discord
from discord.ext import commands
from discord.ext.commands import Context
from discord_slash import SlashContext

sys.path.append('..')
from . import hidden, models
from .data_management import data_manager


def are_there_tasks_due_on_date(team: models.Team, date: dt.date) -> List[models.Task]:
    """Check if there are any tasks due on a certain date and return it if so."""
    try:
        return models.Team.arrange_by_due_date(team.tasks)[date]

    except KeyError:
        raise NoTasksDueOnDateError(team, date, was_expected=False)


def are_there_tasks_tagged_with(tasks, tags) -> List[str]:
    """Check if any of the tasks given are tagged with every given tag
    and return them if so.
    """

    matching_tasks = []

    for task in tasks:
        if set(tags) <= set(task.tags):
            matching_tasks.append(task)

    if not matching_tasks:
        raise NoTasksTaggedWithError

    return matching_tasks


def does_guild_have_control_roles(ctx: SlashContext) -> bool:
    """Check if there are any control roles in a guild."""
    if data_manager.get_guild(ctx.guild).control_roles:
        return True
    raise GuildHasNoControlRolesError()


def does_guild_have_teams(ctx: SlashContext) -> bool:
    """Check if there are any teams in a guild."""
    if data_manager.get_guild(ctx.guild).teams:
        return True
    raise GuildHasNoTeamsError()


def does_team_have_tasks(team: models.Team) -> bool:
    """Check if a team has any active tasks."""
    if team.tasks:
        return True
    raise NoActiveTasksError(team)


def does_user_have_permission(guild: models.Guild, user: discord.Member, action: str) -> bool:
    """Check if a user has permissions within a guild
    to make the bot perform an action.
    """

    user_control_roles = [control_role for control_role in guild.control_roles
                          if control_role.role in user.roles]

    if not user_control_roles:
        # By default, in case the guild member doesn't have any control roles,
        # it is considered that they have full access to the bot.
        return True

    for control_role in user_control_roles:
        if control_role.perms[action] is True:
            # One control role that allows for this action to happen is enough.
            return control_role.perms[action]

    # No control role gave the user permission to perform the action.
    raise UserDoesNotHavePermission


def has_date_passed(date: dt.date, tz: timezone) -> bool:
    """Check if a date has already passed."""
    if date >= datetime.now(tz).date():
        return True
    raise DateHasAlreadyPassedError


def has_datetime_passed(datetime_: datetime, tz: timezone) -> bool:
    """Check if a datetime has already passed."""
    if datetime_ >= datetime.now(tz):
        return True
    raise DateHasAlreadyPassedError


def is_admin(ctx: SlashContext) -> bool:
    """Check if a user has administrator rights."""
    if ctx.channel.permissions_for(ctx.author).administrator:
        return True
    raise UserIsNotAnAdminError(ctx.author)


def is_developer(ctx: Context) -> bool:
    """Check if a user is one of the bot developers."""
    return ctx.author.id in hidden.DEVELOPER_IDS


def is_role_tied_to_control_role(guild: models.Guild, role: discord.Role) -> models.ControlRole:
    """Check if a role is tied to a control role and return it if so."""
    control_role = guild.get_control_role(role)
    if control_role:
        return control_role
    raise InvalidRoleError()


def is_role_tied_to_team(guild: models.Guild, role: discord.Role) -> models.Team:
    """Check if a role is tied to a team and return it if so."""
    team = guild.get_team(role)
    if team:
        return team
    raise InvalidRoleError()


def is_user_in_a_team(ctx: SlashContext) -> bool:
    """Check if a user is in a team."""
    if data_manager.get_guild(ctx.guild).get_user_teams(ctx.author):
        return True
    raise UserIsNotInATeamError(ctx.author, ctx.guild)


class DateHasAlreadyPassedError(commands.CommandError):
    """Raise error when a date not yet passed was expected."""

    def __init__(self):
        super().__init__()


class GuildHasNoControlRolesError(commands.CommandError):
    """Raise error when a guild has no control roles."""

    def __init__(self):
        super().__init__()


class GuildHasNoTeamsError(commands.CommandError):
    """Raise error when a guild has no teams."""

    def __init__(self):
        super().__init__()


class InvalidRoleError(commands.CommandError):
    """Raise error when a role was expected to be tied to the bot in some way."""

    def __init__(self):
        super().__init__()


class NoActiveTasksError(commands.CommandError):
    """Raise error when there are no active tasks in a team."""

    def __init__(self, team: models.Team):
        self.team = team
        super().__init__()


class NoTasksDueOnDateError(commands.CommandError):
    """Raise error when no tasks due on a date could be found."""

    def __init__(self, team: models.Team, date: dt.date, was_expected: bool):
        self.team = team
        self.date = date
        self.was_expected = was_expected
        super().__init__()


class NoTasksTaggedWithError(commands.CommandError):
    """Raise error when no tasks tagged with the selected tags could be found."""

    def __init__(self, team: models.Team, tags: List[str]):
        self.team = team
        self.tags = tags
        super().__init__()


class UserDoesNotHavePermission(commands.CommandError):
    """Raise error when a control role prohibits a user
    from performing an action.
    """

    def __init__(self):
        super().__init__()


class UserIsNotAnAdminError(commands.CommandError):
    """Raise error when a user doesn't have administrator rights."""

    def __init__(self, user: discord.Member):
        self.user = user
        super().__init__()


class UserIsNotInATeamError(commands.CommandError):
    """Raise error when a user isn't in a team."""

    def __init__(self, user: discord.Member, guild: discord.Guild):
        self.user = user
        self.guild = guild
        super().__init__()
