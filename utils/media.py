"""Primarily provides methods for searching and returning 
standardized results from various sources."""

# Standard imports
import json
import logging
import re
from typing import Any, Callable, Literal, Optional, Self, cast

# External imports
import pytube
from benedict import benedict
from fuzzywuzzy import fuzz
from sclib import SoundcloudAPI
from sclib import Track as SoundcloudTrack
from spotipy import Spotify
from spotipy.oauth2 import SpotifyClientCredentials
from yt_dlp import YoutubeDL
from ytmusicapi import YTMusic

# Local imports
import utils.configuration as config
from utils.palette import Palette

log = logging.getLogger('viMusBot')

plt = Palette()

# Function to communicate with the bot and send status messages, useful for long tasks
bot_status_callback: Callable = lambda message: None

# Set constants from config
FORCE_MATCH_PROMPT     : bool = config.get('force-match-prompt') # type: ignore
SPOTIFY_PLAYLIST_LIMIT : int  = config.get('spotify-playlist-limit') # type: ignore
DURATION_LIMIT_SECONDS : int  = config.get('duration-limit') * 60 * 60 # type: ignore

# Useful to point this out if left on accidentally
if FORCE_MATCH_PROMPT:
    log.warning('force-match-prompt is turned on. '+\
        'This is not an inherent problem, but may cause unwanted behavior if left on by accident. '+\
        'Check your config.yml if this is was not intended.')

#region DEFINE CLASSES

# For typing, no functional difference
class MediaSource(str):
    """String subclass that represents a media source. Exists only for typing purposes."""

YOUTUBE    = MediaSource('youtube')
SPOTIFY    = MediaSource('spotify')
SOUNDCLOUD = MediaSource('soundcloud')
GENERIC    = MediaSource('generic') # Anything yt_dlp labels as generic

class MediaError(Exception):
    """Base class for media-related exceptions."""
    class FormatError(Exception):
        """Used for incorrect or unexpected MediaInfo formatting."""

class MediaInfo:
    """Base class for gathering standardized data from different media sources.
    
    Retrieves common attributes that can be obtained the same way regardless of type (Track, Album, Playlist).
    Generally should not be called directly; use the appropriate subclass instead.
    """
    def __init__(self, source: MediaSource, info: Any, yt_info_origin: Optional[Literal['pytube', 'ytmusic', 'ytdl']] = None):
        """
        @source: A valid MediaSource object.
        @info: A collection of info to be parsed and used for object creation. Exactly what this should be depends on the subclass.
        @yt_info_origin: YouTube media can come from three sources: the `pytube` library, the `ytmusicapi` library, and\
            the `yt-dlp` library. If none is specified, it will be automatically determined, however specifying here can save some time.
        """
        self.source: MediaSource = source
        self.info: Any = info
        self.yt_info_origin: Optional[Literal['pytube', 'ytmusic', 'ytdl']] = yt_info_origin

        self.url: str = ''
        self.title: str = ''
        self.artist: str = ''
        self.length_seconds: int = 0
        self.embed_image: str = ''
        self.album_name: str = ''
        self.release_year: str = ''

        if source == SPOTIFY:
            self.url            = cast(str, info['external_urls']['spotify'])
            self.title          = cast(str, info['name'])
            self.artist         = cast(str, benedict(self.info).get('artists[0].name', ''))
        elif source == SOUNDCLOUD:
            self.url            = cast(str, info.permalink_url)
            self.title          = cast(str, info.title)
            self.artist         = cast(str, info.user['username'])
            self.embed_image    = cast(str, info.artwork_url)
            self.length_seconds = int(info.duration // 1000)
        elif source == YOUTUBE:
            if not self.yt_info_origin:
                # Figure out YouTube dict source from either pytube, ytmusicapi, or yt_dlp
                if isinstance(self.info, (pytube.YouTube, pytube.Playlist)):
                    if isinstance(self.info, pytube.Playlist):
                        # Pytube only returns a list of URL strings for playlists which isn't very helpful,
                        # it's better to just enforce using other methods.
                        raise ValueError('pytube.Playlist should not be used to instance MediaInfo.')
                    self.yt_info_origin = 'pytube'
                    # Check if this video has a matching song result on YTMusic, which provides better info
                    log.debug('%s', self.url)
                    if ytmusic_result := ytmusic.search(query=self.info.watch_url.split('watch?v=')[1], filter='songs'):
                        self.yt_info_origin = 'ytmusic'
                        self.info = ytmusic_result[0]
                elif isinstance(self.info, dict):
                    if 'inLibrary' in self.info or 'browseId' in self.info:
                        # Should only be a YTMusic result dict, process as such
                        self.yt_info_origin = 'ytmusic'
                    else:
                        # Probably a dict from yt_dlp at this point
                        self.yt_info_origin = 'ytdl'

            if self.yt_info_origin == 'pytube':
                self.info = cast(pytube.YouTube, self.info)
                self.url            = cast(str, self.info.watch_url)
                self.title          = cast(str, self.info.title)
                self.artist         = cast(str, self.info.author)
                self.length_seconds = int(self.info.length)
                self.embed_image    = cast(str, self.info.thumbnail_url)

            elif self.yt_info_origin == 'ytmusic':
                self.info = cast(dict, self.info)
                self.title          = cast(str, self.info['title'])
                self.artist         = cast(str, self.info['artists'][0]['name'])
                self.embed_image    = cast(str, benedict(self.info).get('thumbnails[0].url', ''))

            elif self.yt_info_origin == 'ytdl':
                self.info = cast(dict, self.info)
                # It'll be 'webpage_url' if ytdl.extract_info() was used on a single video, but
                # 'url' if its a video dictionary from the entries list of a playlist's extracted info
                self.url            = cast(str, self.info.get('webpage_url') or self.info.get('url')) # type: ignore
                self.title          = cast(str, self.info['title']) # type: ignore
                self.artist         = cast(str, self.info['uploader']) # type: ignore
                self.embed_image    = cast(str, benedict(self.info).get('thumbnails[0].url', ''))

            else:
                raise ValueError(f'Invalid yt_result_origin received: {yt_info_origin}')
        else:
            raise ValueError(f'MediaSource object received that has no processing route: {source}')
    
    @classmethod
    def from_pytube(cls, info: pytube.YouTube | str) -> Self:
        """Shorthand for getting a MediaInfo object from a `pytube` source.
        @info: URL string, or a `pytube.YouTube` object
        """
        if isinstance(info, str):
            info = pytube.YouTube(info)
        return cls(YOUTUBE, info, yt_info_origin='pytube')

    @classmethod
    def from_ytmusic(cls, info: dict | str) -> Self:
        """Shorthand for getting a MediaInfo object from a `ytmusicapi` source.
        @info: URL string, or a dictionary returned by `ytmusicapi.ytmusic.YTMusic.search()`
        """
        if isinstance(info, str):
            info = ytmusic.search(info, filter='songs')[0]
        return cls(YOUTUBE, info, yt_info_origin='ytmusic')
    
    @classmethod
    def from_ytdl(cls, info: dict | str) -> Self:
        """Shorthand for getting a MediaInfo object from a `yt_dlp` source.
        @info: URL string, or a dictionary returned by `yt_dlp.YoutubeDL.YoutubeDL.extract_info()`
        """
        if isinstance(info, str):
            info = ytdl.extract_info(info, download=False) # type: ignore
        return cls(YOUTUBE, info, yt_info_origin='ytdl')

    def check_missing(self):
        """For debugging. Looks for and logs any attributes that may be "empty", in the sense that bool(attribute) would return False.
        Some attributes are safe to leave empty, but this can helpful to diagnose some problems.
        """
        print('Checking for any attributes of %s that may be empty...' % self)
        counter: int = 0
        for k, v in vars(self).items():
            if not v:
                print('%s returned as false. Its value is: %s' % k, repr(v))
                counter += 1
        print('%s empty attributes found.' % counter)

class TrackInfo(MediaInfo):
    """Specific parsing for single track data."""
    def __init__(self, source: MediaSource, info: Any, yt_info_origin: Optional[Literal['pytube', 'ytmusic', 'ytdl']] = None):
        """
        @info: Must be track info returned by any of the following:
            - `dict` from `spotipy.Spotify.track()`
            - a `sclib.sync.Track` object returned from `sclib.sync.SoundcloudAPI.resolve()`
            - a `pytube.YouTube` object
            - `dict` from a list item of `ytmusicapi.ytmusic.YTMusic.search()`
            - `dict` from `yt_dlp.YoutubeDL.YoutubeDL.extract_info()`
        """
        MediaInfo.__init__(self, source, info, yt_info_origin)
        self.isrc: str = '' # ISRC can help for more accurate YouTube searching

        if source == SPOTIFY:
            self.length_seconds = int(self.info['duration_ms'] // 1000)
            if 'album' in self.info:
                # An 'album' key indicates this was retrieved from Spotipy.track() or .playlist(), otherwise its from an album
                # get_group_contents() will take care of these in that case, although it can't get an ISRC
                self.embed_image  = cast(str, self.info['album']['images'][0]['url'])
                self.album_name   = cast(str, self.info['album']['name'])
                self.release_year = cast(str, self.info['album']['release_date'].split('-')[0])
                self.isrc         = cast(str, self.info['external_ids'].get('isrc', None))
        elif source == SOUNDCLOUD:
            self.release_year   = cast(str, self.info.release_date.split('-')[0]) if self.info.release_date else ''
        elif source == YOUTUBE:
            if self.yt_info_origin == 'pytube':
                pass
            elif self.yt_info_origin == 'ytmusic':
                self.url            = cast(str, 'https://www.youtube.com/watch?v=' + self.info['videoId'])
                self.length_seconds = int(self.info.get('duration_seconds') or self.info.get('lengthSeconds'))
                self.album_name     = cast(str, benedict(self.info).get('album.name', ''))
            elif self.yt_info_origin == 'ytdl':
                self.length_seconds = int(self.info['duration'])

class AlbumInfo(MediaInfo):
    """Specific parsing for album data."""
    def __init__(self, source: MediaSource, info: Any, yt_info_origin: Optional[Literal['pytube', 'ytmusic', 'ytdl']] = None):
        """
        @info: Must be track info returned by any of the following:
            - `dict` from `spotipy.Spotify.album()`
            - a `pytube.YouTube()` object
            - `dict` from a list item of `ytmusicapi.ytmusic.YTMusic.search()`
            - `dict` from `yt_dlp.YoutubeDL.YoutubeDL.extract_info()`
        """
        MediaInfo.__init__(self, source, info, yt_info_origin)
        self.contents: list[TrackInfo] = get_group_contents(self)
        self.upc: str = ''

        if source == SPOTIFY:
            self.length_seconds = track_list_duration(self.contents)
            self.embed_image    = cast(str, self.info['images'][0]['url'])
            self.album_name     = cast(str, self.info['name'])
            self.release_year   = cast(str, self.info['release_date'].split('-')[0])
            self.upc            = cast(str, self.info['external_ids']['upc'])
        elif source == SOUNDCLOUD:
            self.album_name     = cast(str, self.info.title)
            self.release_year   = cast(str, self.info.release_date.split('-')[0])
        elif source == YOUTUBE:
            if self.yt_info_origin == 'pytube':
                raise ValueError('pytube origin should not be used to instantiate AlbumInfo.')
            elif self.yt_info_origin == 'ytmusic':
                self.url = cast(str, 'https://www.youtube.com/playlist?list' + ytmusic.get_album(self.info['browseId'])['audioPlaylistId'])
                self.length_seconds = track_list_duration(self.contents)
                self.album_name     = cast(str, self.info['title'])
                self.release_year   = cast(str, self.info['year'])
            elif self.yt_info_origin == 'ytdl':
                self.length_seconds = track_list_duration(self.contents)

class PlaylistInfo(MediaInfo):
    """Specific parsing for playlist data."""
    def __init__(self, source: MediaSource, info: Any, yt_info_origin: Optional[Literal['pytube', 'ytmusic', 'ytdl']] = None):
        MediaInfo.__init__(self, source, info, yt_info_origin)
        self.contents: list[TrackInfo] = get_group_contents(self)

        if source == SPOTIFY:
            self.embed_image    = cast(str, self.info['images'][0]['url']) # TODO: This grabs the uncropped image, find out if that's a problem
            self.length_seconds = track_list_duration(self.contents)
        elif source == SOUNDCLOUD:
            pass
        elif source == YOUTUBE:
            if self.yt_info_origin == 'ytmusic':
                raise ValueError('ytmusic origin should not be used to instantiate PlaylistInfo.')
            if self.yt_info_origin == 'ytdl':
                self.length_seconds = track_list_duration(self.contents)

def track_list_duration(track_list: list[TrackInfo]) -> int:
    """Return the sum of track lengths from a list of TrackInfo objects."""
    return int(sum(track.length_seconds for track in track_list))

# Pylint warns about some return paths here returning None, but I can't find a situation where that would happen
def get_group_contents(group_object: AlbumInfo | PlaylistInfo) -> list[TrackInfo]: # type: ignore
    """Retrieves a list of TrackInfo objects based on the URLs found witin an AlbumInfo or PlaylistInfo object."""
    # TODO: This can take a while, maybe find a way to report status back to bot.py?
    track_list: list[Any] = []
    object_list: list[TrackInfo] = []
    if group_object.source == SPOTIFY:
        track_list = cast(list[dict], group_object.info['tracks']['items'])
        log.debug('Looking for MediaInfo group contents...')
        for n, track in enumerate(track_list):
            log.debug('Getting track %s out of %s...', n + 1, len(track_list))
            bot_status_callback(f'Looking for tracks... ({n+1} of {len(track_list)})')
            if isinstance(group_object, AlbumInfo):
                object_list.append(TrackInfo(SPOTIFY, cast(dict, track)))
                object_list[-1].embed_image  = group_object.embed_image
                object_list[-1].album_name   = group_object.album_name
                object_list[-1].release_year = group_object.release_year

            elif isinstance(group_object, PlaylistInfo):
                object_list.append(TrackInfo(SPOTIFY, cast(dict, track['track'])))
        return object_list

    if group_object.source == SOUNDCLOUD:
        track_list = group_object.info.tracks
        for track in track_list:
            object_list.append(TrackInfo(SOUNDCLOUD, track))
        return object_list

    if group_object.source == YOUTUBE:
        if group_object.yt_info_origin == 'ytmusic':
            track_list = ytmusic.get_album(group_object.info['browseId'])['tracks']
        if group_object.yt_info_origin == 'ytdl':
            track_list = group_object.info['entries']
        if group_object.yt_info_origin == 'pytube':
            raise ValueError('pytube origin incompatible with get_group_contents()')

        for track in track_list:
            object_list.append(TrackInfo(YOUTUBE, track))
        return object_list

#endregion

#region CONNECT APIs, ETC.

# Configure youtube dl
ytdl_format_options = {
    'format': 'bestaudio/best',
    'outtmpl': '%(extractor)s-#-%(id)s-#-%(title)s.%(ext)s',
    'restrictfilenames': True,
    'noplaylist': True,
    'nocheckcertificate': True,
    'ignoreerrors': False,
    'logtostderr': False,
    'quiet': True,
    'no_warnings': False,
    'default_search': 'auto',
    'extract_flat': True,
    'source_address': '0.0.0.0',  # bind to ipv4 since ipv6 addresses cause issues sometimes
}
ytdl = YoutubeDL(ytdl_format_options)

# Connect to youtube music API
ytmusic = YTMusic()

# Connect to spotify API
with open('spotify_config.json', 'r', encoding='utf-8') as f:
    scred = json.loads(f.read())['spotify']

client_credentials_manager = SpotifyClientCredentials(
    client_id = scred['client_id'],
    client_secret = scred['client_secret']
)
sp = Spotify(client_credentials_manager = client_credentials_manager)

# Connect to soundcloud API
sc = SoundcloudAPI()

#endregion

#region SETUP FINISHED
#endregion

class Testing:
    """For debugging. Generates every type of MediaInfo object for every valid source."""
    def __init__(self):
        self.t = {
            'sp':  TrackInfo(SPOTIFY, sp.track('https://open.spotify.com/track/1pmImsdC9t35L3TkD26ax8?si=7aad7529066b448d')),
            'sc':  TrackInfo(SOUNDCLOUD, sc.resolve('https://soundcloud.com/sethgibbsmusic/rain')),
            'ytm': TrackInfo(YOUTUBE, ytmusic.search('qAayzrbYYuM', filter='songs')[0]),
            'ytd': TrackInfo(YOUTUBE, ytdl.extract_info('https://www.youtube.com/watch?v=qAayzrbYYuM', download=False)),
            'ytp': TrackInfo(YOUTUBE, pytube.YouTube('https://www.youtube.com/watch?v=qAayzrbYYuM'))
        }
        print(self.t)
        self.a = {
            'sp':  AlbumInfo(SPOTIFY, sp.album('https://open.spotify.com/album/3jgktTCGathax8HKW4aGfg?si=d34b1518a5fc4ef0')),
            'sc':  AlbumInfo(SOUNDCLOUD, sc.resolve('https://soundcloud.com/sethgibbsmusic/sets/chromatic')),
            'ytm': AlbumInfo(YOUTUBE, ytmusic.search('No Dogs Allowed Sidney Gish', filter='albums')[0]),
            'ytd': AlbumInfo(YOUTUBE, ytdl.extract_info(
                'https://www.youtube.com/playlist?list=OLAK5uy_knTbxsoO4G4jNtofx7NSkKaBIaom5-314', download=False)),
        }
        print(self.a)
        self.p = {
            'sp':  PlaylistInfo(SPOTIFY, sp.playlist('https://open.spotify.com/playlist/2Av9o5qHogf6p6kYOGi0uL?si=1fe4d964e25a4e8f')),
            'sc':  PlaylistInfo(SOUNDCLOUD, sc.resolve('https://soundcloud.com/sethgibbsmusic/sets/2019-releases')),
            'ytd': PlaylistInfo(YOUTUBE, ytdl.extract_info(
                'https://www.youtube.com/playlist?list=PLvNp0Boas720BYHiEHd-zM942KP_bCSZ4', download=False)),
        }
        print(self.p)

    @staticmethod
    def verify(obj: TrackInfo | AlbumInfo | PlaylistInfo) -> None:
        """A testing method."""
        std = ['url', 'title', 'artist', 'length_seconds', 'embed_image', 'album_name', 'release_year']
        tra = ['isrc']
        alb = ['contents', 'upc']
        pla = ['contents']
        def check(attrs: list[str]):
            for a in attrs:
                has = bool(getattr(obj, a))
                print(f'{a} existence: {plt.lime if has else plt.red}{has}')
                if has:
                    print(f'...which is: {getattr(obj, a)}')
        check(std)
        if isinstance(obj, TrackInfo):
            check(tra)
        elif isinstance(obj, AlbumInfo):
            check(alb)
        elif isinstance(obj, PlaylistInfo):
            check(pla)

    @staticmethod
    def verall() -> None:
        """Testing method. Runs verify for every result returned."""
        r = Testing()
        for n, i in enumerate((r.t, r.p, r.a)):
            src = ['SINGLE TRACK,', 'PLAYLIST', 'ALBUM'][n]
            print(f'---## {src} ##---')
            for j in i:
                print(f'---| {j} |---')
                Testing.verify(i[j])

# Define matching logic
def compare_media(reference: MediaInfo, compared: MediaInfo,
        mode: Literal['fuzz', 'strict'] = 'fuzz',
        fuzz_threshold: int = 75,
        ignore_title: bool = False,
        ignore_artist: bool = False,
        ignore_album: bool = False,
        **kwargs) -> tuple[int, dict[str, bool]]:
    """Compares the data from two MediaInfo objects, and returns a percentage of how close they are overall, along with the individual
    matching factors themselves.
    
    @reference: MediaInfo object to compare against
    @compared: MediaInfo object to be compared
    @mode: Either 'fuzz' or 'strict'; 'fuzz' uses fuzzy matching to determine whether something should clear a check,\
        where 'strict' only checks for exact matches
    @fuzz_threshold: If using 'fuzz' mode, this is the minimum ratio a match must clear to pass the check
    @ignore_title: Forces a title matching check to pass
    @ignore_artist: Forces an artist matching check to pass
    @ignore_album: Forces an album matching check to pass
    """
    # mode is how exactly the code will determine a match
    # 'fuzz' = fuzzy matching, by default returns a match with a ratio of >75
    # 'strict' = checking for strings in other strings, how matching was done beforehand

    title_threshold: int = kwargs.get('title_threshold', fuzz_threshold)
    artist_threshold: int = kwargs.get('artist_threshold', fuzz_threshold)
    album_threshold: int = kwargs.get('album_threshold', fuzz_threshold)

    if (not reference.album_name) or (not compared.album_name):
        # If either is missing an album name, any checks would just fail, to don't check albums
        ignore_album = True

    # Things like "feat. X" and "XXXX Remaster" aren't present across all platform's titles,
    # so just filter that out
    details_check = re.compile(r'(\(feat\..*\))|(\(.*Remaster.*\))')
    reference.title = re.sub(details_check, '', reference.title)
    compared.title = re.sub(details_check, '', compared.title)

    if mode == 'fuzz':
        matching_title = fuzz.ratio(reference.title.lower(), compared.title.lower()) > title_threshold
        matching_artist = fuzz.ratio(reference.artist.lower(), compared.artist.lower()) > artist_threshold
        matching_album = fuzz.ratio(reference.album_name.lower(), compared.album_name.lower()) > album_threshold
    elif mode == 'strict': # TODO: Maybe deprecate strict mode
        matching_title = reference.title.lower() in compared.title.lower() or (
            reference.title.split(' - ')[0].lower() in compared.title.lower()
            and reference.title.split(' - ')[1].lower() in compared.title.lower()
            )
        matching_artist = reference.artist.lower() in compared.artist.lower()
        matching_album = reference.album_name.lower() in compared.album_name.lower()

    # Do not count tracks that are specific/alternate version,
    # unless said keyword matches the original Spotify title
    alternate_desired: bool = any(keyword in reference.title.lower() for keyword in ['remix', 'cover', 'version'])
    alternate_found: bool = any(keyword in compared.title.lower() for keyword in ['remix', 'cover', 'version'])
    alternate_check: bool = (alternate_desired and alternate_found) or (not alternate_desired and not alternate_found)

    match_results: dict[str, bool] = {
        'title': matching_title or ignore_title,
        'artist': matching_artist or ignore_artist,
        'album': matching_album or ignore_album,
        'alt': alternate_check,
    }
    return int((sum(v for k, v in match_results.items()) / len(match_results)) * 100), match_results

#region SOUNDCLOUD
def soundcloud_set(url: str) -> PlaylistInfo | AlbumInfo:
    """Retrieves a SoundCloud set and returns either a PlaylistInfo or AlbumInfo where applicable."""
    # Soundcloud playlists and albums use the same URL format, a set
    response: Any = sc.resolve(url)
    if isinstance(response, SoundcloudTrack):
        raise ValueError(f'Tried to retrieve a SoundCloud set with a single track URL: {url}')

    # is_album IS a member of Playlist, but Pylint doesn't seem to know that
    is_album: bool = response.is_album # pylint: disable=no-member
    return AlbumInfo(SOUNDCLOUD, response.tracks) if is_album else PlaylistInfo(SOUNDCLOUD, response.tracks)
#endregion

#region SPOTIFY
def spotify_track(url: str) -> TrackInfo:
    """Retrieves a Spotify track and returns it as a TrackInfo object."""
    track: dict = sp.track(url) # type: ignore
    if not track:
        raise MediaError(f'No track found for URL: {url}')

    return TrackInfo(source = SPOTIFY, info = track)

def spotify_playlist(url: str) -> PlaylistInfo:
    """Retrieves a Spotify track and returns it as a PlaylistInfo object."""
    playlist: dict = sp.playlist(url) # type: ignore
    if not playlist:
        raise MediaError(f'No playlist found for URL: {url}')

    return PlaylistInfo(source = SPOTIFY, info = playlist)

def spotify_album(url: str) -> AlbumInfo:
    """Retrieves a Spotify track and returns it as a AlbumInfo object."""
    album: dict = sp.album(url) # type: ignore
    if not album:
        raise MediaError(f'No album found for URL: {url}')

    return AlbumInfo(source = SPOTIFY, info = album)

def analyze_spotify_track(url: str) -> tuple:
    """Returns results from Spotify's "audio features" for a given track."""
    if features := sp.audio_features(url):
        data = features[0]
    else:
        raise MediaError(f'No features found for track: {url}')

    keytable = {
        0: 'C major (A minor)',
        1: 'C#/Db major (A#/Bb minor)',
        2: 'D major (B minor)',
        3: 'D#/Eb major (C minor)',
        4: 'E major (C#/Db minor)',
        5: 'F major (D minor)',
        6: 'F#/Gb major (D#/Eb minor)',
        7: 'G major (E minor)',
        8: 'G#/Ab major (F minor)',
        9: 'A major (F#/Gb minor)',
        10: 'A#/Bb major (G minor)',
        11: 'B major (G#/Ab minor)',
    }

    # Nicer formatting
    data['tempo'] = str(int(data['tempo']))+'bpm'
    data['key'] = keytable[data['key']]
    data['time_signature'] = str(data['time_signature'])+'/4'
    data['loudness'] = str(data['loudness'])+'dB'

    # Replace ms duration with readable duration
    ms = data['duration_ms']
    hours = int(ms / (1000 * 60 * 60))
    minutes = int(ms / (1000 * 60) % 60)
    seconds = int(ms / 1000 % 60)

    # Don't include hours if less than one
    hours = str(hours)
    hours += ':'
    if float(hours[:-1])<1:
        hours = ''
    length = f'{hours}{minutes}:{seconds:02d}'
    data['duration'] = length
    data.pop('duration_ms')

    # Ignore technical/non-useful information
    skip = ['type', 'id', 'uri', 'track_href', 'analysis_url', 'mode']

    return data, skip
#endregion

#region YTMUSIC
def search_ytmusic_text(query: str, max_results: int=1) -> dict[str, Optional[list[TrackInfo] | list[AlbumInfo]]]:
    """Searches YTMusic with a plain-text query. Returns a dictionary containing the top "song", "video", and album results.
    
    @query: String to search with.
    @results: Maximum number of search results to return, per each category.
    """
    songs, videos, albums = [ytmusic.search(query=query, limit=1, filter=category) for category in ['songs', 'videos', 'albums']]
    return {
        'songs': [TrackInfo.from_ytmusic(song) for song in songs][:max_results] if songs else None,
        'videos': [TrackInfo.from_ytmusic(video) for video in videos][:max_results] if videos else None,
        'albums': [TrackInfo.from_ytmusic(album) for album in albums][:max_results] if albums else None
    }

# TrackInfo(YOUTUBE, album, yt_info_origin='ytmusic')
# TrackInfo.from_ytmusic(album)

def match_ytmusic_album(src_info: AlbumInfo) -> AlbumInfo | None:
    """Attempts to find an album on YTMusic that matches `src_info`'s attributes as closely as possible."""
    title, artist, release_year = src_info.title, src_info.artist, src_info.release_year
    query = f'{title} {artist} {release_year}'

    log.info('Starting album search...')

    album_results = [AlbumInfo(YOUTUBE, result, 'ytmusic') for result in ytmusic.search(query=query, limit=1, filter='albums')]

    for result in album_results:
        if compare_media(src_info, result)[0] >= 100:
            log.info('Match found.')
            return result

    log.info('No match found.')
    return None

def match_ytmusic_track(src_info: TrackInfo) -> TrackInfo | list[TrackInfo]:
    """Uses a TrackInfo object to try and retrieve the closest match from YTMusic.
    If no close match could be found — as determined by `compare_media()` — a list of potential matches (`TrackInfo` objects) will be returned.
    Otherwise, just one is returned.
    """

    query = f'{src_info.title} {src_info.artist} {src_info.album_name}'

    # Start search
    if (not FORCE_MATCH_PROMPT) and src_info.isrc:
        log.info('Searching for ISRC: %s', src_info.isrc)
        # pytube is more accurate when searching with an ISRC
        pytube_results = pytube.Search(src_info.isrc).results
        if pytube_results:
            isrc_matches: list[pytube.YouTube] = pytube_results

            log.debug('About to search through potential ISRC matches, of which there are %s. Reference title is: %s',
                len(isrc_matches), src_info.title)
            for n, song in enumerate(isrc_matches):
                # If the title and ISRC match, this is a confident enough match for us
                ratio = fuzz.ratio(song.title, src_info.title)
                log.debug('[%s/%s] Title match ratio is %s: "%s"',
                    n + 1, len(isrc_matches), ratio, song.title)
                if ratio > 75:
                    log.info('Found an ISRC match.')
                    try:
                        # YTMusic has more useful information
                        log.debug('Trying to get information from YTMusic for this match instead of pytube...')
                        track = TrackInfo(YOUTUBE, ytmusic.get_song(song.video_id)['videoDetails'], yt_info_origin='ytmusic')
                        track.album_name = src_info.album_name
                        track.artist = src_info.artist
                        track.embed_image = src_info.embed_image
                        track.isrc = src_info.isrc
                        return track
                    except KeyError:
                        log.debug('Couldn\'t find YTMusic equivalent. TrackInfo will be created with the original pytube object.')
                        return TrackInfo(YOUTUBE, song, yt_info_origin='pytube')

        log.info('No ISRC match found, trying text search.')

    log.info('Searching YTMusic for: %s', query)
    song_results, video_results = [
        [TrackInfo(YOUTUBE, result, yt_info_origin='ytmusic') for result in ytmusic.search(query=query, limit=1, filter=filt)]\
        for filt in ['songs', 'videos']
    ]

    # Remove videos over the specified duration limit
    for song, video in zip(song_results, video_results):
        if song.length_seconds > DURATION_LIMIT_SECONDS:
            song_results.pop(song_results.index(song))

        if video.length_seconds > DURATION_LIMIT_SECONDS:
            video_results.pop(video_results.index(video))

    track_choices: list[TrackInfo] = []

    for result in song_results[:2]:
        track_choices.append(result)

    for result in video_results[:2]:
        track_choices.append(result)

    if FORCE_MATCH_PROMPT:
        log.info('force-match-prompt is enabled, returning choices without checking for matches.')
        return track_choices

    # Check for matches
    log.info('Checking for a close match...')

    # First pass, check officially uploaded songs from artist channels
    for song in song_results[:5]:
        if compare_media(src_info, song, ignore_artist=True)[0] >= 100:
            log.info('Song match found.')
            song.release_year = src_info.release_year
            return song

    # Next, try standard non-"song" videos
    log.info('No "song" match found. Checking videos results...')
    for video in video_results[:5]:
        if compare_media(src_info, video, ignore_artist=True, ignore_album=True)[0] >= 100:
            log.info('Video match found.')
            video.album_name = src_info.album_name
            video.release_year = src_info.release_year
            return video

    log.info('No confident matches were found. Returning the closest ones...')
    return track_choices
#endregion

# Other
def spyt(url: str) -> TrackInfo | list[TrackInfo]:
    """Matches a Spotify URL with its closest match from YouTube or YTMusic"""
    return match_ytmusic_track(spotify_track(url))
