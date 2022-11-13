# viMusBot

### Changelog is now located [here](https://github.com/svioletg/viMusBot/blob/master/changelog.md)

---

## TODO

- [developer] Bundle reaction choices into some sort of function(s) for quicker use
- [feature] Have the `-todo` and `-changelog` commands grab contents from this repository's corresponding markdown files
- [feature] Add command to skip to specified item in queue
---

A bot made in Python 3.10 using the [discord.py](https://github.com/Rapptz/discord.py) library, for personal usage.

Please submit an [issue](https://github.com/svioletg/viMusBot/issues/new) if you've experienced a bug or otherwise odd behavior, or have a feature to request, and feel free to comment on existing issues to provide any additional details that may help narrow down the issue or reach a solution. No bug or feature is too large/small to be submitted, this system is best for me to keep track of everything.

## Usage

I must stress that I'm a hobbyist programmer first and foremost, and this is far from a perfect project - there's probably better options, my coding is fairly messy, etc.; that being aside, feel free to run it yourself, fork the project, or even contribute! While I certainly won't have all the answers, please feel free to submit an issue if you're having trouble using anything.

To run this yourself you'll need:
- Python 3.10
- Required Python packages (run `pip install -r requirements.txt`)
- `ffmpeg` & `ffprobe` installed & added to your PATH
    - If you installed this through linux using `apt-get` or anything similar, you're probably good to go - you can double-check by simply running `ffmpeg` and `ffprobe` in your command prompt or terminal and seeing whether it recognizes the command.
- A `token.txt` file containing your Discord bot's token
- A `spotify_config.json` file for your Spotify API credentials
- A `headers_auth.json` file for ytmusicapi; see [here](https://ytmusicapi.readthedocs.io/en/latest/setup.html) for how to create it

The bot will require at least these permissions:

![Required Bot Permissions](https://cdn.discordapp.com/attachments/327195739346173962/1039979708219129966/image.png)

You can download the repository as a ZIP file directly from the repository page and you'll be set, but I would recommend installing `git` for easier updating:

1. Running `git clone https://github.com/svioletg/viMusBot.git` will create a `viMusBot` folder within wherever the command was run, there's no need to create a folder for it in advance.
2. Once cloned you'll have the files necessary to run the bot, excluding the `token.txt`, `spotify_config.json`, and `headers_auth.json` files, which you'll need to create yourself.
3. With Python 3.10 installed, run `pip --version` and ensure that it reads "(python 3.10)" at the end so that everything installs to the right version.
4. In a command prompt or terminal, enter the viMusBot directory and run `pip install -r requirements.txt`. This should install all of the required packages.
5. Use `python3 bot.py public` to start it, and everything should be good to go. `public` ensures that it will use `token.txt` and not `devtoken.txt` (this file is not required for general use).
    **Note:** You can also type "public" into `default_args.txt`, which will automatically add itself to the list of arguments when you run `bot.py`.

In order to update your files you can simply use `git pull` if you did `git clone`, or just download the ZIP again and replace your files. You can also run `python3 bot.py help` to get a list of options for running the script - doing this will *not* start the bot.