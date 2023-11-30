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

### `key-name`

> Description

**Valid options:**

**Structure:**

```yaml
top-key:
    nested-key:
        key-name: # value here
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

### `allow-spotify-playlists`

> Allow or prevent the queueing of Spotify entire playlists.

**Valid options:** `true`/`false`

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

**Valid options:** `true`/`false`

**Example:**

```yaml
force-no-match: false
```

### `inactivity-timeout`

> A duration in **minutes** of bot inactivity (not actively playing any audio) that it should leave the voice channel after.

**Valid options**: any positive number

**Example:**

```yaml
inactivity-timeout: 10
```

### `prefixes`

> Set the bot's command prefix. Two options are given: *public*, and *developer*. Which one is used is determined by the `public` key described later.

**Valid options**: any string for each `public`/`developer` key

**Example:**

```yaml
prefixes:
    public: "!"
    developer: "%"
```

### `public`

> Currently only decides whether to use the public prefix (true), or the developer prefix (false).

**Valid options:** `true`/`false`

**Example:**

```yaml
public: true
```

### `token-file`

> The path to use for the file your Discord bot token is stored in. By default this is `token.txt`, and you generally shouldn't have to change this. This is largely provided for debugging purposes.

**Valid options:** any valid path (as a string) to a file containing text

**Example:**

```yaml
token-file: "token.txt"
```
