"""Handles testing various parts of the `Voice` cog. Must be used in a running bot."""

# Standard imports
import itertools
import logging
import random
import time
from typing import Callable, Optional, cast

# External imports
from discord import Member
from discord.ext import commands

from cogs.common import command_from_alias, embedq, prompt_for_choice

log = logging.getLogger('lydian')

class VoiceTest:
    """Tests for the `Voice` cog."""
    test_sources = ['youtube', 'spotify', 'bandcamp', 'soundcloud']
    test_urls = {
            'single': {
                'valid': {
                    'youtube':    ['https://music.youtube.com/watch?v=bNpEUbWOBiM',
                                   'https://www.youtube.com/watch?v=3XAhEUHt3zY',
                                   'https://youtube.com/watch?v=Q-i1XZc8ZwA'],
                    'spotify':    ['https://open.spotify.com/track/1E2WTcYLP1dFe1tiGDwRmT?si=e83bb1fcb80640ad',
                                   'https://open.spotify.com/track/0WHtcCpZnoyFlQg3Mf2cdN?si=73230e1b24084038',
                                   'https://open.spotify.com/track/56k2ztFw7hQRzDeoe80pJo?si=90310e0adbf0472a'],
                    'bandcamp':   ['https://jeffrosenstock.bandcamp.com/track/graveyard-song',
                                   'https://jeffrosenstock.bandcamp.com/track/9-10',
                                   'https://jeffrosenstock.bandcamp.com/track/leave-it-in-the-sun'],
                    'soundcloud': ['https://soundcloud.com/sethgibbsmusic/rain',
                                   'https://soundcloud.com/weeppiko/like-a-thunder',
                                   'https://soundcloud.com/griffinmcelroy/the-adventure-zone-ethersea-theme']
                },
                'invalid': {
                    'youtube':    ['https://www.youtube.com/watch?v=THISISANINVALIDURLANDDOESNTEXIST'],
                    'spotify':    ['https://open.spotify.com/track/THISISANINVALIDURLANDDOESNTEXIST'],
                    'bandcamp':   ['https://THISISANINVALIDURLANDDOESNTEXIST.bandcamp.com/track/THISISANINVALIDURLANDDOESNTEXIST'],
                    'soundcloud': ['https://soundcloud.com/THISISANINVALIDURLANDDOESNTEXIST/THISISANINVALIDURLANDDOESNTEXIST']
                }
            },
            'playlist': {
                'valid': {
                    'youtube':    ['https://music.youtube.com/playlist?list=PL0uKqjIajhzGshCt76OeXLspFh5MmM-Vu',
                                   'https://www.youtube.com/playlist?list=PL67cMGyeB5sEh3ZjGgo8oXzIrbDggG1gs',
                                   'https://youtube.com/playlist?list=OLAK5uy_m-FE5IenHYY2Fd1M2RX-k11yKohFrvZi0'],
                    'spotify':    ['https://open.spotify.com/playlist/7IjLgeYeUkFzNvBirgfsAf?si=c55c2848887249da',
                                   'https://open.spotify.com/playlist/1FkZjVP9O80Chh37YhyKaU?si=d12241575b444d45',
                                   'https://open.spotify.com/playlist/3jlpvgHatDehrSrR72DYVq?si=932b79272c7c4a30'],
                    'bandcamp':   ['https://jeffrosenstock.bandcamp.com/album/hellmode',
                                   'https://jeffrosenstock.bandcamp.com/album/post',
                                   'https://jeffrosenstock.bandcamp.com/album/no-dream'],
                    'soundcloud': ['https://soundcloud.com/sethgibbsmusic/sets/2019-releases',
                                   'https://soundcloud.com/sethgibbsmusic/sets/original-tracks-2020',
                                   'https://soundcloud.com/sethgibbsmusic/sets/remixes']
                },
                'invalid': {
                    'youtube':    ['https://www.youtube.com/playlist?list=THISISANINVALIDURLANDDOESNTEXIST'],
                    'spotify':    ['https://open.spotify.com/playlist/THISISANINVALIDURLANDDOESNTEXIST'],
                    'bandcamp':   ['https://THISISANINVALIDURLANDDOESNTEXIST.bandcamp.com/album/THISISANINVALIDURLANDDOESNTEXIST'],
                    'soundcloud': ['https://soundcloud.com/THISISANINVALIDURLANDDOESNTEXIST/sets/THISISANINVALIDURLANDDOESNTEXIST']
                }
            },
            'album': {
                'valid': {
                    'youtube':    ['https://music.youtube.com/playlist?list=OLAK5uy_lQT8aLCDHiFu4_NkoxHt1VSfUBpjSIwHY',
                                   'https://www.youtube.com/playlist?list=OLAK5uy_kb8kfsyt08s2Z29752CH_lelHdl_JDwgg',
                                   'https://youtube.com/playlist?list=OLAK5uy_mp-RVdXLFGSC62WMsBlrqlF3RlZatyowA'],
                    'spotify':    ['https://open.spotify.com/album/1KMfjy6MmPorahRjxhTnxm?si=CS0F1ZFsQqSsn0xH_ahDiA',
                                   'https://open.spotify.com/album/74QTwjBLo1eLqpjL320rXX?si=1ehOqrxBR8WjHftNReHAtw',
                                   'https://open.spotify.com/album/3fn4HfVz5dhmE0PG24rh6h?si=tFUiBS7iSq6QGg-rNNgXkg'],
                    'bandcamp':   ['https://jeffrosenstock.bandcamp.com/album/hellmode',
                                   'https://jeffrosenstock.bandcamp.com/album/post',
                                   'https://jeffrosenstock.bandcamp.com/album/no-dream'],
                    'soundcloud': ['https://soundcloud.com/sethgibbsmusic/sets/2019-releases',
                                   'https://soundcloud.com/sethgibbsmusic/sets/original-tracks-2020',
                                   'https://soundcloud.com/sethgibbsmusic/sets/remixes']
                },
                'invalid': {
                    'youtube':    ['https://www.youtube.com/playlist?list=WROOOOOOOOONGLIIIIIIIIIIIINK'],
                    'spotify':    ['https://open.spotify.com/album/THISISALSOINCORRECTNOTAREALALBUM'],
                    'bandcamp':   ['https://THISISANINVALIDURLANDDOESNTEXIST.bandcamp.com/album/THISISANINVALIDURLANDDOESNTEXIST'],
                    'soundcloud': ['https://soundcloud.com/THISISANINVALIDURLANDDOESNTEXIST/sets/THISISANINVALIDURLANDDOESNTEXIST']
                }
            }
        }

    def __init__(self, inst):
        """
        @inst: A `Voice` cog instance.
        """
        self.inst = inst

    async def perform_test(self, ctx: commands.Context, name: str, *args):
        """Runs a matching test name.

        @name: Will be automatically prefixed with `test_` and called.
        """
        name = command_from_alias(name) or name
        name = 'test_' + name
        log.info('Performing test "%s"...', name)
        if not hasattr(self, name):
            log.error('Test "%s" does not exist.', name)
        test: Callable = getattr(self, name)
        log.info(test.__name__)
        log.info('\n\n%s%s', test.__doc__, '' if test.__doc__.endswith('\n') else '\n')
        await test(ctx, *args)

    async def test_play(self, ctx: commands.Context, source: str, flags: Optional[list[str]]=None, force_invalid: bool=False) -> Optional[dict]:
        """NOT a completely comprehensive test, but covers most common bases

        Valid flags:
        - `multiple` = Use multiple URLs
        - `playlist` = Use a playlist URL
        - `album` = Use an album URL

        "playlist" and "album" can't be used together

        @source: Any valid test source in `self.test_sources`, as well as `"any"` or `"mixed"`.\
            `any` chooses a single test source at random, `mixed` chooses a number of random test sources.
        @force_invalid: Use an intentionally invalid URL.
        """
        # if (not bypass_ctx) and (debugctx is None):
        #     log.error('Debug context is not set; aborting test. Use the "dctx" bot command while in a voice channel to grab one.')
        #     return

        if source not in self.test_sources + ['any', 'mixed']:
            log.error('Invalid source; aborting test. Valid sources are: %s', {', '.join(self.test_sources)})
            return

        flags = flags or []

        valid: str = 'invalid' if force_invalid else 'valid'
        playlist_or_album: str | bool = 'playlist' if 'playlist' in flags else 'album' if 'album' in flags else False
        multiple_urls: bool = 'multiple' in flags

        passed: bool = False
        conclusion: str = ''
        arguments: str = f'SOURCE? {source} | VALID? {valid} | MULTIPLE? {multiple_urls} | PLAYLIST/ALBUM? {playlist_or_album}'

        if 'playlist' in flags and 'album' in flags:
            log.error('Invalid flags; aborting test. The "playlist" and "album" flags cannot be used together.')
            return

        log.info('### START TEST! play command; %s', arguments)

        src = random.choice(self.test_sources) if source in ['any', 'mixed'] else source
        url_type = playlist_or_album if playlist_or_album else 'single'

        self.inst.voice_client = self.inst.voice_client or await cast(Member, ctx.author).voice.channel.connect()
        if not multiple_urls:
            await self.inst.play(ctx, random.choice(self.test_urls[url_type][valid][src]))
            if self.inst.voice_client.is_playing():
                conclusion = 'voice client is playing. Test likely passed.'
                log.info(conclusion)
                passed = True
            else:
                if valid == 'invalid':
                    conclusion = 'voice client is not playing, and an intentionally invalid URL was used. Test likely passed.'
                    log.info(conclusion)
                    passed = True
                else:
                    conclusion = 'voice client is not playing, but a valid URL was used. Test likely failed.'
                    log.info(conclusion)
        else:
            urls = []
            if source == 'mixed':
                for s in self.test_sources:
                    urls.append(random.choice(self.test_urls[url_type][valid][s]))
            else:
                urls = self.test_urls[url_type][valid][src]

            await self.inst.play(ctx, *urls)
            if self.inst.voice_client.is_playing() and self.inst.media_queue != []:
                conclusion = 'Voice client is playing and the queue is not empty. Test likely passed.'
                log.info(conclusion)
                passed = True
            else:
                if valid == 'invalid':
                    conclusion = 'Voice client is not playing, and an intentionally invalid URL was used. Test likely passed.'
                    log.info(conclusion)
                    passed = True
                elif playlist_or_album:
                    conclusion = 'Voice client is not playing, all URLs were valid,' + \
                        f'but multiple {playlist_or_album} URLs were used. Test likely passed.'
                    log.info(conclusion)
                    passed = True
                elif self.inst.media_queue != []:
                    conclusion = 'Voice client is not playing, but the queue is not empty. Test likely failed.'
                    log.info(conclusion)
                else:
                    conclusion = 'Voice client is not playing, but all valid URLs were used. Test likely failed.'
                    log.info(conclusion)

        log.info('Waiting 2 seconds...')
        time.sleep(2)
        log.info('Clearing media queue and stopping voice client...')
        self.inst.media_queue.clear()
        await self.inst.stop(ctx)
        log.info('Waiting 2 seconds...')
        time.sleep(2)
        log.info('### END TEST!')
        return {'passed': passed, 'arguments': arguments, 'conclusion': conclusion}
