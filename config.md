# viMusBot

## Using `config.yml` for configuration & customization

Your viMusBot folder will come with a `config_default.yml` file, which contains various settings needed for the bot to run. Most of what is provided are simply user preferences — things like the bot's command prefix, the color of its embed sidebar, aliases for commands, and limiting the duration of what can be played.

If you want to change these settings, you must create a `config.yml` file (the bot will create this file while starting up if it does not exist) and override the values for what you want to change. Anything not present in `config.yml` will use the default provided by `config_default.yml`.

**It is important to not directly change the values of `config_default.yml`, as this file will be overwritten with each update.**

As an example, if you wanted to change the bot's prefix from the default `-` to `!`, you would write this into `config.yml`...

```yml
prefixes:
    public: "!"
```

...which will override the default value. When a setting is contained within another, like above, that's called **nesting**, and it is important to **indent** nested options just like they are presented in `config_default.yml`. When writing these, you can use `#` before text to write a **comment**, which will be ignored by the bot, and can be used as personal notes.

For a more complete example, your `config.yml` may look something like this:

```yml
embed-color: "0000ff" # blue
duration-limit: 2 # 2 hours
inactivity-timeout: 5 # 5 minutes
aliases:
    move:
        - "mv"
# comments can also be on their own separate lines, like this
vote-to-skip:
    enabled: true
    threshold-percentage: 50
    threshold-type: "percentage"
```

`config_default.yml` has comments for each value, but I've also compiled every setting and its type + valid values on this page, to provide more thorough information.

## Glossary — General Options

Written in alphabetical order. All information below should be accurate as of version **1.9.0**.

### `aliases`

> Alternate names that commands can be triggered with.

**Valid options:** any command name, with a nested list of alias strings within it

**Example:**

```yaml
aliases:
    move:
        - "m"
        - "mv"
```

### `allow-spotify-playlists`

> Allow or prevent the queueing of Spotify entire playlists.

**Valid options:** `true` or `false`

**Example:**

```yaml
allow-spotify-playlists: true
```

### `auto-remove`

> A list of file extensions to automatically delete files of, upon each startup of the bot. Media files are automatically removed after playing them, but occasionally if the bot if interrupted they can remain, so this is used to clean them up.

**Valid options:** a list of any file extensions, preceded with a period/dot

**Example:**

```yaml
auto-remove:
    - ".mp3"
    - ".webm"
```

### `command-blacklist`

> Disables any of the listed commands.

**Valid options:** a list of command names (as strings)

**Example:**

```yaml
command-blacklist:
    - "clear"
    - "join"
```

### `duration-limit`

> An amount of **hours** that queued tracks should be limited by. i.e, any song over this length will be blocked from playing.

**Valid options**: any positive number

**Example:**

```yaml
duration-limit: 2
```

### `embed-color`

> A hex code for the bot's message sidebar color.

**Valid options:** a string containing a valid color hex code

**Example:**

```yaml
embed-color: "ff00aa"
```

### `force-no-match`

> Forces the bot to think its not found any Spotify-YouTube match, thus bringing up the choice prompt every time. *This is primarily used for **debugging**, and should be left turned off in most cases.*

**Valid options:** `true` or `false`

**Example:**

```yaml
force-no-match: false
```

### `inactivity-timeout`

> A duration in **minutes** of bot inactivity (not actively playing any audio) that it should leave the voice channel after.

**Valid options:** any positive number

**Example:**

```yaml
inactivity-timeout: 10
```

### `logging-options`

> A key containing various options regarding how the bot will log its status out to the console. All of these options are only for customizing what you see in your command prompt or terminal — regardless of what you set here, everything will be saved in `vimusbot.log` for troubleshooting.

### `logging-options` → `show-console-logs`

> Enables or disables printing logs to the console for `bot.py` and `spoofy.py` separately.

**Valid options:** `true` or `false` for each file key

**Example:**

```yaml
logging-options:
    show-console-logs:
        bot.py: true
        spoofy.py: false
```

### `logging-options` → `show-verbose-logs`

> Some logs are marked as "verbose", typically meaning they contain more detailed or specific information about a task being performed. These are useful for debugging and troubleshooting, however some may see them as clutter, so this allows you to disable such logs from appearing in the console. Verbose logs are still written to `vimusbot.log` regardless.

**Valid options:** `true` or `false`

**Example:**

```yaml
logging-options:
    show-verbose-logs: false
```

### `logging-options` → `ignore-logs-from`

> Allows you to specify functions that you wish to hide logs from in the console. Function names are shown in **blue** (by default) if your console supports color — they appear after the filename (e.g `[bot.py]`).

**Valid options:** a list of strings containing valid function names

**Example:**

```yaml
logging-options:
    ignore-logs-from:
        - "search_ytmusic"
```

### `logging-options` → `colors`

> Allows you to specify colors for certain types of keywords within logs. Also contains the `no-color` key which will disable colored logging altogether.

**Valid options:** a color name that is any of the following...

```
lime
green
yellow
gold
red
darkred
magenta
darkmagenta
blue
darkblue
```

...for any of the keys listed in the example below.

**Example:**

```yaml
logging-options:
    colors:
        no-color: false # set to "true" to completely disable colored output
        bot-py: "yellow" # only the text that reads [bot.py]
        spoofy-py: "lime" # only the text that reads [spoofy.py]
        warn: "gold" # non-urgent warnings and notices
        error: "red" # used for tracebacks, and other complete failures
        timer: "magenta" # used for the time since the last log shown at the end
        function: "blue" # used for function names
```

### `maximum-urls`

> Maximum number of links that can be queued with one `-play` command.

**Valid options:** any positive number

**Example:**

```yaml
maximum-urls: 3
```

### `prefixes`

> Set the bot's command prefixes for public and developer mode.

**Valid options:** any string for each `public`/`developer` key

**Example:**

```yaml
prefixes:
    public: "!"
    developer: "%"
```

### `public`

> Starts the bot in "public" mode if set to true, or "developer" mode if set to false. Developer mode will make the bot use the [developer prefix](https://github.com/svioletg/viMusBot/blob/master/config.md#prefixes), and will enable developer-only [console commands](https://github.com/svioletg/viMusBot/blob/master/console.md).

**Valid options:** `true` or `false`

**Example:**

```yaml
public: true
```

### `show-users-in-queue`

> Enables or disables displaying who added what to the queue.

**Valid options:** `true` or `false`

**Example:**

```yaml
show-users-in-queue: true
```

### `spotify-playlist-limit`

> Prevents queueing a Spotify playlist longer than this limit.

**Valid options:** any positive number

**Example:**

```yaml
spotify-playlist-limit: 20
```

### `token-file`

> The path to use for the file your Discord bot token is stored in. By default this is `token.txt`, and you generally shouldn't have to change this. This is largely provided for debugging purposes.

**Valid options:** any valid path (as a string) to a file containing text

**Example:**

```yaml
token-file: "token.txt"
```

### `use-top-match`

> If enabled, the top result when trying to match a Spotify track to YouTube results will be used right away, otherwise if the bot isn't confident in its match, it will prompt the user to choose one from a list of top results.

**Valid options:** `true` or `false`

**Example:**

```yaml
use-top-match: true
```

### `use-url-cache`

> Enables or disables the use of the bot's URL caching system, which can slightly speed up the process of queueing in general.

**Valid options:** `true` or `false`

**Example:**

```yaml
use-url-cache: true
```

### `vote-to-skip`

> A category of keys relating to the vote-skip system.

### `vote-to-skip` → `enabled`

> Enables or disables vote-skipping. If disabled, the `-skip` command will skip tracks instantly.

**Valid options:** `true` or `false`

**Example:**

```yaml
vote-to-skip:
    enabled: true
```

### `vote-to-skip` → `threshold-type`

> How vote-skipping should function, by percentage or a defined total.

**Valid options:** `"percentage"` or `"exact"`

**Example:**

```yaml
vote-to-skip:
    threshold-type: "percentage"
```

### `vote-to-skip` → `threshold-percentage`

> The percentage of users (out of the total users present in the voice channel) that need to use `-skip` before the track will be skipped. Only needed if `threshold-type` is set to `"percentage"`.

**Valid options:** any positive number

**Example:**

```yaml
vote-to-skip:
    threshold-percentage: 75
```

### `vote-to-skip` → `threshold-exact`

> The exact number of users that need to use `-skip` before the track will be skipped. Only needed if `threshold-type` is set to `"exact"`.

**Valid options:** any positive number

**Example:**

```yaml
vote-to-skip:
    threshold-exact: 4
```