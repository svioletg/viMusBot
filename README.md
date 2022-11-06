# viMusBot

### Changelog is now located [here](https://github.com/svioletg/viMusBot/blob/master/changelog.md)

---

## TODO

- [improvement] Find a way to build the discord.py embed in `spoofy.py` without importing `discord`
- [feature] Have the `-todo` and `-changelog` commands grab contents from this repository's corresponding markdown files
- [feature] Add command to skip to specified item in queue
- [feature] Add current timestamp to `-nowplaying` command

---

A bot made in Python 3.10 using the [discord.py](https://github.com/Rapptz/discord.py) library, for personal usage.

Please submit an [issue](https://github.com/svioletg/viMusBot/issues/new) if you've experienced a bug or otherwise odd behavior, or have a feature to request, and feel free to comment on existing issues to provide any additional details that may help narrow down the issue or reach a solution. No bug or feature is too large/small to be submitted, this system is best for me to keep track of everything.

## Running The Bot

I must stress that I'm a hobbyist programmer first and foremost, and this is far from a perfect project - there's probably better options, my coding is fairly messy, etc.; that being aside, feel free to run it yourself, fork the project, or even contribute! While I certainly won't have all the answers, please feel free to submit an issue if you're having trouble running the bot!

To run this yourself you'll need:
- Python 3.10\*
- Required Python packages (run `pip install -r requirements.txt`)
- `ffmpeg` & `ffprobe` installed
 - If you're running Windows, I'd recommend you add these to your PATH.
 - Running `apt install ffmpeg` (or whatever your distro's equivalent manager is) should install both for you, as well as adding them to the system's PATH.
- A `token.txt` file containing your bot's token
- A `config.json` file for your Spotify API credentials
- A `headers_auth.json` file for ytmusicapi; see [here](https://ytmusicapi.readthedocs.io/en/latest/setup.html) for more details

\**I've been running it off of Python 3.10, so this is mostly just a precautionary measure - it might work with lower versions, I would recommend upgrading regardless.*

**Note:** When running the bot for general use, make sure to pass "public" as a command-line argument. e.g `python3 bot.py public`