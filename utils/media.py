"""Primarily provides methods for searching and returning 
standardized results from various sources."""

from ast import Pass
import json
import time
import traceback
from typing import Any, Literal, cast

import pytube
import regex as re
import sclib
import spotipy
import yt_dlp
from fuzzywuzzy import fuzz
from spotipy.oauth2 import SpotifyClientCredentials
from ytmusicapi import YTMusic

from utils.logging import Log
from utils.palette import Palette
import utils.configuration as config

plt = Palette()

last_logtime = time.time()

# TODO: Remove/update this for refactor
logger = Log()
log = logger.log

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

class MediaError:
    # TODO: Re-evaluate if this is needed once this file's rework is done
    """Base class for media-related exceptions."""
    class FormatError(Exception):
        pass

class MediaInfo:
    def __init__(self, source: MediaSource, info: Any):
        self.source = source
        self.info = info
        self.url: str
        self.title: str
        self.artist: str
        self.length_seconds: int
        self.album_name: str
        self.album_image: str

        if source == SPOTIFY:
            self.url            = cast(str, info['external_urls']['spotify'])
            self.title          = cast(str, info['name'])
            self.artist         = cast(str, info['artists'][0]['name'])
            self.album_name     = cast(str, info['album']['name'])
            self.album_image    = cast(str, info['images'][0]['url'])
        elif source == SOUNDCLOUD:
            self.url            = cast(str, info.permalink_url)
            self.title          = cast(str, info.title)
            self.artist         = cast(str, info.user['username']) # Gets the user that uploaded the album, not a guarantee that this is accurate
            self.album_image    = cast(str, info.artwork_url)
            self.length_seconds = int(info.duration // 1000)
        elif source == YOUTUBE:
            pass
        else:
            pass

class TrackInfo(MediaInfo):
    def __init__(self, source: MediaSource, info: Any):
        MediaInfo.__init__(self, source, info)
        self.album_name: str
        self.isrc: str

        if source == SPOTIFY:
            self.length_seconds = cast(int, info['duration_ms'] // 1000)
            self.isrc           = cast(str, info['external_ids'].get('isrc', None))
        elif source == SOUNDCLOUD:
            pass
        elif source == YOUTUBE:
            pass
        else:
            pass

class AlbumInfo(MediaInfo):
    def __init__(self, source: MediaSource, info: Any):
        MediaInfo.__init__(self, source, info)
        self.contents: list[TrackInfo] = get_group_contents(self)
        self.upc: str

        if source == SPOTIFY:
            self.length_seconds = length_of_media_list(self.contents)
            self.upc            = cast(str, info['external_ids']['upc'])
        elif source == SOUNDCLOUD:
            pass
        elif source == YOUTUBE:
            pass
        else:
            pass

class PlaylistInfo(MediaInfo):
    def __init__(self, source: MediaSource, info: Any):
        MediaInfo.__init__(self, source, info)
        self.contents: list[TrackInfo] = get_group_contents(self)
        self.length_seconds: int

        if source == SPOTIFY:
            self.length_seconds = length_of_media_list(self.contents)
        if source == SOUNDCLOUD:
            pass
        if source == YOUTUBE:
            pass

def length_of_media_list(track_list: list[TrackInfo]) -> int:
    return int(sum(track.length_seconds for track in track_list))

def get_group_contents(group_object: AlbumInfo | PlaylistInfo) -> list[TrackInfo]:
    """Retrieves a list of TrackInfo objects based on the URLs found witin an AlbumInfo or PlaylistInfo object."""
    # TODO: Make compatible with all sources
    # TODO: This can take a while, maybe find a way to report status back to bot.py?
    object_list: list[TrackInfo] = []
    track_list: list[Any] = []
    if group_object.source == SPOTIFY:
        track_list = cast(list[dict], group_object.info['tracks']['items'])
        for n, track in enumerate(track_list):
            # print(f'Getting track {n+1} out of {len(track_list)}...')
            if isinstance(group_object, AlbumInfo):
                object_list.append(TrackInfo(SPOTIFY, cast(dict, sp.track(track['external_urls']['spotify']))))
            elif isinstance(group_object, PlaylistInfo):
                object_list.append(TrackInfo(SPOTIFY, cast(dict, sp.track(track['track']['external_urls']['spotify']))))
        return object_list

    if group_object.source == SOUNDCLOUD:
        track_list = group_object.info.tracks
        for track in track_list:
            object_list.append(TrackInfo(SOUNDCLOUD, track))
        return object_list

    if group_object.source == YOUTUBE:
        pass

#endregion

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

ytdl = yt_dlp.YoutubeDL(ytdl_format_options)

#region API CONNECTIONS

# Connect to youtube music API
ytmusic = YTMusic()

# Connect to spotify API
with open('spotify_config.json', 'r', encoding='utf-8') as f:
    scred = json.loads(f.read())['spotify']

client_credentials_manager = SpotifyClientCredentials(
    client_id = scred['client_id'],
    client_secret = scred['client_secret']
)
sp = spotipy.Spotify(client_credentials_manager = client_credentials_manager)

# Connect to soundcloud API
sc = sclib.SoundcloudAPI()

#endregion

# SoundCloud
def soundcloud_set(url: str) -> PlaylistInfo | AlbumInfo:
    """Retrieves a SoundCloud set and returns either a PlaylistInfo or AlbumInfo where applicable."""
    # Soundcloud playlists and albums use the same URL format, a set
    response: Any = sc.resolve(url)
    return AlbumInfo(SOUNDCLOUD, response.tracks) if response.is_album \
        else PlaylistInfo(SOUNDCLOUD, response.tracks)

# Spotify
def spotify_track(url: str) -> TrackInfo | Exception:
    """Retrieves a Spotify track and returns it as a TrackInfo object.

    Returns a SpotifyException if retrieval fails."""
    try:
        track: dict = cast(dict, sp.track(url))
    except spotipy.exceptions.SpotifyException as e:
        log(f'Failed to retrieve Spotify track: {e}')
        return e

    return TrackInfo(source = SPOTIFY, info = track)

def spotify_playlist(url: str) -> PlaylistInfo | Exception:
    """Retrieves a Spotify track and returns it as a PlaylistInfo object.

    Returns a SpotifyException if retrieval fails."""
    try:
        playlist: dict = cast(dict, sp.playlist(url))
    except spotipy.exceptions.SpotifyException as e:
        log(f'Failed to retrieve Spotify playlist: {e}')
        return e

    return PlaylistInfo(source = SPOTIFY, info = playlist)

def spotify_album(url: str) -> AlbumInfo | Exception:
    """Retrieves a Spotify track and returns it as a AlbumInfo object.

    Returns a SpotifyException if retrieval fails."""
    try:
        album: dict = cast(dict, sp.album(url))
    except spotipy.exceptions.SpotifyException as e:
        log(f'Failed to retrieve Spotify album: {e}')
        return e

    return AlbumInfo(source = SPOTIFY, info = album)

# For analyze()
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

### SETUP FINISH

# Define matching logic
def is_matching(reference: dict, ytresult: dict,
                mode: Literal['fuzz', 'strict'] = 'fuzz',
                threshold: int = 75, 
                ignore_title: bool = False, 
                ignore_artist: bool = False, 
                ignore_album: bool = False,
                **kwargs) -> bool:
    # TODO: Review this!
    # mode is how exactly the code will determine a match
    # 'fuzz' = fuzzy matching, by default returns a match with a ratio of >75
    # 'strict' = checking for strings in other strings, how matching was done beforehand

    # overrides the fuzzy matching threshold, default is 75%
    title_threshold = kwargs.get('title_threshold', threshold)
    artist_threshold = kwargs.get('artist_threshold', threshold)
    album_threshold = kwargs.get('album_threshold', threshold)

    ref_title, ref_artist, ref_album = reference['title'], reference['artist'], reference['album']
    yt_title, yt_artist = ytresult['title'], ytresult['artists'][0]['name']
    try:
        yt_album = ytresult['album']['name']
    except Exception as e:
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

    return (matching_title or ignore_title) \
        and (matching_artist or ignore_artist) \
        and (matching_album or ignore_album) \
        and (alternate_check)

# Youtube
def pytube_track_data(pytube_object: pytube.YouTube) -> dict:
    # This must be done in order for the description to load in
    try:
        pytube_object.bypass_age_gate()
        description_list = pytube_object.description.split('\n')
    except Exception as e:
        log(f'pytube description retrieval failed; using ytdl...', verbose=True)
        log(f'Cause of the above: {e}')
        ytdl_info = ytdl.extract_info(pytube_object.watch_url)
        if not ytdl_info:
            raise ValueError('ytdl.extract_info() returned None.')
        description_list: list[str] = ytdl_info['description'].split('\n')

    if 'Provided to YouTube by' not in description_list[0]:
        # This function won't work if it doesn't follow the auto-generated template on most official song uploads
        raise VimusbotErrors.FormattingError(f'{plt.warn} Unexpected description formatting. URL: {pytube_object.watch_url}')

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

def search_ytmusic_text(query: str) -> tuple:
    """Searches YTMusic with a plain-text query."""
    try:
        top_song = ytmusic.search(query=query, limit=1, filter='songs')[0]
    except IndexError:
        top_song = None

    try:
        top_video = ytmusic.search(query=query, limit=1, filter='videos')[0]
    except IndexError:
        top_video = None

    return top_song, top_video

def search_ytmusic_album(title: str, artist: str, year: str, upc: str='') -> str|None:
    if FORCE_NO_MATCH:
        log(f'{plt.warn}force_no_match is set to True.'); return None

    query = f'{title} {artist} {year}'
    
    log('Starting album search...', verbose=True)
    check = re.compile(r'(\(feat\..*\))|(\(.*Remaster.*\))')

    album_results = ytmusic.search(query=query, limit=5, filter='albums')
    for yt in album_results:
        title_match = fuzz.ratio(check.sub('', title), check.sub('', yt['title'])) > 75
        artist_match = fuzz.ratio(artist, yt['artists'][0]['name']) > 75
        year_match = fuzz.ratio(year, yt['year']) > 75
        if title_match + artist_match + year_match >= 2:
            log('Match found.', verbose=True)
            return 'https://www.youtube.com/playlist?list='+ytmusic.get_album(yt['browseId'])['audioPlaylistId']
    
    song_results = ytmusic.search(query=query,limit=5,filter='songs')
    for yt in song_results:
        title_match = fuzz.ratio(check.sub('', title), check.sub('', yt['album']['name'])) > 75
        artist_match = fuzz.ratio(artist, yt['artists'][0]['name']) > 75
        year_match = fuzz.ratio(year, yt['year']) > 75
        if title_match + artist_match + year_match >= 2:
            log('Match found.', verbose=True)
            return 'https://www.youtube.com/playlist?list='+ytmusic.get_album(yt['album']['id'])['audioPlaylistId']
    
    log('No match found.', verbose=True)
    return None

# Trim ytmusic song data down to what's relevant to us
def trim_track_data(data: dict|object, album: str='', is_pytube_object: bool=False) -> dict:
    if is_pytube_object:
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

def search_ytmusic(title: str, artist: str, album: str, isrc: str=None, limit: int=10, fast_search: bool=False):
    unsure = False

    query = f'{title} {artist} {album}'
    reference = {'title':title, 'artist':artist, 'album':album, 'isrc':isrc}

    # Start search
    if isrc is not None and not FORCE_NO_MATCH:
        log(f'Searching for ISRC: {isrc}', verbose=True)
        # For whatever reason, pytube seems to be more accurate here
        isrc_matches = pytube.Search(isrc).results
        for song in isrc_matches:
            if fuzz.ratio(song.title, reference['title']) > 75:
                log('Found an ISRC match.', verbose=True)
                return trim_track_data(song, is_pytube_object=True)
            
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
        if is_matching(reference, song, ignore_artist=True):
            log('Song match found.')
            match = song
            break

    # Next, try standard non-"song" videos
    if not match_found():
        log('Not found; checking for close match...')
        for song in video_results[:5]:
            if is_matching(reference, song, ignore_artist=True, ignore_album=True):
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
        return trim_track_data(match)
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
    title = sp.track(url)['name']
    artist = sp.track(url)['artists'][0]['name']
    data = sp.audio_features(url)[0]

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
    return re.search(r'([\p{IsHan}\p{IsBopo}\p{IsHira}\p{IsKatakana}]+)', text)

def spyt(url: str, limit: int=20, **kwargs) -> dict|tuple:
    """Matches a Spotify URL with its closest match from YouTube or YTMusic"""
    track = spotify_track(url)
    result = search_ytmusic(title=track['title'], artist=track['artist'], album=track['album'], isrc=track['isrc'], limit=limit, **kwargs)
    if isinstance(result, tuple) and result[0] == 'unsure':
        log('Returning as unsure.')
        return result
    return result