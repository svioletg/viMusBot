# viMusBot

## FAQ

Firstly, check the [issues page](https://github.com/svioletg/viMusBot/issues) to see if your problem has already been reported or solved. Most bugs are kept track of there — this page is only for issues that I cannot seem to fix, and require workarounds.

## How can viMusBot support Spotify links if its audio is protected by DRM?

viMusBot does not *directly* extract and play audio from a given Spotify link - instead, it simply uses the track info gathered from said link, and uses it to find the best possible match on YouTube Music (or standard YouTube, if the former fails). Feel free to dive into [spoofy.py](https://github.com/svioletg/viMusBot/blob/master/spoofy.py) to see how this is currently done — and if you're familiar with Python, don't hesitate to contribute any improvements if you see an opportunity!

## How can I change my bot's prefix, or set any other options?

Configuration is set using YAML: `config_default.yml` lists out every "key" you can change and their default values, this file is used as a fallback and should not be edited. To override any of these settings, create a `config.yml` file within your viMusBot directory if it's not already present, and write in any key (using the same structure as seen in the default file) with the value you want. For more in-depth information on every key, see [config.md](https://github.com/svioletg/viMusBot/blob/master/docs/config.md).

## Common issues
