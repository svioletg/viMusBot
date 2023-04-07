# viMusBot

### Full changelog: [changelog.md](https://github.com/svioletg/viMusBot/blob/master/changelog.md)

### See progress on bug fixes and new features here: [viMusBot 1.x](https://github.com/users/svioletg/projects/1/views/1)

---

A bot made in Python 3.10 using the [discord.py](https://github.com/Rapptz/discord.py) library, for personal usage. I wasn't happy enough with the options already available, so I decided to try my own take on it.

Please submit an [issue](https://github.com/svioletg/viMusBot/issues/new) if you've experienced a bug or otherwise odd behavior, or have a feature to request, and feel free to comment on existing issues to provide any additional details that may help narrow down the issue or reach a solution. No bug or feature is too large/small to be submitted, this system is best for me to keep track of everything.

---

If you want to be notified of updates & have a GitHub account, you can click "Watch" on this repository, and then select "Custom" -> "Releases" -> "Apply".

---

## Important: Before Using
### Do Not Use `dev`
If you're downloading from this repository, *always* download from either the [releases page](https://github.com/svioletg/viMusBot/releases/latest) (recommended) or the **master** branch. The **dev** branch is for keeping track of incremental work-in-progress changes that are *not* suitable for general use, and are typically unstable or non-functioning.

### Use On One Server
When I say "an **instance** of the bot" or anything similar, what I'm referring to is *one* `bot.py` script that is currently running, in a single window or `screen` (the command-line tool `screen`, not a monitor screen).

While it's of course fine to have your instance in multiple servers, it should be noted that using it to play music in more than one server at a time *will* cause problems, and it is heavily recommended to only play music through it on one server at any given moment.

I'm aiming to fix this eventually, progress is being tracked in [Issue #17](https://github.com/svioletg/viMusBot/issues/17) if you'd like to see any updates, but for the time being if you really need to have the bot actively playing on multiple servers, the best idea would be to run mutiple separate instances.

## How To Use

If you're not familiar with using the command line or Python, [get Python here](https://www.python.org/downloads/) and skip to [Using The Wizard](#using-the-wizard) for a more guided setup.

I've tried to make this section as thorough as I can, but if you don't mind some googling or are more familiar with the command line, here's the short version:
<<<<<<< HEAD
<<<<<<< HEAD

---

1. Get the source files from the [latest release](https://github.com/svioletg/viMusBot/releases/latest), extract them where you want.
2. Create `spotify_config.json` and `token.txt`. Create an app with the Spotify Web API and enter your Client ID and Client Secret in the following format:
```
{
    "spotify":
    {
        "client_id": "YOUR_ID",
        "client_secret": "YOUR_SECRET"
    }
}
```
3. Ensure you've selected the right intents and permissions (see **Bot Token & Permissions** below), and paste your bot's token into `token.txt`.
4. Duplicate `config_default.yml` and rename the copy as `config.yml` - the bot will only use the latter for its options. Edit it how you like.
5. If FFmpeg and FFprobe aren't installed on your system, either install it through your package manager of choice or download the binaries and drop them in the viMusBot folder.
6. Open a command prompt or terminal in your viMusBot directory, and run `python3 bot.py`.

For a more in-depth tutorial, continue below.

---

There are two ways to start using the bot. If you're generally familiar with using the command prompt or terminal for your OS, follow the [**Standard Setup**](#standard-setup) section below. Alternatively, I've provided a script in this project to automatically obtain and walk you through most of the files and information you'll need; in which case, follow the [**Using The Wizard**](#using-the-wizard) section.

***Regardless of which section you follow***, you must first install the latest version of [Python](https://www.python.org/downloads/). Anything above Python 3.7 should in theory work, but its best to grab the latest one.

***If you are using the Windows installer***, when the installer starts you will see a "Add Python [your version] to PATH" checkbox near the bottom. Make sure that's ticked *on*, or else the `python3` command will not function, and you'll have to add it yourself before you can use any scripts provided here.

If you're installing on Linux, you should be able to run `apt install python3` and be set. Substitute `apt` if you're using a different package manager.

### Standard Setup

Ensure that the latest version of Python has been installed and added to your PATH.

1. Go to the [latest release](https://github.com/svioletg/viMusBot/releases/latest) of this repository, look in the "Assets" section, and download "Source code" in either .zip or .tar.gz format; extract it wherever you like. Inside should be a "viMusBot" folder, which in turn contains all of the files you'll run the bot with.

2. Download both FFmpeg and FFprobe and drop them into the extracted folder - it should have `bot.py` and `spoofy.py` along with some others inside of it.
    - If you're on *Linux*, you likely already have these installed, otherwise `apt install ffmpeg` (or apt equivalent) will install both FFmpeg and FFprobe for you.
    - If you're on *Windows* you'll probably have to download these manually. Go to [ffmpeg.org](https://ffmpeg.org) and find the Windows builds, or click [here](https://github.com/BtbN/FFmpeg-Builds/releases/download/latest/ffmpeg-master-latest-win64-gpl.zip) for a direct download of BtbN's latest Windows build.
        - From this ZIP, go into the "bin" folder found inside and copy "ffmpeg.exe" and "ffprobe.exe" to the bot's folder.

3. Open a command prompt or terminal in your viMusBot folder, and run the command: `pip install -r requirements.txt`
    - If this does not work, try `python3 -m pip install -r requirements.txt`

4. Create the following new documents inside your folder:
    - `spotify_config.json`
    - `token.txt`

5. Copy-paste the "config_default.yml" file, and rename it to "config.yml".
    - It is recommend you keep the original in case you want to completely reset to default or check something.

From this point, skip to [Getting Your Credentials](#getting-your-credentials) to finish setting up.

---

### Using The Wizard

Go to the [latest release](https://github.com/svioletg/viMusBot/releases/latest), download the `vmb-wizard.py` file, and save it anywhere - the bot will not be setup in its directory, rather it will ask you where to download the files to.

=======

---

1. Get the source files from the [latest release](https://github.com/svioletg/viMusBot/releases/latest), extract them where you want.
2. Create `spotify_config.json` and `token.txt`. Create an app with the Spotify Web API and enter your Client ID and Client Secret in the following format:
```
{
    "spotify":
    {
        "client_id": "YOUR_ID",
        "client_secret": "YOUR_SECRET"
    }
}
```
3. Ensure you've selected the right intents and permissions (see **Bot Token & Permissions** below), and paste your bot's token into `token.txt`.
4. Duplicate `config_default.yml` and rename the copy as `config.yml` - the bot will only use the latter for its options. Edit it how you like.
5. If FFmpeg and FFprobe aren't installed on your system, either install it through your package manager of choice or download the binaries and drop them in the viMusBot folder.
6. Open a command prompt or terminal in your viMusBot directory, and run `python3 bot.py`.

For a more in-depth tutorial, continue below.

---

There are two ways to start using the bot. If you're generally familiar with using the command prompt or terminal for your OS, follow the [**Standard Setup**](#standard-setup) section below. Alternatively, I've provided a script in this project to automatically obtain and walk you through most of the files and information you'll need; in which case, follow the [**Using The Wizard**](#using-the-wizard) section.

***Regardless of which section you follow***, you must first install the latest version of [Python](https://www.python.org/downloads/). Anything above Python 3.7 should in theory work, but its best to grab the latest one.

***If you are using the Windows installer***, when the installer starts you will see a "Add Python [your version] to PATH" checkbox near the bottom. Make sure that's ticked *on*, or else the `python3` command will not function, and you'll have to add it yourself before you can use any scripts provided here.

If you're installing on Linux, you should be able to run `apt install python3` and be set. Substitute `apt` if you're using a different package manager.

### Standard Setup

Ensure that the latest version of Python has been installed and added to your PATH.

1. Go to the [latest release](https://github.com/svioletg/viMusBot/releases/latest) of this repository, look in the "Assets" section, and download "Source code" in either .zip or .tar.gz format; extract it wherever you like. Inside should be a "viMusBot" folder, which in turn contains all of the files you'll run the bot with.

2. Download both FFmpeg and FFprobe and drop them into the extracted folder - it should have `bot.py` and `spoofy.py` along with some others inside of it.
    - If you're on *Linux*, you likely already have these installed, otherwise `apt install ffmpeg` (or apt equivalent) will install both FFmpeg and FFprobe for you.
    - If you're on *Windows* you'll probably have to download these manually. Go to [ffmpeg.org](https://ffmpeg.org) and find the Windows builds, or click [here](https://github.com/BtbN/FFmpeg-Builds/releases/download/latest/ffmpeg-master-latest-win64-gpl.zip) for a direct download of BtbN's latest Windows build.
        - From this ZIP, go into the "bin" folder found inside and copy "ffmpeg.exe" and "ffprobe.exe" to the bot's folder.

3. Open a command prompt or terminal in your viMusBot folder, and run the command: `pip install -r requirements.txt`
    - If this does not work, try `python3 -m pip install -r requirements.txt`

4. Create the following new documents inside your folder:
    - `spotify_config.json`
    - `token.txt`

5. Copy-paste the "config_default.yml" file, and rename it to "config.yml".
    - It is recommend you keep the original in case you want to completely reset to default or check something.

From this point, skip to [Getting Your Credentials](#getting-your-credentials) to finish setting up.

---

### Using The Wizard

Go to the [latest release](https://github.com/svioletg/viMusBot/releases/latest), download the `vmb-wizard.py` file, and save it anywhere - the bot will not be setup in its directory, rather it will ask you where to download the files to.

>>>>>>> dev
Installing Python should have installed the Python Launcher for the version you have; assuming this is the case, you can simply double-click the file and it will open a console of its own.

Follow the instructions on screen. You may want to do the steps below for getting your credentials first, just to have them on hand. If you're using the wizard, you may ignore any instructions regarding creating files, as it will do this for you.

=======

---

1. Get the source files from the [latest release](https://github.com/svioletg/viMusBot/releases/latest), extract them where you want.
2. Create `spotify_config.json` and `token.txt`. Create an app with the Spotify Web API and enter your Client ID and Client Secret in the following format:
```
{
    "spotify":
    {
        "client_id": "YOUR_ID",
        "client_secret": "YOUR_SECRET"
    }
}
```
3. Ensure you've selected the right intents and permissions (see **Bot Token & Permissions** below), and paste your bot's token into `token.txt`.
4. Duplicate `config_default.yml` and rename the copy as `config.yml` - the bot will only use the latter for its options. Edit it how you like.
5. If FFmpeg and FFprobe aren't installed on your system, either install it through your package manager of choice or download the binaries and drop them in the viMusBot folder.
6. Open a command prompt or terminal in your viMusBot directory, and run `python3 bot.py`.

For a more in-depth tutorial, continue below.

---

There are two ways to start using the bot. If you're generally familiar with using the command prompt or terminal for your OS, follow the [**Standard Setup**](#standard-setup) section below. Alternatively, I've provided a script in this project to automatically obtain and walk you through most of the files and information you'll need; in which case, follow the [**Using The Wizard**](#using-the-wizard) section.

***Regardless of which section you follow***, you must first install the latest version of [Python](https://www.python.org/downloads/). Anything above Python 3.7 should in theory work, but its best to grab the latest one.

***If you are using the Windows installer***, when the installer starts you will see a "Add Python [your version] to PATH" checkbox near the bottom. Make sure that's ticked *on*, or else the `python3` command will not function, and you'll have to add it yourself before you can use any scripts provided here.

If you're installing on Linux, you should be able to run `apt install python3` and be set. Substitute `apt` if you're using a different package manager.

### Standard Setup

Ensure that the latest version of Python has been installed and added to your PATH.

1. Go to the [latest release](https://github.com/svioletg/viMusBot/releases/latest) of this repository, look in the "Assets" section, and download "Source code" in either .zip or .tar.gz format; extract it wherever you like. Inside should be a "viMusBot" folder, which in turn contains all of the files you'll run the bot with.

2. Download both FFmpeg and FFprobe and drop them into the extracted folder - it should have `bot.py` and `spoofy.py` along with some others inside of it.
    - If you're on *Linux*, you likely already have these installed, otherwise `apt install ffmpeg` (or apt equivalent) will install both FFmpeg and FFprobe for you.
    - If you're on *Windows* you'll probably have to download these manually. Go to [ffmpeg.org](https://ffmpeg.org) and find the Windows builds, or click [here](https://github.com/BtbN/FFmpeg-Builds/releases/download/latest/ffmpeg-master-latest-win64-gpl.zip) for a direct download of BtbN's latest Windows build.
        - From this ZIP, go into the "bin" folder found inside and copy "ffmpeg.exe" and "ffprobe.exe" to the bot's folder.

3. Open a command prompt or terminal in your viMusBot folder, and run the command: `pip install -r requirements.txt`
    - If this does not work, try `python3 -m pip install -r requirements.txt`

4. Create the following new documents inside your folder:
    - `spotify_config.json`
    - `token.txt`

5. Copy-paste the "config_default.yml" file, and rename it to "config.yml".
    - It is recommend you keep the original in case you want to completely reset to default or check something.

From this point, skip to [Getting Your Credentials](#getting-your-credentials) to finish setting up.

---

### Using The Wizard

Go to the [latest release](https://github.com/svioletg/viMusBot/releases/latest), download the `vmb-wizard.py` file, and save it anywhere - the bot will not be setup in its directory, rather it will ask you where to download the files to.

Installing Python should have installed the Python Launcher for the version you have; assuming this is the case, you can simply double-click the file and it will open a console of its own.

Follow the instructions on screen. You may want to do the steps below for getting your credentials first, just to have them on hand. If you're using the wizard, you may ignore any instructions regarding creating files, as it will do this for you.

>>>>>>> dev
Once the setup has finished, the bot will be ready to use in the directory you selected, and you only need to double-click the `bot.py` file to start it.

Setup will have created a `config.yml` file for you - the default settings should be fine in most cases, but I do suggest you look through it just in case you'd like to change some things. You can edit this file in any text editor, although something like Notepad++ will make it a little easier to navigate.

> *NOTE: If the bot detects any new changes in the default config file, after updating for example, it will merge your settings with the new options. This will remove things like comments and extra formatting, so it is reocmmended to keep `config_default.yml` to refer back to if you need help on what a particular option does.*

---

### Getting Your Credentials

This bot will require some information in order for the Spotify API features to function, along with a token for bot to run on Discord. The latter will be covered first.

### Bot Token & Permissions

1. Go to https://discord.com/developers/applications and log in.
2. Click the blue "New Application" button in the top right. Enter any name you want, and create the app. You should then be taken to a new dashboard for it.
3. From the left side menu, go to the "Bot" tab, and then select "Add Bot" on the right. Set its username to whatever you want it to display as, and select an icon if you wish. This is not required, and if no icon is selected, it will simply display as a default Discord icon.
4. Click "Reset Token", and then when you see a token appear, click "Copy". **If you're using the setup wizard, skip to step 5 here.** Open up `token.txt` and paste this string into it, and save the file. Unless you reset your token again, you will not need to change this in the future.
    - Note: Whether to leave the "Public Bot" toggle on or off is up to you. If it's off, only you will ever be able to invite it to servers. Otherwise, anyone with an invite link may do so.
5. Scroll down to **Privileged Gateway Intents**, and turn *on* the **Server Members Intent** and **Message Content Intent** switches, seen below.
![intent switches](https://cdn.discordapp.com/attachments/327195739346173962/1058205536769806376/image.png)
6. Go to **Bot Permissions** below this, and enable the following:
![bot permissions](https://cdn.discordapp.com/attachments/327195739346173962/1039979708219129966/image.png)
7. Make sure these settings are saved, and you're now done with this section. To generate an invite link, go to "OAuth2" on the left side menu, then select "URL Generator". Tick the "bot" box in **Scopes**, and then enable the same permissions you did above.

### Spotify API

In order for the bot to use the Spotify Web API and look up track, album, and playlist info - which is used to then find a YouTube equivalent match so that Spotify links may be used to queue songs - we need to authenticate to it with a client ID and secret, which we'll acquire now.

1. Go to your [Developer Dashboard](https://developer.spotify.com/dashboard/applications) and log in with your Spotify account.
2. Select "Create An App", enter a title and description (doesn't matter what, neither will be used or seen by the bot), and click "Show Client Secret" when taken to the app's overview page.

![spotify secret button](https://cdn.discordapp.com/attachments/327195739346173962/1058207796497219595/image.png)

3. **If you're using the setup wizard, it will ask you for this information.** Otherwise, create `spotify_config.json` in your bot's folder, and paste in the following text...
```
{
    "spotify":
    {
        "client_id": "YOUR_ID",
        "client_secret": "YOUR_SECRET"
    }
}
```
...and replace `YOUR_ID` with the string seen next to "Client ID", and `YOUR_SECRET` with the string seen next to "Client Secret". Make sure they are both surrounded by quotation marks like above.

---

With all the above done, you should be ready to go! If you have any questions or need clarification, feel free to ask by submitting a new issue.