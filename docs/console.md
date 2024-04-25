# viMusBot / Using the Console

Added in v1.9.0, the **console** lets you type and run commands into the terminal or window the bot is running in. Note that these "commands" are entirely separate from the "commands" you would use on Discord itself — most of them are just for getting some basic information, or for developer debugging usage. A few notes about using them:

- Console commands do not use any prefix, and are case-insensitive.
- If the bot sends a log message while typing a command, it may appear disconnected or pushed up — the console will still count this as the same string until you hit enter/return, so just continue typing and it will work as usual.

- Less-than and greater-than signs indicate **required parameters**, like `<this>`, while square brackets indicate **optional parameters**, like `[this]`; remember not to include the `<>` or `[]` symbols in the actual command.
- Commands with lots of extra options may have an argument called `flags`. Unlike most arguments, this is not meant to be a single value, but one or more of a given set of valid terms that will modify the conditions of the command being run.
- Any commands that are prefaced with "(dev)" will only function if `public` is turned off in your configuration.
- Lastly, some commands require a discord.py `context` object in order to function. These commands will be indicated with "(ctx)" by their name; use the `-dctx` command in Discord to obtain a debug context object — if the command requires connecting to a voice channel, like `test play`, you'll need to be connected to a voice channel first.

## Commands

### `colors`

> Displays the current console logging color palette: default color names followed by the customizable colors (warn, error, etc.)

*Parameters: N/A*

### `stop`

*Parameters: N/A*

Attempts to cancel the currently running bot & console threads, and exits the script.

### (dev) (ctx) `test play <source> [flags]`

> Tests the "play" Discord command with a variety of scenarios.

*Parameters:*
- `source`
  - *Required*; The source of URL(s) to test
  - Valid options are `any`, `mixed`, `youtube`, `spotify`, `bandcamp`, `soundcloud`
    - `any` will choose a single source at random
    - `mixed` will choose multiple random sources (if the `multiple` flag is not used, this has the same effect as `any`)
  - You can also use `all` here to automatically test every single combination
    - **This can take several minutes to complete!**
    - Any additional flags supplied after `all` will be ignored
- `flags`
  - *Optional*; Modifies the test's conditions
  - Valid options:
    | Name | Description |
    |-|-|
    | `invalid` | Use an intentionally invalid URL |
    | `multiple` | Use multiple URLs |
    | `playlist` | Use a playlist URL |
    | `album` | Use an album URL |

    > Note: The "playlist" and "album" flags cannot be used together in the same command

*Example:*
```
test play spotify playlist
```
