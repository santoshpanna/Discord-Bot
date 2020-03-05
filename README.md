# Discord Bot
A python bot written for personal use.

## Services
- Reddit
  - Game deal news 
    - `scrapes r/freegamefindings, r/steamdeals, r/gamedeals`
  - Crack and Repack news
    - `scrapes r/crackwatch`
- Game Updates
  - CSGO
  - Destiny 2
- Moderation
  - `!remove message <number>`
- Game Specific
  - CSGO
    - `!csgo`
    - `!csgo register <steamid/steamprofile>`
- Status
  - see server status - `!status server`
  - set bot status - `!status set "<status>"`
  - see csgo status, same as `!csgo` - `!status csgo`
- Core
  - Load service - `!load <servicename>`
  - Unload service - `!unload <servicename>`
  - Reload service - `!reload <servicename>`

### Features
- multiple services
- support for multiple guilds
- support for service and channel mapping in guilds

### Upcoming 
- Web interface

### Usage
- update config.cfg variables
- run bot - `python bot.py`
