# Changelog

### See [here](#versioning-info) for an explanation on categories and how my versioning works for this project.

## 1.6.5
> *2022.12.24*

### Developer
- `bot.py` changes:
    - `player_queue` list replaced with the `MediaQueue` class
        - Separate queues are now stored per a guild's ID
        - *All* functions in `MediaQueue` require a discord.py `Context` object and will automatically determine the ID; creating a new queue if one does not exist
        - `.get(ctx)` must be called after every `player_queue` to affect the list, with the exception of `.clear(ctx)`
    - `queue_batch()` now requires a `Context` object as the first argument

### Features
- Aliases for commands can now be customized through the config ([#14](https://github.com/svioletg/viMusBot/issues/14))
- Commands can now be blacklisted/disabled through the config ([#15](https://github.com/svioletg/viMusBot/issues/15))

### Fixes
- Fixed a minor issue with the `-nowplaying` command returning what last played despite nothing currently playing

### Notes
The switch to using a `MediaQueue` class with separated queues for guilds was meant as a solution to [Issue #17](https://github.com/svioletg/viMusBot/issues/17), however that issue became much larger in scope than I had thought.

As such, I'm keeping these changes as a head start on that since they don't seem to negatively effect functionality, while I will deal with fixing the larger issue in its entirety later down the line.

## 1.6.4
> *2022.12.23*

### Features
- The bot will now send any errors it encounters as chat messages

### Other
- As a workaround to [Issue #16](https://github.com/svioletg/viMusBot/issues/16), a small note is now added as a subtitle to the "Trying to queue..." message regarding SoundCloud links sometimes returning a 403 Forbidden error

## 1.6.3
> *2022.12.21*

### Developer
- Various changes to code formatting for readability
    - Imports are now alphabetical, and imports of local files are separated
    - Especially long lines of code have been split into multiple lines
- `bot.py` changes:
    - `playnext()` renamed to `play_url()`
    - `next_in_queue()` renamed to `advance_queue()`
    - `queue_multiple()` renamed to `queue_batch()`
    - The `-join` command just calls `ensure_voice()` instead of having a duplicate of the joining code, for consistency

### Features
- Added a `-loop` command ([Issue #12](https://github.com/svioletg/viMusBot/issues/12))

### Other
- The bot will now assume the first result from a Japanese title search is correct, and will queue it (see [Issue #11](https://github.com/svioletg/viMusBot/issues/11) for details)
- The following packages are now needed, and have been added to `requirements.txt`:
    - `regex` version 2022.10.31

### Notes
I've gone back and added some notes or corrections to older versions' changelogs. Initially I was considering just removing the incorrect text, but I've decided to leave it there and strike it out, adding an explanation below.

## 1.6.2
> *2022.12.16*

### Developer
- `strip_color()` added to the `Palette` class, removes all color formatting from a string
    - As a result, `log()` only needs one version of `logstring` to work off of
- Version number is now stored in `version.txt` instead of in `bot.py`, both in case any file needs to reference it, and so the bot could potentially check for updates in the future
- Config file is now validated after importing all non-local libraries and before importing local files, so that it only has to be validated once and not per each file
    - These messages are printed instead of being logged, as a result

### Features
- Implemented [Issue #9](https://github.com/svioletg/viMusBot/issues/9): Detect whether the config template has changed on startup & merge with existing accordingly
    - Local `config.yml` will be updated with any new options present in the most recent `config_default.yml`, and pre-existing options' values will be preserved along with them
- `duration-limit` (number) added to the config
    - Stops videos/tracks over X hours from being downloaded and queued
- `inactivity-timeout` (number) added to the config
    - Disconnects the bot from voice if nothing has been playing for X minutes
    - Set to 0 to disable this and have the bot stay until manually disconnected

### Fixes
- Fixed [Issue #6](https://github.com/svioletg/viMusBot/issues/6): Bot does not disconnect after set timeout
- Fixed [Issue #10](https://github.com/svioletg/viMusBot/issues/10): "join" command does not function if the bot has not previously been in a voice channel
- The `voice` variable now properly resets after leaving a voice channel

## 1.6.1
> *2022.12.09*

### Developer
- Video duration is now checked *after* checking its availability
    - The result of `ytdl.extract_info()` is now stored in a variable to avoid waiting for it each time

### Features
- `use-top-match` (boolean) added to the config
    - Automatically queues the top result of a Spotify-YouTube match, regardless of how close the match is
- Starting the bot will now notify you if you're missing config options, and will exit
    - `config_default.yml` will be downloaded if it does not exist in the directory

### Fixes
- Fixed [Issue #7](https://github.com/svioletg/viMusBot/issues/7): Queue stalls until -skip is called when a Spotify choice prompt is timed out
- Fixed force_no_match not functioning

### Improvements
- Old "Now playing" messages now automatically delete themselves
- Log messages marked as a warning or an error will now output regardless of function blacklist

### Notes
I had intended to include more in this update, but I've been sick and too low on energy to work on the more complicated stuff, so I'm at least getting these live for now.

In the future, your config file will be automatically merged & updated with the latest config_default.yml; this current method of warning the user is just do mitigate issues until that's set in place.

## 1.6.0
> *2022.11.29*

### Remember to replace your INI file with the new YAML template!

### Developer
- The `log()` function in `bot.py` and `spoofy.py` has been moved to `newlog()` in `customlog.py`, so the log template and other aspects can be edited without needing to copy-paste between files
- `log()` still exists in the other files, now as a wrapper for `customlog.newlog()` so that you can still call it with only a message

### Features
- `bot.py` and `spoofy.py` will now write to `vimusbot.log` in addition to printing to console
    - When the bot is stopped and started, this is copied to `vimusbot-old.log`
- Various new options added/renamed in config
    - Inlucing an option to specify which functions you'd like to blacklist log messages from - note that this only affects what's printed to the console, it will still be written to `vimusbot.log`
- `test()` added to `palette.py` to display every currently set color
    - This can be seen by running `python3 palette.py --show`

### Improvements
- Spotify URLs will now be queued directly, and matching will be done once its turn in the queue has been reached
    - Subsequently, queueing Spotify playlists has become *significantly* faster, and should no longer cause major problems
- Config files now use YAML instead of INI
- If an ISRC match succeeds, data will be obtained with pytube, which is slightly faster than ytmusicapi

### Notes
I've stopped including the commit link so that each update doesn't require two separate commits for it. You can find a version's latest commit by searching through all of them and finding the last commit before one with a new version number.

## 1.5.4
> *2022.11.22* / *[view commit](https://github.com/svioletg/viMusBot/commit/96ad0dd19870b0462293c2e6a458922730a5a01d)*

### Other
- Added an option to limit how long Spotify playlists can be for queueing (40 by default, see notes)
- Split `print_logs` into `print_bot_logs` and `print_spoofy_logs`
- When queueing a Spotify playlist, the bot will list what tracks it could not find a match for

### Notes
It was discovered that queueing a Spotify playlist longer than roughly 40 tracks will lock up the bot, due to the voice client returning as not connected despite it still being so. I can't seem to locate the root cause of this problem, so for now a limit has been added to circumvent this.

This would likely be fixed by having a faster method of queueing up Spotify tracks, but with pyspotify not functioning these days, it's going to be a long time until I find a solution.

## 1.5.3
> *2022.11.18* / *[view commit](https://github.com/svioletg/viMusBot/commit/9185f52120ca5738c8a821fb6e360d56ab7a894f)*

### Improvements
- Spotify-YouTube song matching will now try to match the ISRC code ~~(or UPC for albums)~~ first before falling back on the text search method, this is slightly faster and usually more accurate
    - CORRECTION: UPC searching support was *not* added into 1.5.3. Although that was the intention, I had forgotten to add it to the update - and later discovered that searching by UPC doesn't work at all, regardless.

### Other
- Command-line arguments are no longer supported, instead `config.ini` has been added with the same options; this effectively replaces `default_args.txt` as well
- Playlist support has been re-added, but it turned off by default; set `allow_spotify_playlists` in the config to enable it
    - **Note:** This is still very slow, as it takes around 1-2 seconds per track, which can build up very fast on large playlists. I am searching for a way to speed up the process, but it will likely be a while

## 1.5.2
> *2022.11.12* / *[view commit](https://github.com/svioletg/viMusBot/commit/91c7109a77c8700a72d3e8b9c3ed334bbb039d88)*

### Developer
- `default_args.txt` created, entering a list of arguments into this file will automatically add them to the command anytime you run the bot; use the `nodefault` argument to ignore this file
    - **Note:** Use `bot.py help` for a list of valid arguments. Arguments must be entered in one line, separated by commas. For example, if the content of `default_args.txt` is `public, quiet, fnm`, the bot will start as if you ran `bot.py public quiet fnm`. The `help` argument will be ignored if added to this file.
- Changes in `bot.py`:
    - Created `prompt_for_choice()` for easier creation of selection prompt messages; prompt message must be built beforehand
    - `urltitle()` renamed to `title_from_url()`
    - `on_command_error()` will now log the full traceback, which can be disabled by passing the `notrace` command-line argument
- Changes in `spoofy.py`:
    - In `is_matching()`, the `title`, `artist`, and `album` variables were replaced with `ref_title` and so on; matching `yt_title` etc. variables were created as shortcuts to `ytresult`'s keys
    - Fuzzy matching was implemented, and can be turned off by passing `mode='old'` to `is_matching()`
    - `is_matching()` takes new optional arguments for determing the threshold of fuzzy matching; `threshold` sets one threshold for title, artist, and album, or you can specify `title_threshold` etc.

## 1.5.1
> *2022.11.11* / *[view commit](https://github.com/svioletg/viMusBot/commit/a92909b4047fbbb9e91a85d4c3001af40e1dbe06)*

### Fixes
- Fixed broken SoundCloud link queueing

## 1.5.0
> *2022.11.10* / *[view commit](https://github.com/svioletg/viMusBot/commit/e2f0e17618eb00427b2263e189b72c556235f582)*

### Developer
- Added the `help` command-line argument
- The embed for `-analyze` is now built inside `bot.py`, removing the need for `spoofy.py` to import the discord library
- `queue_objects_from_list()` renamed to `generate_QueueItems()`
- `queue_batch()` renamed to `queue_multiple()`
- `config.json` renamed to `spotify_config.json`
- Changes in `spoofy.py`:
    - `match` is now directly used when returning `search_ytmusic()`, instead of indexing `search_out`
    - `search_out` replaced by two separate variables instead of overwriting itself; `song_results` and `video_results`
    - `reference` in must now be a dictionary
    - `track_info()` renamed to `spotify_track()`
    - `playlist_info()` removed
    - `spotify_album()` created
    - `soundcloud_playlist()` created
- Library/requirement changes:
    - `soundcloud-api` is now required (see [here](https://github.com/3jackdaws/soundcloud-lib))
    - `fuzzywuzzy` is now required
    - `python-Levenshtein` is now required

### Fixes
- Fixed `-move` not printing the right video title
- Fixed SoundCloud playlists not working because of a missing 'title' key - the title will be approximated from the URL
- Fixed SoundCloud playlist items past #5 not queueing correctly; youtube-dl's info extractor fails to get proper metadata past 5 tracks and only returns an API URL, so [this library by 3jackdraws](https://github.com/3jackdaws/soundcloud-lib) is being used
- Fixed Spotify albums not queueing correctly

### Features
- Added `-shuffle` to randomize the queue

### Improvements
- Spotify albums will queue faster

### Other
- If the bot is unsure about a Spotify-YouTube match, instead of giving 5 user-uploaded results, it will provide the top 2 song results and top 2 video results
- Spotify playlist support has been removed until a faster solution is found

## 1.4.0
> *2022.11.05* / *[view commit](https://github.com/svioletg/viMusBot/commit/d71fc727627f0f785f4538fea30d9c377a29c92c)*

### Developer
- `print_logs` can be set to false by passing "quiet" as a command-line argument
- `palette.py` created with the `Palette` class, which will help keep log message styling consistent
- The `log()` function in both files will now retrieve the name of the function it was called from, and add it to the message
 - `log()` should now be identical across each file, as everything is retrieved automatically
- The following apply to `spoofy.py`:
    - `remix_check` and related variables have been renamed to `alternate_check`, as they are now used for multiple different terms
    - `searchYT()` renamed to `search_ytmusic()` for consistency
    - `search_ytmusic()` now requires `title`, `artist`, and `album` as positional arguments
    - `is_matching()` is now defined outside of `search_ytmusic()`, and now requires the `reference` argument (a *list* containing the title, artist, and album originally obtained from the Spotify data)
    - The `item` argument in `is_matching()` has been renamed to `ytresult` for clarity

### Features
- `-play` now can work with a search query instead of a link, and will give the user a choice between the top song and top user-uploaded video found (if they're the same video, it automatically queues)

### Fixes
- Generic extractor bug thought to be fixed in 1.3.7 should now be *properly* fixed, the `subprocess.check_output()` function wasn't working when a string was passed and needed a list to work correctly; I hadn't tested it thoroughly enough

### Improvements
- Spotify/YouTube matching logic: The first YouTube search checks for a matching album instead of a matching artist, checking the artist was causing problems when the artist name on YouTube Music was not the same as on Spotify

## 1.3.7
> *2022.11.05* / *[view commit](https://github.com/svioletg/viMusBot/commit/530cda2d9cd53d244a2801d556e12028847a873e)*

### Developer
- `debug` has been renamed to `print_logs` to be more accurate

### Fixes
- Errors should now be caught automatically, and the bot will now actually use `discord.log` as intended
- ~~Links that use the [generic] youtube-dl extractor (like direct links to files) now queue correctly, they were failing at the duration check the generic extractor does not retrieve the length of the file~~
    - CORRECTION: This bug still ended up present in this version, and was later properly fixed in version [1.4.0](#140).
- Downloaded files will delete themselves correctly after finishing or being skipped

### Improvements
- Spotify/YouTube matching logic: Checking for remixes will now include covers

## 1.3.6
> *2022.11.04* / *[view commit](https://github.com/svioletg/viMusBot/commit/09d6597a1fd80abb32a939e76bf3bef0b15b5e8c)*

### Developer
- Moved `force_no_match` further up in `spoofy.py`'s code so that it warns the user at startup
- Dev mode can now be turned off by adding "public" as a command-line argument, and thus the files no longer need to be directly edited for this.
- `force_no_match` is now set from the command line by passing the "fnm" argument.
- Logging functions in `spoofy.py` have been moved to the top of the file
- Removed a few `print()` commands added for testing and weren't removed before commit

### Improvements
- Bot will now leave voice after 10 minutes of inactivity.

### Fixes
- The `-remove` was added long ago but never worked due to an oversight on my end, it works properly now

## 1.3.5
> *2022.10.31* / *[view commit](https://github.com/svioletg/viMusBot/commit/3b52e4fbbe48f663893b3613c98c53faedb388dc)*

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
> *2022.10.30* / *[view commit](https://github.com/svioletg/viMusBot/commit/85b5edc141a66416416633812f80326c19783215)*

### Developer
- `colorama` is now being used for better readability in logs
- `log()` in both `bot.py` and `spoofy.py` will now log the elapsed time between calls of itself

### Fixes
- Fixed the YouTube search prompt not deleting itself if cancelled with an ??? reaction
- `force_no_match` in `spoofy.py` works again, [was removed in 1.3.0 after re-writing the match-finding code](https://github.com/svioletg/viMusBot/blob/1b8b3caee4aaf6ad65733b34963b16069a3bb5c6/spoofy.py#L80) and I had forgot to write it back in; a new `match_found()` function has been added to check both the `match` variable and whether `force_no_match` is active

### Improvements
- Playlists now queue *much* faster, due to using youtube-dl's `extract_flat` option
- Extracting titles from YouTube videos is faster, now using the `pytube` library

### Other
- Queued items must now be less than 5 hours in duration
- When building YouTube results message (after `unsure` has been returned from `spoofy.spyt()`), the bot will no longer check every video's availability before adding it to the list of options, speeding up the process significantly; it will still check for availability when queueing the video, however

## 1.3.3
> *2022.10.29* / *[view commit](https://github.com/svioletg/viMusBot/commit/02d4ba3e45bebb97115f3ede7e1377482ca92931)*

### Fixes
- Fixed broken Spotify queueing; `if` statement at [`spoofy.py`:224](https://github.com/svioletg/viMusBot/blob/1141ce31113920ecdf2591d65f58e5780d9b273d/spoofy.py#L224) was written incorrectly, and `valid` was used instead of `url` at [`bot.py`:348](https://github.com/svioletg/viMusBot/blob/1141ce31113920ecdf2591d65f58e5780d9b273d/bot.py#L348)

## 1.3.2
> *2022.10.28* / *[view commit](https://github.com/svioletg/viMusBot/commit/1141ce31113920ecdf2591d65f58e5780d9b273d)*

### Fixes
- Fixed Bandcamp albums, SoundCloud albums, and SoundCloud playlists not being queued properly (I believe this was also affecting YouTube playlists)

## 1.3.1
> *2022.10.28* / *[view commit](https://github.com/svioletg/viMusBot/commit/08ba730fafb1165de2d6fb82752c71d0ac70dd2d)*

### Fixes
- Automatic file removal now includes .mp3 files

### Improvements
- Bot will remove old files from Youtube DL on startup

## 1.3.0
> *2022.10.28* / *[view commit](https://github.com/svioletg/viMusBot/commit/1b8b3caee4aaf6ad65733b34963b16069a3bb5c6)*

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

Version numbers do *not* roll over into the next highest spot, e.g if the last update was `1.0.9`, the next update would not be `1.1.0` - it would be labelled as `1.0.10`.

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
Any changes that do not directly fit into any other category. Usually this is something that could potentially go into "Improvements", but is more of a temporary solution or workaround.

#### Notes
Usually unused, any additional notes regarding the release. Listed last, out of alphabetical order.

---

This changelog was started at 1.3.0, thus only versions then onwards appear. I've decided not to write changelogs for previous versions as to not risk forgetting anything.