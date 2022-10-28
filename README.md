# viMusBot

# Changelog

## 1.3.2

- Fixed Bandcamp albums, SoundCloud albums, and SoundCloud playlists not being queued properly (I believe this was also affecting YouTube playlists)

## 1.3.1

- Bot will remove old files from Youtube DL on startup
- Automatic file removal now includes .mp3 files

## 1.3.0

- Added support for YouTube & Spotify playlists, as well as Spotify albums
- Improved Spotify-YouTube song matching logic
- The bot now clears the queue after disconnecting via `-leave`

---

## TODO

- Support queueing Bandcamp/SoundCloud albums or playlists
- Find faster way to check URLs for errors (maybe threading?)
- Queueing playlists & albums takes longer than I'd like

---

A bot made in Python 3.10 using the [discord.py](https://github.com/Rapptz/discord.py) library, for personal usage.

Please submit an [issue](https://github.com/svioletg/viMusBot/issues/new) if you've experienced a bug or otherwise odd behavior, or have a feature to request, and feel free to comment on existing issues to provide any additional details that may help narrow down the issue or reach a solution. No bug or feature is too large/small to be submitted, this system is best for me to keep track of everything.

*I would not recommend using this code to learn Python, programming in general, or how to use discord.py efficiently*; by all means I hope it helps you, but I am by no means an expert and it is bound to be messy. 

You're free to use it for yourself, fork it, do whatever, but there's probably better options if you're just looking to host one - if you want something you can modify for your needs, I've tried to keep the code *relatively* clean and I'm only using two .py files here, but ease of public usage isn't exactly a priority at the moment.

To run this yourself you'll need Python 3.10 installed, the required Python packages (`pip install -r requirements.txt`), a `token.txt` file containing your bot's token, and a `config.json` file for your Spotify API credentials.