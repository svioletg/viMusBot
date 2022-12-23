# viMusBot

### Changelog is now located [here](https://github.com/svioletg/viMusBot/blob/master/changelog.md)

---

A bot made in Python 3.10 using the [discord.py](https://github.com/Rapptz/discord.py) library, for personal usage. I wasn't happy enough with the options already available, so I decided to try my own take on it.

Please submit an [issue](https://github.com/svioletg/viMusBot/issues/new) if you've experienced a bug or otherwise odd behavior, or have a feature to request, and feel free to comment on existing issues to provide any additional details that may help narrow down the issue or reach a solution. No bug or feature is too large/small to be submitted, this system is best for me to keep track of everything.

## Usage

I must stress that I'm a hobbyist programmer first and foremost, and this is far from a perfect project - there's probably better options, my coding is fairly messy, etc.; that being aside, feel free to run it yourself, fork the project, or even contribute! While I certainly won't have all the answers, please feel free to submit an issue if you're having trouble using anything.

To run this yourself you'll need:
- A minimum of Python 3.7 (according to [vermin](https://pypi.org/project/vermin/)), but the latest version is recommended
    - If you're on Windows using the installer, make sure to check the "Add Python 3.x to PATH" box. Linux should do this automatically.
- Required Python packages (run `pip install -r requirements.txt`)
- `ffmpeg` & `ffprobe` installed & added to your PATH
    - If you installed this through linux using `apt-get` or anything similar, you're probably good to go - you can double-check by simply running `ffmpeg` and `ffprobe` in your command prompt or terminal and seeing whether it recognizes the command.
- A `token.txt` file containing your Discord bot's token
- A `spotify_config.json` file for your Spotify API credentials
- A `headers_auth.json` file for ytmusicapi; see [here](https://ytmusicapi.readthedocs.io/en/latest/setup.html) for how to create it

The bot will require at least these permissions:

![Required Bot Permissions](https://cdn.discordapp.com/attachments/327195739346173962/1039979708219129966/image.png)

You can download the repository as a ZIP file directly from the repository page and you'll be set, but I would recommend installing `git` for easier updating; use `apt-get install git` or equivalent on Linux, or [download it here](https://git-scm.com/download/win) for Windows.

1. Running `git clone https://github.com/svioletg/viMusBot.git` will create a `viMusBot` folder within wherever the command was run, there's no need to create a folder for it in advance.
2. Once cloned you'll have the files necessary to run the bot, excluding the `token.txt`, `spotify_config.json`, and `headers_auth.json` files, which you'll need to create yourself.
3. With Python installed, run `pip --version` and ensure that it reads "(python 3.7)" or above at the end so that everything installs to the right version.
4. In a command prompt or terminal, enter the viMusBot directory and run `pip install -r requirements.txt`. This should install all of the required packages.
5. Rename or copy `config_example.yml` to `config.yml`, and change any options you'd like. The default settings should be about right for most cases.
6. Use `python3 bot.py` to start it up, and everything should be good to go.

Use `git pull` to update your files if you ran `git clone`, otherwise download the ZIP again and overwrite your files.