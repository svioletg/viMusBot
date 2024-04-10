# viMusBot

## You are on the `dev` branch. Switch to the `master` branch here: https://github.com/svioletg/viMusBot/tree/master

### Full changelog: [changelog.md](https://github.com/svioletg/viMusBot/blob/master/changelog.md)

### See progress on bug fixes and new features here: [viMusBot Taskboard](https://github.com/users/svioletg/projects/1/views/1)

---

viMusBot is a Discord music bot with support for Spotify links, written in Python.

> *I'm always looking to improve these instructions. If you find there's missing information, things are unclear, or any other issues, please [open a new issue](https://github.com/svioletg/viMusBot/issues), and I'll try to address any problems when I'm able.*

Start by downloading `Source code (zip)` from the [latest stable release](https://github.com/svioletg/viMusBot/releases/latest), extract the contents wherever you want, and then follow the instructions below as needed.

## Section Links

[Setting Up: Python](#setting-up-python)

[Setting Up: Required software](#setting-up-required-software)

[Setting Up: Discord](#setting-up-discord)

[Setting Up: Spotify API](#setting-up-spotify-api)

[Running & Updating](#running--updating)

## Setting up: Python

viMusBot needs Python in order to run. The [Python homepage](https://www.python.org/downloads) can point you to installers for Windows or MacOS — most Linux distros should have it available in your package manager, or you can download the source from the same link mentioned. As of writing this, viMusBot is fully compatible with Python 3.12, the currently latest major version. If using the Windows installer, **make sure to tick the "Add Python 3.12 to PATH" checkbox** (it may say "Add Python to enviornment variables" instead, check the box regardless.)

Next, you need to install viMusBot's required packages. For a quick and automatic setup on Windows, the `envsetup.bat` script is included which will automatically create a Python virtual enviornment (venv), and install the requirements there. `start.bat` is also included which will run the main script using the newly created venv, as well as `update.bat` which will attempt to automatically update viMusBot itself and its Python dependencies\*. `.bat` files can be run just by double-clicking them.

Otherwise, you can install any requirements by running the command `pip install -r requirements.txt` from within your viMusBot directory. Using a venv isn't required, but is recommended to keep everything self-contained.

## Setting up: Required software

viMusBot requires [FFmpeg and FFprobe](https://www.ffmpeg.org/) to function properly. On Windows, the `getff.bat` script will try to grab the needed files automatically. Otherwise, you can download them manually as described below.

For **Windows**, go to [this page](https://github.com/BtbN/FFmpeg-Builds/releases) and download `ffmpeg-master-latest-win64-gpl.zip`, attached to the top release on the page. Extract this anywhere you'd like, and move or copy `ffmpeg.exe` and `ffprobe.exe` from within `bin` to the same folder as `bot.py`.

For **Mac**, go to [this page](https://evermeet.cx/ffmpeg/) and download the archives for both `FFmpeg` and `FFprobe`. They should each have a single file within named `ffmpeg` and `ffprobe` respectively, add these to your PATH variable or drop them inside the same folder as `bot.py`.

For **Linux**, you can likely install it via your distro's package manger. e.g for Ubuntu, you can run `apt install ffmpeg`. This should also install `ffprobe`, try running both the `ffmpeg` and `ffprobe` commands in a terminal to ensure you have them.

## Setting up: Discord

Go to the [Discord Developer Portal](https://discord.com/developers/applications/) and login with your Discord account. You should land on your "Applications" page — click the blue "**New Application**" button near the top right of the screen, enter any name of your choosing and tick the box to agree to Discord's terms, then finally click "**Create**".

You should now be at the "General Information" page for your app. Using the left-hand sidebar, go to the "**Bot**" page. Here, you can change the username and profile picture that your bot will appear as in your server, which can of course be whatever you choose. You should see a blue button labelled "**Reset Token**" — click it, and after confirming you should see a new long string of random letters and numbers. Copy this string, create a new file called `token.txt` within the same folder as `bot.py`, paste your copied string into it, then save and close the file.

The last thing you'll need to do on the Discord side of things is give the bot its required permissions and "intents". Under the "Privilaged Gateway Intents" section, turn **on** the switches next to "**Server Members Intent**" and "**Message Content Intent**". Below this section, you'll see a "Bot Permissions" box with many checkboxes. viMusBot currently only requires the following to function:

*General Permissions*

- Read Messages/View Channels

*Text Permissions*

- Send Messages
- Send Messages in Threads
- Add Reactions

*Voice Permissions*

- Connect
- Speak

Tick the boxes next to these permissions, and then save your changes. To create an invite link for your bot, click "OAuth2" on the left sidebar and then go to "URL Generator". Under "Scopes", tick only the "bot" checkbox. Under "Bot Permission", select the same ones mentioned earlier. Your link will be at the bottom of this page.

## Setting up: Spotify API

You'll need to supply an API "client ID" and "client secret" in order for Spotify-related functions to work. You will need a Spotify account, but you will **not** need a Spotify Premium subscription.

1. Start by going to your [Spotify for Developers Dashboard](https://developer.spotify.com/dashboard). Once you're logged in and at this page, you should see a blue "**Create app**" button, which you should click.
2. Fill in the Name and Description fields with whatever you want; the "Website" field can be left blank. The Redirect URI field is required, although it will not actually be used by the bot, so you can just enter `localhost`.
3. Under "Which API/SDKs are you planning to use?", select "Web API". Click the checkbox below to agree to Spotify's terms, then hit "Save".
![Spotify app setup page](https://i.imgur.com/hoPjBKE.png)
4. You should now be sent to your app's dashboard with some graphs displayed. On the right side of the screen, click "Settings".
5. Click "View client secret" to reveal the string. The file `spotifysetup.bat` has been included with viMusBot to set up your config automatically — open it, and then paste in the requested information.
![Client ID and client secret fields](https://i.imgur.com/4AoWjWj.png)

*Alternatively*, you can manually create the required `spotify_config.json` file, and then paste in the following...

```json
{
    "spotify":
    {
        "client_id": "YOUR_ID",
        "client_secret": "YOUR_SECRET"
    }
}
```

...where `YOUR_ID` and `YOUR_SECRET` are your app's client ID and client secret respectively.

## Running & Updating

viMusBot should now be fully equipped to run. If you know how to run Python scripts, just run `bot.py`. If you used the `envsetup.bat` file earlier to set up a virtual enviornment, you can use `start.bat` to automatically run the bot within said enviornment. You can stop the bot at any time by pressing `Ctrl` and `C` at the same time, while within the command prompt window.

viMusBot will automatically check for new releases each time it starts. To automatically update your files, run the `update.py` script, or open `update.bat`. If using the latter, all of this project's dependencies will be automatically updated inside of the earlier created enviornment as well, so you should be set. If you only ran the `update.py` script, you'll have to update them manually by using `pip install -r requirements.txt` or whatever is appropriate for your setup.

If you experience any issues with the bot, or you want a new feature added, you're free to [open a new issue](https://github.com/svioletg/viMusBot/issues) so I can look into it when possible.
