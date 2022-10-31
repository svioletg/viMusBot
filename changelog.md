# Changelog

### See [here](#versioning-info) for an explanation on categories and how versioning works for this project.

## 1.3.5
> *2022.10.31*

### Developer
- Created `bot_stable.py` and `spoofy_stable.py`, which are the last-pushed versions of `bot.py` and `spoofy.py` respectively, to keep the bot running without interruptions from development. `bot.py` and `spoofy.py` will use a different token meant for development use, and are copied over to the "stable" files once ready to commit. These files are not included in the repository, as they would just be duplicates.
- Defining `bot` has been moved to the bottom of `bot.py`, to keep all of the related sections closer together

### Improvements
- Changed `-queue` to allow specifying a page (a group of 10 queue items), instead of just now being able to see anything past #10
- New help command implemented with the [discord-pretty-help](https://github.com/stroupbslayen/discord-pretty-help) library

### Other
- Added the `-changelog` command, which sends a link to changelog.md and displays the most recent version
- Using `-queue` when the player queue is empty now sends its own message.

## 1.3.4
> *2022.10.30*

### Developer
- `colorama` is now being used for better readability in logs
- `log()` in both `bot.py` and `spoofy.py` will now log the elapsed time between calls of itself

### Fixes
- Fixed the YouTube search prompt not deleting itself if cancelled with an ❌ reaction
- `force_no_match` in `spoofy.py` works again, [was removed in 1.3.0 after re-writing the match-finding code](https://github.com/svioletg/viMusBot/blob/1b8b3caee4aaf6ad65733b34963b16069a3bb5c6/spoofy.py#L80) and I had forgot to write it back in; a new `match_found()` function has been added to check both the `match` variable and whether `force_no_match` is active

### Improvements
- Playlists now queue *much* faster, due to using youtube-dl's `extract_flat` option
- Extracting titles from YouTube videos is faster, now using the `pytube` library

### Other
- Queued items must now be less than 5 hours in duration
- When building YouTube results message (after `unsure` has been returned from `spoofy.spyt()`), the bot will no longer check every video's availability before adding it to the list of options, speeding up the process significantly; it will still check for availability when queueing the video, however

## 1.3.3
> *2022.10.29*

### Fixes
- Fixed broken Spotify queueing; `if` statement at [`spoofy.py`:224](https://github.com/svioletg/viMusBot/blob/1141ce31113920ecdf2591d65f58e5780d9b273d/spoofy.py#L224) was written incorrectly, and `valid` was used instead of `url` at [`bot.py`:348](https://github.com/svioletg/viMusBot/blob/1141ce31113920ecdf2591d65f58e5780d9b273d/bot.py#L348)

## 1.3.2
> *2022.10.28*

### Fixes
- Fixed Bandcamp albums, SoundCloud albums, and SoundCloud playlists not being queued properly (I believe this was also affecting YouTube playlists)

## 1.3.1
> *2022.10.28*

### Fixes
- Automatic file removal now includes .mp3 files

### Improvements
- Bot will remove old files from Youtube DL on startup

## 1.3.0
> *2022.10.28*

### Features
- Added support for YouTube & Spotify playlists, as well as Spotify albums

### Improvements
- Improved Spotify-YouTube song matching logic
- The bot now clears the queue after disconnecting via `-leave`

---

## Versioning Info

Versions are numbered as X.Y.Z, where:
- X is the **project version**, which should always remain at 1 unless the project is re-written almost entirely
- Y is the **major version**, for all-new functionality or other large changes
- Z is the **minor version**, for things like bugfixes or minor improvements to the code

## Categories

Each version will contain categories for its changes, which are:

#### Developer
Changes that are only applicable to developers, and that usually make diagnosing problems easier, like improving the logging system.

#### Features
All-new functionality not previously present in the project. This usually coincides with a new **major version**, for example [1.3.0](#130) with its implementation of playlist/album support.

#### Fixes
Fixed bugs or other unintended behavior.

#### Improvements
General improvements to the either the user or developer experience, like making a command simpler to use, reducing the amount of code needed for something, or otherwise making existing functionality more efficient.

#### Other
Any changes that do not directly fit into any other category. Usually this is something that could potentially go into "Improvements", but is more of a temporarily solution or workaround.

---

This changelog was started at 1.3.0, thus only versions then onwards appear. I've decided not to write changelogs for previous versions as to not risk forgetting anything.