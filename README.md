# viMusBot

# This README is part of the dev branch! These instructions are likely not accurate! Click [here](https://github.com/svioletg/viMusBot/tree/master) to switch to the master branch.

### Changelog is now located [here](https://github.com/svioletg/viMusBot/blob/master/changelog.md)

---

A bot made in Python 3.10 using the [discord.py](https://github.com/Rapptz/discord.py) library, for personal usage. I wasn't happy enough with the options already available, so I decided to try my own take on it.

Please submit an [issue](https://github.com/svioletg/viMusBot/issues/new) if you've experienced a bug or otherwise odd behavior, or have a feature to request, and feel free to comment on existing issues to provide any additional details that may help narrow down the issue or reach a solution. No bug or feature is too large/small to be submitted, this system is best for me to keep track of everything.

## Important: Before Using
### Do Not Use `dev`
If you're downloading from this repository, *always* download from either the releases page (recommended) or the **master** branch. The **dev** branch is for keeping track of incremental work-in-progress changes that are *not* suitable for general use, and are typically unstable or non-functioning.

### Use On One Server
When I say "an **instance** of the bot" or anything similar, what I'm referring to is *one* `bot.py` script that is currently running, in a single window or `screen` (the command-line tool `screen`, not a monitor screen).

While it's of course fine to have your instance in multiple servers, it should be noted that using it to play music in more than one server at a time *will* cause problems, and it is heavily recommended to only play music through it on one server at any given moment.

I'm aiming to fix this eventually, progress is being tracked in [Issue #17](https://github.com/svioletg/viMusBot/issues/17) if you'd like to see any updates, but for the time being if you really need to have the bot actively playing on multiple servers, the best idea would be to run mutiple separate instances.

## How To Use

The bot will require at least these permissions:

![Required Bot Permissions](https://cdn.discordapp.com/attachments/327195739346173962/1039979708219129966/image.png)

Make sure that "Server Members Intent" and "Message Content Intent" are ticked **on** in the Bot tab.

There are two ways to start using the bot. If you're generally familiar with using the command prompt or terminal for your OS, follow the **Standard Setup** section below. Alternatively, I've provided a script in this project to automatically obtain and walk you through most of the files and information you'll need; in which case, follow the **Using The Wizard** section.

**Regardless of which section you follow**, you must first install the latest version of [Python](https://www.python.org/downloads/). Anything above Python 3.7 should in theory work, but its best to grab the latest one.

**If you are using the Windows installer**, when the installer starts you will see a "Add Python [your version] to PATH" checkbox near the bottom. Make sure that's ticked *on*, or else the `python3` command will not function, and you'll have to add it yourself before you can use any scripts provided here.

If you're installing on Linux, you should be able to run `apt install python3` and be set. Substitute `apt` if you're using a different package manager.

### Standard Setup

- A `headers_auth.json` file for ytmusicapi; see [here](https://ytmusicapi.readthedocs.io/en/latest/setup.html) for how to create it

1. Go to the [latest release](https://github.com/svioletg/viMusBot/releases/latest) of this repository, look in the "Assets" section, and download "Source code" in either .zip or .tar.gz format; extract it wherever you like.
2. Download both FFmpeg and FFprobe and drop them into this created folder (it should have `bot.py` and `spoofy.py` along with some others inside of it)