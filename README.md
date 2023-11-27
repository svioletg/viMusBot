# viMusBot

## You are on the `dev` branch. Switch to the `master` branch here: https://github.com/svioletg/viMusBot/tree/master

## This entire README will be rewritten before the next release. ([Issue #40](https://github.com/svioletg/viMusBot/issues/40))

### Full changelog: [changelog.md](https://github.com/svioletg/viMusBot/blob/master/changelog.md)

### See progress on bug fixes and new features here: [viMusBot Taskboard](https://github.com/users/svioletg/projects/1/views/1)

---

viMusBot is a Discord music bot with support for Spotify links, written in Python. You will need [FFmpeg](https://www.ffmpeg.org/) installed in order for the bot to function - if you don't, this will be explained in [Setting Up: Required software](#setting-up-required-software).

> *My intention for this README is to be as clear and understandable as possible for general users unfamiliar with Python and/or using the command line. If you find some sections are lacking information, poorly worded, or any other issues are present, feel free to [open a new issue](https://github.com/svioletg/viMusBot/issues) so I can get around to fixing it, thank you!*

Start by downloading `Source code (zip)` from the [latest stable release](https://github.com/svioletg/viMusBot/releases/latest), extract the contents wherever you choose, and then follow the instructions below as needed.

## Section Links

[Setting Up: Python](#setting-up-python)

[Setting Up: Required software](#setting-up-required-software)

[Setting Up: Discord](#setting-up-discord)

[Setting Up: Spotify API](#setting-up-spotify-api)

[Running & Updating](#running--updating)

## Setting up: Python

Having Python installed in order to run the bot, which can be gotten from https://www.python.org/downloads. As of writing this, viMusBot is fully compatible with the current latest version, that being Python 3.12. If using the Windows installer, make sure to tick the "Add Python 3.12 to PATH" checkbox near the bottom. You can confirm that Python was successfully installed by opening a command prompt, and running the `py` command.

Next, you need to install viMusBot's required packages. If you're unfamiliar with using Python, the `envsetup.bat` file is included to automatically create a Python virtual enviornment (venv), and install the requirements there. A second batch file, `start.bat`, is also included which will run the main script using the newly created venv. Note that `.bat` files will only work on Windows.

## Setting up: Required software

Aside from Python and its required packages (explained in the next section), you will only need one additional program for the bot and its voice channel-related functions to work: [FFmpeg](https://www.ffmpeg.org/).

For **Linux**, you can likely install it via your distro's package manger. e.g for Ubuntu, you can run `apt install ffmpeg`.

For **Windows**, go to [this page](https://github.com/BtbN/FFmpeg-Builds/releases) and download `ffmpeg-master-latest-win64-gpl.zip`, attached to the top release on the page. Extract this anywhere you'd like, and move or copy `ffmpeg.exe` and `ffprobe.exe` from within `bin` to the same folder as `bot.py`.

For **Mac**, go to [this page](https://evermeet.cx/ffmpeg/) and download the archives for both `FFmpeg` and `FFprobe`. They should each have a single file within named `ffmpeg` and `ffprobe` respectively, add these to your PATH variable or drop them inside the same folder as `bot.py`.

## Setting up: Discord

## Setting up: Spotify API

You'll need to supply an API "client ID" and "client secret" in order for Spotify-related functions to work. The process is fairly simple, and you'll only need a Spotify account - this does **not** require a Spotify Premium subscription.

1. Start by visiting your [Spotify for Developers Dashboard](https://developer.spotify.com/dashboard). Once you're logged in and at this page, you should see a blue "Create app" button.
2. Click "**Create app**", and fill in the Name and Description fields with whatever you want; the Website field can be left blank. The Redirect URI field is required, although it will not actually be used by the bot, so you can just enter `localhost`.
3. Under "Which API/SDKs are you planning to use?", select "Web API". Click the checkbox below to agree to Spotify's terms, and finally hit the blue "Save" button.
![Spotify app setup page](https://i.imgur.com/hoPjBKE.png)
4. You should now be sent to your app's dashboard with some graphs displayed. On the right side of the screen, click "Settings".
5. Click "View client secret" to reveal the string. The file `spotifysetup.bat` has been included with viMusBot to set up your config automatically — open it, and then paste in the requested information.
![Client ID and client secret fields](https://i.imgur.com/4AoWjWj.png)

*Alternatively*, you can also manually create the required `spotify_config.json` file, and then paste in the following:

```json
{
    "spotify":
    {
        "client_id": "YOUR_ID",
        "client_secret": "YOUR_SECRET"
    }
}
```

Where `YOUR_ID` and `YOUR_SECRET` are your app's client ID and client secret respectively.

## Running & Updating

viMusBot should now be fully equipped to run. If you know how to run Python scripts, just run `bot.py`. If you used the `envsetup.bat` file earlier to set up a virtual enviornment, you can use `start.bat` to automatically run the bot within said enviornment. You can stop the bot at any time by pressing `Ctrl` and `C` at the same time, while within the command prompt window.

viMusBot will automatically check for new releases each time it starts. To automatically update your files, run the `update.py` script, or open `update.bat`. If you're using the latter, all of this project's dependencies will be automatically updated as well, so you should be set. If you only ran the `update.py` script, you'll have to update them manually by using `pip install -r requirements.txt`.

If you experience any issues with the bot, or you want a new feature added, you're free to [open a new issue](https://github.com/svioletg/viMusBot/issues) so I can look into it when possible.
