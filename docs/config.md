# viMusBot / Configuration

viMusBot has many settings available to customize and configure your bot. To use them, create a `config.yml` file in the bot's directory. Here you'll enter any config "keys" that you wish to change, which will then override the default value for that option.

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

## Glossary

Written in alphabetical order. All information below should be accurate as of version **2.0.0**.

### `album-track-limit`

> Prevents queueing an album longer than this limit.


**Valid options:** any positive number

**Example:**

```yaml
album-track-limit: 20
```

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

### `allow-playlists-albums`

> Allow or prevent the queueing of entire playlists / albums.
> *NOTE: The bot will generally try its best to distinguish between a user-made playlist and an actual album, but the process isn't guaranteed to work, hence both being controlled by one configuration key.*

**Valid options:** `true` or `false`

**Example:**

```yaml
allow-playlists-albums: true
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

### `force-match-prompt`

> Forces the bot to think its not found any Spotify-YouTube match, thus bringing up the choice prompt every time. *This is primarily used for **debugging**, and should be left turned off in most cases.*

**Valid options:** `true` or `false`

**Example:**

```yaml
force-match-prompt: false
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

### `logging-options` → `console-log-level`

> Sets the "log level" for what you see in the console. Shows any logs including and higher than that level's priority.

**Valid options:** In order of ascending priority: "DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"

**Example:**

```yaml
logging-options:
    console-log-level: "INFO"
```

### `logging-options` → `log-full-tracebacks`

> Whether to log the entire traceback upon encountering an error. Again, tracebacks are still saved to the logfile no matter what, this only toggles them in the console window.

**Valid options:** `true` or `false`

**Example:**

```yaml
logging-options:
    log-full-tracebacks: false
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
        module: "blue" # used for file names
        warn: "gold" # non-urgent warnings and notices
        error: "red" # used for tracebacks, and other complete failures
        timer: "magenta" # used for the time since the last log shown at the end
        function: "blue" # used for function names
```

### `maximum-file-size`

> Maximum file size allowed for `yt_dlp` to download, in megabytes (MB).

**Valid options:** any positive number

**Example:**

```yaml
maximum-file-size: 10 # 10 MB
```

### `maximum-urls`

> Maximum number of links that can be queued with one `-play` command.

**Valid options:** any positive number

**Example:**

```yaml
maximum-urls: 3
```

### `play-history-max`

> Maximum number of tracks to store in the bot's "play history" — which can be accessed with the `-history` command.

**Valid options:** any positive number

**Example:**

```yaml
play-history-max: 5
```

### `playlist-track-limit`

> Prevents queueing a playlist longer than this limit.

**Valid options:** any positive number

**Example:**

```yaml
playlist-track-limit: 20
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

> Starts the bot in "public" mode if set to true, or "developer" mode if set to false. Developer mode will make the bot use the [developer prefix](#prefixes), and will enable developer-only [console commands](https://github.com/svioletg/viMusBot/blob/master/docs/console.md).

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
