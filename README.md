# **Ivone**

**A task management bot for teams using Discord. Be it at school, work or anywhere else, Ivone keeps you organized.**

**The official instance of the bot is offline and there are no plans of bringing it back. You can still host it yourself or fork the project.**

> **[Changelog](https://github.com/Bernardozomer/ivone-bot#changelog) | [Overview](https://github.com/Bernardozomer/ivone-bot#overview) | [Setup](https://github.com/Bernardozomer/ivone-bot#setup) | [License](https://github.com/Bernardozomer/ivone-bot#license)**

----

## Changelog:

### **v2.0.1 (2021-05-14)**
- Fixed:
    - The due time of a task can now be edited 

### **v2.0.0 (2021-05-08)**
- Added:
    - Added control roles: roles that control what server members can do with the bot
    - Added support for multiple teams per user
    - Added more configuration options
    - Added support for different date and time formats and any timezone

- Changed:
    - Switched language to English
    - Converted commands to slash commands
    - Changed some nomenclature
    - Restructured the project and data models
    - Changed the style of the README file a bit

## Overview

Ivone is written in Python 3.9+, using the [discord.py](https://github.com/Rapptz/discord.py) and [discord-py-slash-command](https://github.com/eunwoo1104/discord-py-slash-command) libraries.
It's designed for teams to keep track of their active tasks without leaving Discord. With this bot in your server, you can:
- Have multiple teams per server and per user;
- Create, edit and delete tasks;
- View and filter through your active tasks;
- Receive notifications for your tasks in three different moments, or opt out of each one of those;
- Create and grant your server members control roles that determine which permissions they have over the bot's features;
- Have support for two different date and time formats and any timezone;
- And more...

## Setup

To get the bot up and running, simply invite it to your server, create and join a team and start creating your tasks.
You may also want to change the server locale and timezone (default is en-US and EST). These steps are all laid before you as you use the bot.

Bot interaction is done through slash commands, so type / in the chat and wait for the command list to show up.

If you wish to host the bot yourself, you'll need to create a hidden.py module inside the /src directory containing this:

```python
TOKEN = 'your-API-token-here'
FEEDBACK_CHANNEL_ID = 0  # Change for the ID of the channel you wish to use for user feedback.
DEVELOPER_IDS = []  # Fill with the ID of users you want to have developer-level access to the bot.
```

Afterwards, create the /data directory in the project root, where data generated by the bot will be stored in JSON.

Before selfhosting, please ensure that you're following the license. The Ivone bot profile picture isn't included in this source code and should not be used without permission. To avoid confusion, please don't name your instance "Ivone" or something too similar.

Then, to start the bot, simply run /src/main.py.

If you want to contribute to the project, please do!

## License

Licensed under the [GNU General Public License v3.0](https://github.com/Bernardozomer/ivone-bot/blob/master/LICENSE) license.
