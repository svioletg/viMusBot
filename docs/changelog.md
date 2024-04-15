# viMusBot

## Changelog

---

## 1.9.0

> *2024.04.xx / dev.33*

### Developer
- Improved some error handling and logic for text searching in both `bot.py` and `spoofy.py`
- Added type annotations to most functions and their parameters, as well as a few variables where it felt needed
- `bot.py`
    - The `test_play()` function has been added which will test some common queueing scenarios in succession
      - This does not comprehensively cover every single base for testing
      - It can be manually triggered by running `test play` in the new console
    - Most constants have been made uppercase
    - `generate_QueueItems()` has been renamed to `generate_from_list()` and is now a class method of the `QueueItem`
    - `player_queue` renamed to `media_queue`
    - `update_check` renamed to `update_check_result`
    - `play_url()` renamed to `play_item()`
    - `get_aliases()` renamed to `command_aliases()`
    - The `get_queued_by_text()` function has been created, replacing the f-string that `submitter_text` gets set to, now that there's extra logic required for whether to use nicknames
    - Code has been updated to be compatible with `discord-pretty-help` version 2.0.1 and above, as versions prior to 2.0.1 are unavailable through pip, rendering the bot unusable if you have no way of installing an older version
    - The "Command is not found" error is now properly caught and ignored, as having the bot send a message in this scenario is unnecessary
    - Startup file removal will now use `pathlib` to check extensions instead of regex
    - Calls to `os.path` replaced with `Path()`
    - Simplified `log_traceback()`
- `spoofy.py`
    - `pytube_track_data()` will not attempt to retry data retrieval anymore, as the core issue should be fixed (see **Fixes** below)
      - In the event that it still fails — as of writing, there's an issue with non-age-restricted videos raising an age restriction error that has not been fixed in a public release, for example — it will fall back on `yt_dlp`
    - `trim_track_data()` has had an argument renamed: `from_pytube` -> `is_pytube_object`
- `update.py`
    - `tkinter` is no longer imported, as it was only used for a test that was left in before release in error
    - `target_dir` variable removed, files can only be extracted into the directory `update.py` sits in

### Features
- `config_default.yml` will now be used as a fallback when keys are missing from `config.yml`, so that you only have to write in what you actually want to change into your config (and to avoid having to put in new config keys every time they're added by an update)
- Multiple URLs can be queued at once when using the `-play` command
    - Only multiple single-track URLs will work; multiple playlist/album URLs, or a mix of URLs and plain text terms, will be prevented from queueing
- `https://spotify.link` URLs are now supported ([Issue #57](https://github.com/svioletg/viMusBot/issues/57))
- A "console" now runs concurrently with the bot, allowing user input for basic commands into the command prompt or terminal; available commands can be found at [console.md](https://github.com/svioletg/viMusBot/blob/master/docs/console.md), newly added ones listed below
    - `stop`
        - Cancels the console & bot threads and quits out of the script
    - `test play <source> [valid] [multiple_urls] [playlist_or_album]`
        - **Only works when not running in "public" mode**, see your configuration file to change this
        - Uses
- Things like track titles and lengths are now cached for as long as the bot is running, avoiding duplicate requests and slightly speeding up queue times
    - Should the cache cause problems for you, you can clear it out with the new `-clearcache` command, or disable it entirely with the `use-url-cache` config key (see the **Other** section below)
- The sidebar color on bot messages can now be customized

### Fixes
- Too many to list individually, but lots of `-play`-related errors have been either fixed or at least properly caught and dealt with, thanks to the new tests
- The remaining queue time now factors in the remaining time of the currently playing track
- Trying to queue a private Spotify playlist will now give a proper message in response informing the user of such
- The `search_ytmusic_text()` function had a typo for a *very* long time that meant the top video result wasn't actually being checked; both the top song and top video results should now return correctly, and the user will be shown a prompt to decide which to queue (as was always intended to be the case)
- `customlog.py` did not actually ignore logs from the function names present in the `ignore-logs-from` config key due to an incorrectly typed expression, which has now been fixed
- `pytube` should now retrieve data correctly most of the time, `bypass_age_gate()` must be used to load in the description (as described in [pytube issue #1674](https://github.com/pytube/pytube/issues/1674))
- Fixed [Issue #4](https://github.com/svioletg/viMusBot/issues/4): "Queueing a track right as one is finishing or starting skips the next in queue"
- Fixed [Issue #41](https://github.com/svioletg/viMusBot/issues/41): "Looping does not function"

### Other
- Config changes:
    - `use-url-cache` (boolean) added; determines whether to cache information retrieved from URLs like titles and durations
    - `embed-color` (string) added; specifies the color of the sidebar on bot messages, must be a hex code (e.g "ff00ff")
    - `auto-update-config` removed; no longer used
- Changes in `requirements.txt`:
    - `python-benedict` is now required
    - `requests` is now required (to support [Issue #57](https://github.com/svioletg/viMusBot/issues/57))
    - `inquirer` is no longer required, it is only used for `vmb-wizard.py` which is now deprecated
- A few `.bat` scripts have been added to make initial setup and use of the bot easier
- `vmb-wizard.py` has been removed
- If one is set, the queue will now display the nicknames of users instead of account names
- The note added to queue messages regarding problems with SoundCloud ([Issue #16](https://github.com/svioletg/viMusBot/issues/16)) was removed as it hasn't caused problems recently, and was more likely an API issue on their end
- Current timestamp has been added to the bot's logs, to aid in future debugging

## 1.8.3
> *2023.04.29 / dev.32*

### Developer
- `length_from_url()` has been **renamed** to `duration_from_url()`
- The `length` attribute of `QueueItem` has been **renamed** to `duration`
- `duration_from_url()` and `title_from_url()` have been moved down to the `# Misc. helper functions` section of `bot.py`
- `play_url()` now requires a `QueueItem` object instead of a URL string (`url` argument replaced with `item`)
    - By extension, `play_url()` no longer requires the `user` argument
    - This was done to cut down on unnecessary and redundant operations, such as retrieving a track's duration when we've already got it in the `QueueItem` it originated from
    - As well, `play_url()` is now *only* invoked by the `advance_queue()` function, as `-play` will now append a new `QueueItem` to the queue before calling `advance_queue()` instead of using the URL
- The duration limit check now makes use of `duration_from_url()` to keep everything organized better
- The `extract_from_ytmusic` argument of `trim_track_data()` has been **renamed** to `extract_with_ytmusic`

### Fixes
- Fixed an issue that broke playing direct file links, which was causing a KeyError when retrieving the duration
- The workaround for `NoneType` errors relating to `pytube` has been amended to fall back on `yt-dlp` for data retrieval if all attempts fail

### Other
- Spotify-to-YouTube album matching should be much more reliable now, due to making a second pass through the "Songs" filter of YouTube Music

## 1.8.2
> *2023.04.19 / dev.31*

### Developer
- Added a `__name__ == '__main__'` check to `bot.py` so it can be imported for debug purposes without actually starting asyncio

### Features
- Using `-queue` will now display each item's times, as well as the total time of the entire queue
    - If a link's time can't be retrieved (this happens when queueing entire Bandcamp albums, for example), it won't appear and won't be counted as part of the total queue time
- The bot will edit its *"Spotify link detected, searching YouTube..."* message once a match has been found, so that progress is more visible

### Fixes
- Using `-leave` when the bot is not connected to a voice channel gives a proper message instead of an error
- Partially fixed an issue where some YouTube videos would randomly cause `NoneType`-related errors when retrieving data through pytube; this appears to be an issue on either pytube or YouTube's end, but for the time being my workaround will have pytube retry retrieving data up to 10 times, at which point it will give up and not queue the link
- Album matches should be slightly better, since it will strip out any "Remastered" text from titles
- Timestamps will now display properly if over an hour

## 1.8.1
> *2023.04.11 / dev.30*

### Developer
- Since [Issue #34](https://github.com/svioletg/viMusBot/issues/34) has been hard to reproduce, a try/except block has been added to where the error typically occurs, and will log some relevant data - that way, when it does occur, it should be easier to identify the problem
- The vote-skip check is now `>=` instead of `==`, to prevent any bugs with the number being higher than the threshold (say, if you set the exact vote number to 0, for some reason)

### Features
- `-nowplaying` and `-queue` will now show what user has queued which link (can be disabled, see "Config changes" below)
- Vote-to-skip threshold can now be set to a specific number of users, in addition to being a percentage
- Config changes:
    - Changes in the `vote-to-skip` section:
        - `threshold-type` (string) was added; can be set to "percentage" or "exact"
        - `threshold` has been **renamed** to `threshold-percentage`
        - `threshold-exact` (number) was added; determines the exact number of users needed to successfully skip
    - `show-users-in-queue` (boolean) was added
        - Toggles whether the name of who submitted what into the queue will be displayed with `-nowplaying` and `-queue`

### Fixes
- Fixed total time not displaying correctly when less than a minute (times would show as `:40` instead of `0:40`, for example)
- Fixed [Issue #35](https://github.com/svioletg/viMusBot/issues/35): "SoundCloud links completely broken (DownloadError [...] URL looks truncated.)"
> NOTE: This is unrelated to the 403 error that can happen with SoundCloud links. That issue unfortunately remains.
- Fixed [Issue #31](https://github.com/svioletg/viMusBot/issues/31): "TypeError: int() argument must be a string, a bytes-like object or a real number, not 'NoneType'" when playing some songs via text search; this was previously thought to be fixed in 1.8.0, however I made an oversight that rendered the fix useless
- Fixed an issue with `ytmusicapi` returning some videos with the `album` key set to `None`, instead of the key not existing (which was previously checked for)
- Spotify/YouTube matching should be slightly improved, the match detection will now ignore any sort of "(20xx Remaster)" information in the title that is missing from the other
- Using `-skip` will stop the currently playing song immediately, instead of waiting for the next song in queue to be downloaded

## 1.8.0
> *2023.04.07 / dev.29*

### Developer
- Various code improvements & edits
    - Almost every function should have types declared for their arguments, and a `->` operator to indicate its return type
    - Old, unused code entirely removed
    - Certain sections were changed to improve readability and clarity
- `bot.py`:
    - `public` no longer determines the token file, and is now only used to select which command prefix to use
    - `TODO` dictionary removed, hasn't been used for a long time
- `spoofy.py`:
    - `spotify_album()` now retrieves a year
    - `search_ytmusic_album()` now uses the release year for matching, will pass if at least 2 out of the title, artist, and year match

### Features
- Song length will now be displayed when using `-nowplaying`, as well as elapsed time
- Vote-to-skip has been added, and can be configured through `config.yml`
- Config changes:
    - `auto-remove` (list of strings) added to the config
        - Determines which file extensions to include in the on-startup file cleanup
        - Includes most common media formats by default

    > Note: Media files not in use by the bot are normally deleted once the queue advances, however some can by left behind occassionally; thus, on startup, the bot will remove any stray files like this

    - `token-file` (string; file name or path) added to the config
        - Specifies which file `bot.py` will check for the bot's token
        - `public` no longer determines this file
    - `logging-options/show-verbose-logs` (boolean) added to the config
        - If enabled, will stop certain logs from showing in the console window, ones that may be seen as clutter and are more useful for debugging (they are still logged to `vimusbot.log` regardless)
    - `vote-to-skip` section added to the config
        - `enabled` (boolean) added; toggles whether skipping will be done by vote or instantly
        - `threshold` (number) added; percentage of users connected to a voice channel needed to skip (only include the number, not the percentage sign - doing so will break the YAML)
    - `palette.py` now displays each available color on the same line, separated by a space

### Fixes
- Fixed [Issue #25](https://github.com/svioletg/viMusBot/issues/25): Bot thinks its outdated despite the version numbers matching
- Fixed YouTube links retrieved using pytube causing occassional errors, the bot will now fall back on the slower yt-dlp method instead of aborting
- `duration_limit` was being set incorrectly in `bot.py` and could interfere with the user-set limit, now grabs it from the config file like it should
- Fixed [Issue #28](https://github.com/svioletg/viMusBot/issues/28): "Not connected to voice" message is duplicated
- Fixed [Issue #30](https://github.com/svioletg/viMusBot/issues/30): "ValueError: too many values to unpack" for certain songs
- ~~Fixed [Issue #31](https://github.com/svioletg/viMusBot/issues/31): "TypeError: int() argument must be a string, a bytes-like object or a real number, not 'NoneType'" when playing some songs via text search~~
    - CORRECTION: Due to an oversight by me, this was not properly fixed. It was subsequently fixed in 1.8.1.

### Other
- `-todo` command removed
- `config.yml` will **no longer automatically update itself** with new keys from `config_default.yml` — see [this page in the new FAQ](https://github.com/svioletg/viMusBot/blob/master/faq.md#how-do-i-update-my-config) on manually updating

## 1.7.0
> *2023.01.13 / dev.28*

### Developer
- `bot.py` changes:
    - `-reload` command added that will re-import `spoofy.py` for quicker debugging and testing
        - This is disabled in the default config provided
    - No longer checks for availability before queueing since it was unnecessarily slowing things down, if a video is unavailable it'll just be skipped in the queue or throw an error beforehand
- `palette.py` no longer checks for a `--show` argument, instead will use `__name__` to detect if its being run as a script or not

### Features
- A new setup "wizard" has been created to aid the process of setting up the bot for the first time, for users less experienced with the command line
- The bot will now check for updates when being run; it can then be automatically updated by running `update.py`

### Fixes
- Removed a couple `print()` instances meant for debugging and accidentally left in the release
- Tracks with featured artists have different titles on Spotify and YouTube so the match would always fail, this is now fixed

## 1.6.5
> *2022.12.24 / dev.27*

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
> *2022.12.23 / dev.26*

### Features
- The bot will now send any errors it encounters as chat messages

### Other
- As a workaround to [Issue #16](https://github.com/svioletg/viMusBot/issues/16), a small note is now added as a subtitle to the "Trying to queue..." message regarding SoundCloud links sometimes returning a 403 Forbidden error

## 1.6.3
> *2022.12.21 / dev.25*

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
> *2022.12.16 / dev.24*

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
> *2022.12.09 / dev.23*

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
> *2022.11.29 / dev.22*

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
> *2022.11.22 / dev.21*

### Other
- Added an option to limit how long Spotify playlists can be for queueing (40 by default, see notes)
- Split `print_logs` into `print_bot_logs` and `print_spoofy_logs`
- When queueing a Spotify playlist, the bot will list what tracks it could not find a match for

### Notes
It was discovered that queueing a Spotify playlist longer than roughly 40 tracks will lock up the bot, due to the voice client returning as not connected despite it still being so. I can't seem to locate the root cause of this problem, so for now a limit has been added to circumvent this.

This would likely be fixed by having a faster method of queueing up Spotify tracks, but with pyspotify not functioning these days, it's going to be a long time until I find a solution.

## 1.5.3
> *2022.11.18 / dev.20*

### Improvements
- Spotify-YouTube song matching will now try to match the ISRC code ~~(or UPC for albums)~~ first before falling back on the text search method, this is slightly faster and usually more accurate
    - CORRECTION: UPC searching support was *not* added into 1.5.3. Although that was the intention, I had forgotten to add it to the update - and later discovered that searching by UPC doesn't work at all, regardless.

### Other
- Command-line arguments are no longer supported, instead `config.ini` has been added with the same options; this effectively replaces `default_args.txt` as well
- Playlist support has been re-added, but it turned off by default; set `allow_spotify_playlists` in the config to enable it
    - **Note:** This is still very slow, as it takes around 1-2 seconds per track, which can build up very fast on large playlists. I am searching for a way to speed up the process, but it will likely be a while

## 1.5.2
> *2022.11.12 / dev.19*

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
> *2022.11.11 / dev.18*

### Fixes
- Fixed broken SoundCloud link queueing

## 1.5.0
> *2022.11.10 / dev.17*

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
    - [+] `soundcloud-api` is now required (see [here](https://github.com/3jackdaws/soundcloud-lib))
    - [+] `fuzzywuzzy` is now required
    - [+] `python-Levenshtein` is now required

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
> *2022.11.05 / dev.16*

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
> *2022.11.05 / dev.15*

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
> *2022.11.04 / dev.14*

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
> *2022.10.31 / dev.13*

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
> *2022.10.30 / dev.12*

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
> *2022.10.29 / dev.11*

### Fixes
- Fixed broken Spotify queueing; `if` statement at [`spoofy.py`:224](https://github.com/svioletg/viMusBot/blob/1141ce31113920ecdf2591d65f58e5780d9b273d/spoofy.py#L224) was written incorrectly, and `valid` was used instead of `url` at [`bot.py`:348](https://github.com/svioletg/viMusBot/blob/1141ce31113920ecdf2591d65f58e5780d9b273d/bot.py#L348)

## 1.3.2
> *2022.10.28 / dev.10*

### Fixes
- Fixed Bandcamp albums, SoundCloud albums, and SoundCloud playlists not being queued properly (I believe this was also affecting YouTube playlists)

## 1.3.1
> *2022.10.28 / dev.9*

### Fixes
- Automatic file removal now includes .mp3 files

### Improvements
- Bot will remove old files from Youtube DL on startup

## 1.3.0
> *2022.10.28 / dev.8*

### Features
- Added support for YouTube & Spotify playlists, as well as Spotify albums

### Improvements
- Improved Spotify-YouTube song matching logic
- The bot now clears the queue after disconnecting via `-leave`

*The following versions were not originally released with a changelog, but are included for clarity's sake.*

## 1.2.2
> *2022.10.27 / dev.7*

## 1.2.1
> *2022.10.27 / dev.6*

## 1.2.0
> *2022.10.26 / dev.5*

## 1.1.2
> *2022.10.25 / dev.4*

## 1.1.1
> *2022.10.25 / dev.3*

## 1.1.0
> *2022.10.25 / dev.2*

## 1.0.0
> *2022.10.24 / dev.1*

---

## Versioning Info

### Public Release Versions
Versions are numbered as X.Y.Z, where:
- X is reserved for huge, fundamental structural changes to the code, and is almost never increased
- Y represents a "major version", typically coinciding with new features, or a very large number of bugfixes / internal improvements
- Z is the "minor version", usually just representing handfuls of bugfixes or small improvements/additions

### Hotfix Versions
Hotfixes are different from normal releases in that they *replace* their respective version's release instead of simply adding onto the list. This is normally done for security vulnerabilities, or for any issues in the original version that completely prevent usage of the bot. Hotfixes simply add a letter to the end of their version number, e.g 1.8.3's first hotfix was 1.8.3a, its second hotfix became 1.8.3b, and so on. If a hotfix is released, it is usually recommended to update right away.

### Development Versions
The `dev` branch is used for tracking work on new versions, and its code is never considered stable or suitable for general usage. When new versions are being worked on, a separate version system is used — in this case, a single incrementing number is used for each new version being worked on. Public release version numbers are usually decided right upon their release, and the scope of an update may change drastically, so one number is used instead of trying to predict the next public version number. `1.0.0` would have been `dev.1` although this system wasn't in place at that time, and `1.8.3` was `dev.32`, as an example. Since `dev.34` each new development version gets its own branch.

## Release Note Categories

Each release will contain categories for its changes, which are:

### Developer
Changes that are generally only relevant to developers; internal changes, performance improvements, renamed or moved symbols, etc.

### Features
All-new functionality not previously present in the project. This usually (but not always) coincides with a new **major version**, for example [1.3.0](#130) with its implementation of playlist/album support.

### Fixes
Bugs or other unintended behavior that have been fixed.

### Other
Any changes that do not directly fit into any other category.

### Notes
Usually unused, any additional notes regarding the release. Listed last, out of alphabetical order.

---

This changelog was started at 1.3.0, so versions prior do not have a proper changelog accompanying them. I've added their dates based off of commits.
