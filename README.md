# viMusBot

## You are on the `dev` branch. Switch to the `master` branch here: https://github.com/svioletg/viMusBot/tree/master

Full changelog: [changelog.md](https://github.com/svioletg/viMusBot/blob/master/docs/changelog.md)

See progress on bug fixes and new features here: [viMusBot Taskboard](https://github.com/users/svioletg/projects/1/views/1)

---

viMusBot is a Discord music bot with support for Spotify links, written in Python.

Start by downloading the `Source code (zip)` file under **Assets** from the bottom of the [latest stable release](https://github.com/svioletg/viMusBot/releases/latest) page. Extract the contents into a folder anywhere, then follow the instructions below.

## Contents

[Setting Up: Python](#setting-up-python)

[Setting Up: Required software](#setting-up-required-software)

[Setting Up: Discord](#setting-up-discord)

[Setting Up: Spotify API](#setting-up-spotify-api)

[Running & Updating](#running--updating)

[Documentation & Guides](#documentation--guides)

## Setting up: Python

viMusBot needs Python in order to run. The [Python homepage](https://www.python.org/downloads) can point you to installers for Windows or MacOS, while most Linux distros should have it available in your package manager. As of writing this, the most recent major version is Python 3.12, which viMusBot is being written and tested in, and thus this version is recommended.

If you're using the Windows installer, ***make sure to tick the "Add Python 3.12 to PATH" checkbox***. It may say "Add Python to enviornment variables" instead, still check the box regardless.

Next, you need to install viMusBot's required packages. For a quick and automatic setup on Windows, the `envsetup.bat` script is included which will automatically create a Python virtual enviornment (venv) in your viMusBot folder, and install any requirements within it. `start.bat` is also included which will run the main script using the newly created venv, as well as `update.bat` which will attempt to automatically update viMusBot itself and its Python dependencies. `.bat` files are run like any other program - just by double-clicking them.

Otherwise, you can install any requirements by running the command `pip install -r requirements.txt` from within your viMusBot directory. Using a venv isn't required, but is recommended to keep everything self-contained.

## Setting up: Required software

viMusBot requires [FFmpeg and FFprobe](https://www.ffmpeg.org/) to function properly.

For **Windows**, go to [this page](https://github.com/BtbN/FFmpeg-Builds/releases) and download `ffmpeg-master-latest-win64-gpl.zip` ([direct link](https://github.com/BtbN/FFmpeg-Builds/releases/download/latest/ffmpeg-master-latest-win64-gpl.zip)), attached to the top release on the page. Extract this anywhere you'd like, and move or copy `ffmpeg.exe` and `ffprobe.exe` from within the `bin` folder over to the same folder as `bot.py`.

For **Mac**, go to [this page](https://evermeet.cx/ffmpeg/) and download the archives for both `FFmpeg` and `FFprobe`. They should each have a single file within named `ffmpeg` and `ffprobe` respectively, drop them inside the same folder as `bot.py`.

For **Linux**, you can likely install it via your distro's package manger. e.g for Ubuntu, you can run `apt install ffmpeg`. This should also install `ffprobe`, try running both the `ffmpeg` and `ffprobe` commands in a terminal to ensure you have them.

If you already have FFmpeg and FFprobe added to your system's enviornment variables or PATH, then the bot will run just fine without them present in its folder.

## Setting up: Discord

Go to the [Discord Developer Portal](https://discord.com/developers/applications/) and login with your Discord account. You should land on your "Applications" page — click the blue "**New Application**" button near the top right of the screen, enter a name, and hit "**Create**". The application does *not* have to be named "viMusBot".

You should now be at the "General Information" page for your app. Using the left-hand sidebar, go to the "**Bot**" page. Here, you can change the username and profile picture that your bot will appear as in your server.

You should see a blue button labelled "**Reset Token**" — click it, and after confirming you'll get a new long string of random letters and numbers. Copy this string, create a new file called `token.txt` within your viMusBot folder, paste your copied string into it, then save and close the file.

The last thing you'll need to do on the Discord side of things is give the bot its required permissions and "intents". Under the "Privileged Gateway Intents" section, turn **on** the switches next to "**Server Members Intent**" and "**Message Content Intent**". Below this section, you'll see a "Bot Permissions" box with many checkboxes. viMusBot currently only requires the following to function:

*General Permissions*

- Read Messages/View Channels

*Text Permissions*

- Send Messages
- Send Messages in Threads
- Add Reactions

*Voice Permissions*

- Connect
- Speak

Tick the boxes next to these permissions, and then save your changes.

**To create an invite link** for the bot, click "OAuth2" on the left sidebar, then "URL Generator". Under "Scopes", tick only the "bot" checkbox. Under "Bot Permission", select the same permissions shown above. Your link will be at the bottom of this page.

## Setting up: Spotify API

You'll need to supply an API "client ID" and "client secret" in order for Spotify-related functions to work. You will need a Spotify account, but you will **not** need a Spotify Premium subscription.

1. Start by going to your [Spotify for Developers Dashboard](https://developer.spotify.com/dashboard). Once you're logged in and at this page, you should see a blue "**Create app**" button, which you should click.
2. Fill in the Name and Description fields with whatever you want; the "Website" field can be left blank. The Redirect URI field is required, although it will not actually be used by the bot, so you can just enter `localhost`.
3. Under "Which API/SDKs are you planning to use?", select "Web API", then hit "Save".
![Spotify app setup page](https://i.imgur.com/hoPjBKE.png)
4. You should now be sent to your app's dashboard with some graphs displayed. On the right side of the screen, click "Settings".
5. Click "View client secret" to reveal the string.
![Client ID and client secret fields](https://i.imgur.com/4AoWjWj.png)

The `spotifysetup.bat` script has been included with viMusBot to set up your config automatically — if you're on Windows, you can run it, and then paste in the requested information.

Alternatively, you can manually create the required `spotify_config.json` file, and then paste in the following...

```json
{
    "spotify":
    {
        "client_id": "YOUR_ID",
        "client_secret": "YOUR_SECRET"
    }
}
```

...where `YOUR_ID` and `YOUR_SECRET` are your app's client ID and client secret respectively — make sure to keep them surrounded by quotation marks.

## Running & Updating

viMusBot should now be fully equipped to run — `bot.py` is the main Python script. If you used `envsetup.bat` earlier to set up a virtual enviornment, you can use `start.bat` to run the bot within said enviornment. You can stop the bot at any time by typing `stop` into the command prompt or terminal window and hitting enter, by pressing `Ctrl` and `C` at the same time, or by closing the window.

viMusBot will automatically check for new releases each time it starts. To update, run the `update.py` script, or open `update.bat`. The latter will also update the required Python packages — `update.py` will only update the bot's files, so it is recommended to manually update your packages afterwards by using `pip install -r requirements.txt`. Any changes to the required packages will be written into the changelog.

If you experience any issues with the bot, or you want a new feature added, you're free to [open a new issue](https://github.com/svioletg/viMusBot/issues) so I can look into it when possible.

## Documentation & Guides

Extra pages of information are stored inside this repository's `docs` directory. It currently contains the following:

[Changelog](https://github.com/svioleg/viMusBot/blob/master/docs/changelog.md)

[FAQ](https://github.com/svioleg/viMusBot/blob/master/docs/faq.md)

[Using `config.yml` for configuration & customization](https://github.com/svioleg/viMusBot/blob/master/docs/config.md)

[Using the Console](https://github.com/svioleg/viMusBot/blob/master/docs/console.md)
