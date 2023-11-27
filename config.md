# viMusBot

## Using `config.yml` for configuration & customization

Your viMusBot folder will come with a `config_default.yml` file, which contains various settings needed for the bot to run. Most of what is provided are simply user preferences — things like the bot's command prefix, the color of its embed sidebar, aliases for commands, and limiting the duration of what can be played.

If you want to change these settings, you must create a `config.yml` file (the bot will create this file while starting up if it does not exist) and override the values for what you want to change. Anything not present in `config.yml` will use the default provided by `config_default.yml`.

**It is important to not directly change the values of `config_default.yml`, as this file will be replaced with each update.**

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
vote-to-skip:
    enabled: true
    threshold-percentage: 50
    threshold-type: "percentage"
```

`config_default.yml` has comments for each value, but I've also compiled every setting and its type + valid values on this page, to provide more thorough information.

## Glossary — Keys

> Written in alphabetical order.

### `aliases`
