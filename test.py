import sys

from vmbutils.logging import Log

bot_logger = Log()
log = bot_logger.log
log('Test!')

import vmbutils.media as media

log('SPOTIFY: TRACK')
var = media.spotify_track('https://open.spotify.com/track/4A003vQ5hw24V0WajOageQ?si=7aab24e020f14b38')
print(var)
log('DONE!')
log('SPOTIFY: ALBUM')
var = media.spotify_album('https://open.spotify.com/album/0RyezpNCj0HGTv2Mrwaat5?si=edfba21fdfdb4020')
print(var)
log('DONE!')
log('SPOTIFY: PLAYLIST')
var = media.spotify_playlist('https://open.spotify.com/playlist/05m7rZf4SP4qHRrRBVK8yf?si=5c1b75b3a514435f')
print(var)
log('DONE!')
