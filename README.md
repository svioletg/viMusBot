# viMusBot

### Changelog is now located [here](https://github.com/svioletg/viMusBot/blob/master/changelog.md)

---

## TODO

- Have the bot leave after X minutes of inactivity
- Add current timestamp to `-nowplaying` command
- Add command to skip to specified item in queue

---

A bot made in Python 3.10 using the [discord.py](https://github.com/Rapptz/discord.py) library, for personal usage.

Please submit an [issue](https://github.com/svioletg/viMusBot/issues/new) if you've experienced a bug or otherwise odd behavior, or have a feature to request, and feel free to comment on existing issues to provide any additional details that may help narrow down the issue or reach a solution. No bug or feature is too large/small to be submitted, this system is best for me to keep track of everything.

## Running The Bot

I must stress that I'm a hobbyist programmer first and foremost, and this is far from a perfect project - there's probably better options, my coding is fairly messy, etc.; that being aside, feel free to run it yourself, fork the project, or even contribute! While I certainly won't have all the answers, please feel free to submit an issue if you're having trouble running the bot!

To run this yourself you'll need:
- Python 3.10\*
- Required Python packages (run `pip install -r requirements.txt`)
- `ffmpeg` installed
 - If you're running Windows, I'd recommend you add FFmpeg to your PATH.
 - If you've installed it on Linux through `apt install ffmpeg`, you're likely good to go.
- A `token.txt` file containing your bot's token
- A `config.json` file for your Spotify API credentials
- A `headers_auth.json` file for ytmusicapi; see [here](https://ytmusicapi.readthedocs.io/en/latest/setup.html) for more details

\**I've been running it off of Python 3.10, so this is mostly just a precautionary measure - it might work with lower versions, I would recommend upgrading regardless.*

**Note:** I try to remember to do this myself before I push commits, but just incase -  before you run the bot make sure `dev` is set to **false** in `bot.py`, and `force_no_match` is set to **false** in `spoofy.py`. If you don't know how to do this, open the files and look near the top, there should be something like `dev=False` and `force_no_match=False`. If it says `True`, instead, simply replace it with `False` - and the capitlization *is* important.

If these are left on `True` then the bot won't start correctly as it would be looking for `devtoken.txt`, and `force_no_match` is for testing purposes - leaving it set to `True` would make it so automatic matching is disabled and you would always get a selection menu when queueing Spotify links.