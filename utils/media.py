"""Primarily provides methods for searching and returning 
standardized results from various sources."""

# Standard imports
import json
import traceback
from typing import Any, Callable, Literal, cast

# External imports
import pytube
import regex as re
from benedict import benedict
from fuzzywuzzy import fuzz
from sclib import SoundcloudAPI, Track as SoundcloudTrack, Playlist as SoundcloudPlaylist
from spotipy import Spotify
from spotipy.exceptions import SpotifyException
from spotipy.oauth2 import SpotifyClientCredentials
from yt_dlp import YoutubeDL
from ytmusicapi import YTMusic

# Local imports
import utils.configuration as config
from utils.palette import Palette

plt = Palette()

# Logs won't be printed unless bot.py assigns this to its own logger
log: Callable = lambda message, verbose=False: None

# Function to communicate with the bot and send status messages, useful for long tasks
bot_status_callback: Callable = lambda message: None

# Set constants from config
FORCE_NO_MATCH         : bool = config.get('force-no-match') # type: ignore
SPOTIFY_PLAYLIST_LIMIT : int  = config.get('spotify-playlist-limit') # type: ignore
DURATION_LIMIT         : int  = config.get('duration-limit') # type: ignore

# Useful to point this out if left on accidentally
if FORCE_NO_MATCH:
    log(f'{plt.warn}NOTICE: force_no_match is set to True.')

#region DEFINE CLASSES

# For typing, no functional difference
class MediaSource(str):
    """String subclass that represents a media source. Exists only for typing purposes."""

YOUTUBE    = MediaSource('youtube')
SPOTIFY    = MediaSource('spotify')
SOUNDCLOUD = MediaSource('soundcloud')

class MediaError(Exception):
    # TODO: Re-evaluate if this is needed once this file's rework is done
    """Base class for media-related exceptions."""
    class FormatError(Exception):
        """Used for incorrect or unexpected MediaInfo formatting."""

class MediaInfo:
    """Base class for gathering standardized data from different media sources.
    
    Retrieves common attributes that can be obtained the same way regardless of type (Track, Album, Playlist).
    Generally should not be called directly; use the appropriate subclass instead.
    """
    def __init__(self, source: MediaSource, info: Any, yt_result_origin: Literal['pytube', 'ytmusic', 'ytdl'] | None = None):
        self.source: MediaSource = source
        self.info: Any = info
        self.yt_result_origin: Literal['pytube', 'ytmusic', 'ytdl'] | None = yt_result_origin

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
            if not self.yt_result_origin:
                # Figure out YouTube dict source from either pytube, ytmusicapi, or yt_dlp
                if isinstance(self.info, (pytube.YouTube, pytube.Playlist)):
                    if isinstance(self.info, pytube.Playlist):
                        # Pytube only returns a list of URL strings for playlists which isn't very helpful,
                        # it's better to just enforce using other methods.
                        raise ValueError('pytube.Playlist should not be used to instance MediaInfo.')
                    self.yt_result_origin = 'pytube'
                    self.url = cast(str, self.info.watch_url)
                    # Check if this video has a matching song result on YTMusic, which provides better info
                    if ytmusic_result := ytmusic.search(query = self.url.split('watch?v=')[1], filter = 'songs'):
                        self.yt_result_origin = 'ytmusic'
                        self.info = ytmusic_result[0]
                elif isinstance(self.info, dict):
                    if 'inLibrary' in self.info or 'browseId' in self.info:
                        # Should only be a YTMusic result dict, process as such
                        self.yt_result_origin = 'ytmusic'
                    else:
                        # Probably a dict from yt_dlp at this point
                        self.yt_result_origin = 'ytdl'
            # Lots of type ignores here, Pylance seems confused
            if self.yt_result_origin == 'pytube':
                self.title          = cast(str, self.info.title) # type: ignore
                self.artist         = cast(str, self.info.author) # type: ignore
                self.length_seconds = int(self.info.length) # type: ignore
                self.embed_image    = cast(str, self.info.thumbnail_url) # type: ignore
            
            if self.yt_result_origin == 'ytmusic':
                self.title          = cast(str, self.info['title']) # type: ignore
                self.artist         = cast(str, [item['name'] for item in self.info['artists'] if item['name'] != 'Album'][0]) # type: ignore
                self.embed_image    = cast(str, benedict(self.info).get('thumbnails[0].url', ''))
            elif self.yt_result_origin == 'ytdl':
                # It'll be 'webpage_url' if ytdl.extract_info() was used on a single video, but
                # 'url' if its a video dictionary from the entries list of a playlist's extracted info
                self.url            = cast(str, self.info.get('webpage_url', self.info.get('url'))) # type: ignore
                self.title          = cast(str, self.info['title']) # type: ignore
                self.artist         = cast(str, self.info['uploader']) # type: ignore
                self.embed_image    = cast(str, benedict(self.info).get('thumbnails[0].url', ''))
        else:
            pass

class TrackInfo(MediaInfo):
    """Specific parsing for single track data."""
    def __init__(self, source: MediaSource, info: Any, yt_result_origin: Literal['pytube', 'ytmusic', 'ytdl'] | None = None):
        MediaInfo.__init__(self, source, info, yt_result_origin)
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
            if self.yt_result_origin == 'pytube':
                pass
            if self.yt_result_origin == 'ytmusic':
                self.url = cast(str, f'https://www.youtube.com/watch?v={self.info['videoId']}')
                self.length_seconds = int(self.info['duration_seconds'])
                self.album_name     = cast(str, self.info['album'])
            if self.yt_result_origin == 'ytdl':
                self.length_seconds = int(self.info['duration'])
        else:
            pass

class AlbumInfo(MediaInfo):
    """Specific parsing for album data."""
    def __init__(self, source: MediaSource, info: Any, yt_result_origin: Literal['pytube', 'ytmusic', 'ytdl'] | None = None):
        MediaInfo.__init__(self, source, info, yt_result_origin)
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
            if self.yt_result_origin == 'pytube':
                self.upc = cast(str, self.info.upc)
            elif self.yt_result_origin == 'ytmusic':
                self.url            = cast(str, f'https://www.youtube.com/playlist?list={ytmusic.get_album(self.info['browseId'])['audioPlaylistId']}')
                self.length_seconds = track_list_duration(self.contents)
                self.album_name     = cast(str, self.info['title'])
                self.release_year   = cast(str, self.info['year'])
            elif self.yt_result_origin == 'ytdl':
                self.length_seconds = track_list_duration(self.contents)
        else:
            pass

class PlaylistInfo(MediaInfo):
    """Specific parsing for playlist data."""
    def __init__(self, source: MediaSource, info: Any, yt_result_origin: Literal['pytube', 'ytmusic', 'ytdl'] | None = None):
        MediaInfo.__init__(self, source, info, yt_result_origin)
        self.contents: list[TrackInfo] = get_group_contents(self)

        if source == SPOTIFY:
            self.embed_image    = cast(str, self.info['images'][0]['url']) # TODO: This grabs the uncropped image, find out if that's a problem
            self.length_seconds = track_list_duration(self.contents)
        if source == SOUNDCLOUD:
            pass
        if source == YOUTUBE:
            if self.yt_result_origin == 'ytmusic':
                raise ValueError('ytmusic origin is incompatible with PlaylistInfo.')
            if self.yt_result_origin == 'ytdl':
                self.length_seconds = track_list_duration(self.contents)
        else:
            pass

def track_list_duration(track_list: list[TrackInfo]) -> int:
    """Return the sum of track lengths from a list of TrackInfo objects."""
    return int(sum(track.length_seconds for track in track_list))

# Pylance warns about some return paths here returning None, but I can't find a situation where that would happen
def get_group_contents(group_object: AlbumInfo | PlaylistInfo) -> list[TrackInfo]: # type: ignore
    """Retrieves a list of TrackInfo objects based on the URLs found witin an AlbumInfo or PlaylistInfo object."""
    # TODO: This can take a while, maybe find a way to report status back to bot.py?
    track_list: list[Any] = []
    object_list: list[TrackInfo] = []
    if group_object.source == SPOTIFY:
        track_list = cast(list[dict], group_object.info['tracks']['items'])
        for n, track in enumerate(track_list):
            log(f'Getting track {n+1} out of {len(track_list)}...', verbose=True)
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
        if group_object.yt_result_origin == 'ytmusic':
            track_list = ytmusic.get_album(group_object.info['browseId'])['tracks']
        if group_object.yt_result_origin == 'ytdl':
            track_list = group_object.info['entries']
        if group_object.yt_result_origin == 'pytube':
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

class Testing:
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
            'ytd': AlbumInfo(YOUTUBE, ytdl.extract_info('https://www.youtube.com/playlist?list=OLAK5uy_knTbxsoO4G4jNtofx7NSkKaBIaom5-314', download=False)),
        }
        print(self.a)
        self.p = {
            'sp':  PlaylistInfo(SPOTIFY, sp.playlist('https://open.spotify.com/playlist/2Av9o5qHogf6p6kYOGi0uL?si=1fe4d964e25a4e8f')),
            'sc':  PlaylistInfo(SOUNDCLOUD, sc.resolve('https://soundcloud.com/sethgibbsmusic/sets/2019-releases')),
            'ytd': PlaylistInfo(YOUTUBE, ytdl.extract_info('https://www.youtube.com/playlist?list=PLvNp0Boas720BYHiEHd-zM942KP_bCSZ4', download=False)),
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

# SoundCloud
def soundcloud_set(url: str) -> PlaylistInfo | AlbumInfo:
    """Retrieves a SoundCloud set and returns either a PlaylistInfo or AlbumInfo where applicable."""
    # Soundcloud playlists and albums use the same URL format, a set
    response: Any = sc.resolve(url)
    if isinstance(response, SoundcloudTrack):
        raise ValueError(f'Tried to retrieve a SoundCloud set with a single track URL: {url}')

    # is_album IS a member of Playlist, but Pylint doesn't seem to know that
    is_album: bool = response.is_album # pylint: disable=no-member
    return AlbumInfo(SOUNDCLOUD, response.tracks) if is_album else PlaylistInfo(SOUNDCLOUD, response.tracks)

# Spotify
def spotify_track(url: str) -> TrackInfo:
    """Retrieves a Spotify track and returns it as a TrackInfo object."""
    track: dict = sp.track(url) # type: ignore
    if not track:
        raise MediaError(f'No track found for URL: {url}')

    return TrackInfo(source = SPOTIFY, info = track)

def spotify_playlist(url: str) -> PlaylistInfo:
    """Retrieves a Spotify track and returns it as a PlaylistInfo object.

    Returns a SpotifyException if retrieval fails."""
    playlist: dict = sp.playlist(url) # type: ignore
    if not playlist:
        raise MediaError(f'No playlist found for URL: {url}')

    return PlaylistInfo(source = SPOTIFY, info = playlist)

def spotify_album(url: str) -> AlbumInfo:
    """Retrieves a Spotify track and returns it as a AlbumInfo object.

    Returns a SpotifyException if retrieval fails."""
    album: dict = sp.album(url) # type: ignore
    if not album:
        raise MediaError(f'No album found for URL: {url}')

    return AlbumInfo(source = SPOTIFY, info = album)

# Define matching logic
def compare_media(reference: dict, ytresult: dict,
        mode: Literal['fuzz', 'strict'] = 'fuzz',
        fuzz_threshold: int = 75,
        ignore_title: bool = False,
        ignore_artist: bool = False,
        ignore_album: bool = False,
        **kwargs) -> bool:
    # TODO: Review this!
    # mode is how exactly the code will determine a match
    # 'fuzz' = fuzzy matching, by default returns a match with a ratio of >75
    # 'strict' = checking for strings in other strings, how matching was done beforehand

    title_threshold = kwargs.get('title_threshold', fuzz_threshold)
    artist_threshold = kwargs.get('artist_threshold', fuzz_threshold)
    album_threshold = kwargs.get('album_threshold', fuzz_threshold)

    ref_title, ref_artist, ref_album = reference['title'], reference['artist'], reference['album']
    yt_title, yt_artist = ytresult['title'], ytresult['artists'][0]['name']
    try:
        yt_album = ytresult['album']['name']
    except KeyError as e:
        log(f'Ignoring album name. (Cause: {traceback.format_exception(e)[-1]})')
        # User-uploaded videos have no 'album' key
        yt_album = ''

    check = re.compile(r'(\(feat\..*\))|(\(.*Remaster.*\))')
    ref_title = check.sub('',ref_title)
    yt_title = check.sub('',yt_title)

    if mode == 'fuzz':
        matching_title = fuzz.ratio(ref_title.lower(), yt_title.lower()) > title_threshold
        matching_artist = fuzz.ratio(ref_artist.lower(), yt_artist.lower()) > artist_threshold
        matching_album = fuzz.ratio(ref_album.lower(), yt_album.lower()) > album_threshold
    elif mode == 'strict':
        matching_title = ref_title.lower() in yt_title.lower() or (
            ref_title.split(' - ')[0].lower() in yt_title.lower() 
            and ref_title.split(' - ')[1].lower() in yt_title.lower()
            )
        matching_artist = ref_artist.lower() in yt_artist.lower()
        matching_album = ref_album.lower() in yt_album.lower()
        
    # Do not count tracks that are specific/alternate version,
    # unless said keyword matches the original Spotify title
    alternate_desired = any(i in ref_title.lower() for i in ['remix', 'cover', 'version'])
    alternate_found = any(i in yt_title.lower() for i in ['remix', 'cover', 'version'])
    alternate_check = (alternate_desired and alternate_found) or (not alternate_desired and not alternate_found)
    # TODO: Rework to use a confidence score
    return (matching_title or ignore_title) \
        and (matching_artist or ignore_artist) \
        and (matching_album or ignore_album) \
        and (alternate_check)

# Youtube
def pytube_track_data(pytube_object: pytube.YouTube) -> dict:
    # TODO: Docstring, better name!
    # This must be done in order for the description to load in
    try:
        pytube_object.bypass_age_gate()
        description_list = pytube_object.description.split('\n')
        # TODO: Figure out what exception this actually raises
    except Exception as e:
        print(e)
        log(f'pytube description retrieval failed; using ytdl...', verbose=True)
        log(f'Cause of the above: {e}')
        ytdl_info = ytdl.extract_info(pytube_object.watch_url)
        if not ytdl_info:
            raise ValueError('ytdl.extract_info() returned None')
        description_list: list[str] = ytdl_info['description'].split('\n')

    if '' not in description_list[0]:
        # This function won't work if it doesn't follow the auto-generated template on most official song uploads
        raise MediaError.FormatError(f'{plt.warn} Unexpected YouTube description formatting. URL: {pytube_object.watch_url}')

    for item in description_list.copy():
        if item == '':
            description_list.pop(description_list.index(item))

    description_dict = {
        # some keys have been added for previous code compatbility
        'title': pytube_object.title,
        'artists': [{'name':description_list[1].split(' · ')[1]}],
        'album': {'name': description_list[2]},
        'length': pytube_object.length,
        'videoId': pytube_object.video_id
    }

    return description_dict

def search_ytmusic_text(query: str) -> dict:
    """Searches YTMusic with a plain-text query."""
    songs, videos = [ytmusic.search(query=query, limit=1, filter=filt) for filt in ['songs', 'videos']]
    top_song: dict | None = songs[0] if songs else None
    top_video: dict | None = videos[0] if songs else None

    return {'top_song': top_song, 'top_video': top_video}

def search_ytmusic_album(album_info: AlbumInfo) -> str | None:
    """Attempts to find an album on YTMusic that matches `album_info`'s attributes as closely as possible."""
    if FORCE_NO_MATCH:
        log(f'{plt.warn}force_no_match is set to True.'); return None

    title, artist, release_year = album_info.title, album_info.artist, album_info.release_year
    query = f'{title} {artist} {release_year}'
    
    log('Starting album search...', verbose=True)
    check = re.compile(r'(\(feat\..*\))|(\(.*Remaster.*\))')

    album_results = ytmusic.search(query=query, limit=5, filter='albums')
    for yt in album_results:
        title_match = fuzz.ratio(check.sub('', title), check.sub('', yt['title'])) > 75
        artist_match = fuzz.ratio(artist, yt['artists'][0]['name']) > 75
        year_match = fuzz.ratio(release_year, yt['year']) > 75
        if title_match + artist_match + year_match >= 2:
            log('Match found.', verbose=True)
            return 'https://www.youtube.com/playlist?list='+ytmusic.get_album(yt['browseId'])['audioPlaylistId']
    
    song_results = ytmusic.search(query=query,limit=5,filter='songs')
    for yt in song_results:
        title_match = fuzz.ratio(check.sub('', title), check.sub('', yt['album']['name'])) > 75
        artist_match = fuzz.ratio(artist, yt['artists'][0]['name']) > 75
        year_match = fuzz.ratio(release_year, yt['year']) > 75
        if title_match + artist_match + year_match >= 2:
            log('Match found.', verbose=True)
            return 'https://www.youtube.com/playlist?list='+ytmusic.get_album(yt['album']['id'])['audioPlaylistId']
    
    log('No match found.', verbose=True)
    return None

# Trim ytmusic song data down to what's relevant to us
def trim_track_data(data: dict | pytube.YouTube, album: str='') -> dict:
    # TODO: Might be unnecessary now, verify
    if isinstance(data, pytube.YouTube):
        data = pytube_track_data(data)
        try:
            album = data['album']['name']
        except KeyError as e:
            log(f'Failed to retrieve album from pytube object. ({e})', verbose=True)
            pass
    if 'duration' in data: duration = data['duration']
    elif 'length' in data: duration = data['length']
    relevant = {
        'title': data['title'],
        'artist': data['artists'][0]['name'],
        'url': 'https://www.youtube.com/watch?v='+data['videoId'],
        'album': album,
        'duration': duration,
    }
    return relevant

def search_ytmusic(title: str, artist: str, album: str, isrc: str='', limit: int=10, fast_search: bool=False):
    unsure = False

    query = f'{title} {artist} {album}'
    reference = {'title':title, 'artist':artist, 'album':album, 'isrc':isrc}

    # Start search
    if (isrc) and (not FORCE_NO_MATCH):
        log(f'Searching for ISRC: {isrc}', verbose=True)
        # For whatever reason, pytube seems to be more accurate here
        pytube_results = pytube.Search(isrc).results
        if not pytube_results:
            log('No ISRC match found, falling back on text search.')
        isrc_matches: list = cast(list, pytube_results)
        for song in isrc_matches:
            if fuzz.ratio(song.title, reference['title']) > 75:
                log('Found an ISRC match.', verbose=True)
                return trim_track_data(song)
            
        log('No ISRC match found, falling back on text search.')

    log(f'Trying query \"{query}\" with a limit of {limit}')
    song_results = ytmusic.search(query=query, limit=limit, filter='songs')
    video_results = ytmusic.search(query=query, limit=limit, filter='videos')
    # Remove videos over a certain length
    for s, v in zip(song_results, video_results):
        if int(s['duration_seconds']) > DURATION_LIMIT*60*60:
            song_results.pop(song_results.index(s))
        if int(v['duration_seconds']) > DURATION_LIMIT*60*60:
            video_results.pop(video_results.index(v))
    
    if fast_search:
        log('fast_search is True.', verbose=True)
        log('Returning match.', verbose=True)
        return trim_track_data(song_results[0])

    log('Checking for exact match...')
    if FORCE_NO_MATCH:
        log(f'{plt.warn}NOTICE: force_no_match is set to True.')

    # Check for matches
    match = None
    def match_found() -> bool:
        return match != None if not FORCE_NO_MATCH else False

    if is_jp(query):
        # Assumes first Japanese result is correct, otherwise
        # it won't be recognized since YT Music romanizes/translates titles
        # See: https://github.com/svioletg/viMusBot/issues/11
        match = song_results[0]

    # First pass, check officially uploaded songs from artist channels
    for song in song_results[:5]:
        if compare_media(reference, song, ignore_artist=True):
            log('Song match found.')
            match = song
            break

    # Next, try standard non-"song" videos
    if not match_found():
        log('Not found; checking for close match...')
        for song in video_results[:5]:
            if compare_media(reference, song, ignore_artist=True, ignore_album=True):
                log('Video match found.')
                match = song
                break
    
    if not match_found():
        log('No match. Setting unsure to True.', verbose=True)
        unsure = True

    # Make new dict with more relevant information
    results = {}
    # Determine what to queue
    if match_found():
        # Return match
        log('Returning match.', verbose=True)
        return trim_track_data(match) # TODO: Check what's actually going on here
    else:
        log('Creating results dictionary...', verbose=True)
        song_choices = 2
        video_choices = 2
        position = 0
        for result in song_results[:song_choices]:
            results[position] = trim_track_data(result,album=result['album']['name'])
            position += 1

        for result in video_results[:video_choices]:
            results[position] = trim_track_data(result)
            position += 1

        # Ask for confirmation if no exact match found
        if unsure:
            log('Returning as unsure.')
            return 'unsure', results

def analyze_track(url: str) -> tuple:
    # TODO: Rewrite with MediaInfo objects
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
    hours = int(ms/(1000*60*60))
    minutes = int(ms/(1000*60)%60)
    seconds = int(ms/1000%60)

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

# Other
def is_jp(text: str) -> bool:
    # TODO: Test this
    print('!!! is_jp() called')
    return re.search(r'([\p{IsHan}\p{IsBopo}\p{IsHira}\p{IsKatakana}]+)', text)

def spyt(url: str, limit: int=20) -> dict | tuple:
    """Matches a Spotify URL with its closest match from YouTube or YTMusic"""
    track = spotify_track(url)
    result = search_ytmusic(title=track.title, artist=track.artist, album=track.album_name, isrc=track.isrc, limit=limit)
    if isinstance(result, tuple) and result[0] == 'unsure':
        log('Returning as unsure.')
        return result
    return result