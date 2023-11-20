import json
import os
import sys
import time
import traceback
from inspect import currentframe, getframeinfo

import colorama
import pytube
import regex as re
import sclib
import spotipy
import yaml
import yt_dlp
from benedict import benedict
from colorama import Back, Fore, Style
from fuzzywuzzy import fuzz
from spotipy.oauth2 import SpotifyClientCredentials
from ytmusicapi import YTMusic

# Local files
import customlog
from palette import Palette

_here = os.path.basename(__file__)

# Personal debug logging
colorama.init(autoreset=True)
plt = Palette()

last_logtime = time.time()

def log(msg: str, verbose=False):
    global last_logtime
    customlog.newlog(msg=msg, last_logtime=last_logtime, called_from=sys._getframe().f_back.f_code.co_name, verbose=verbose)
    last_logtime = time.time()

def log_line():
    cf = currentframe()
    print('@ LINE ', cf.f_back.f_lineno)

# Parse config from YAML
with open('config_default.yml','r') as f:
    config_default = benedict(yaml.safe_load(f))

with open('config.yml','r') as f:
    config = benedict(yaml.safe_load(f))

FORCE_NO_MATCH         : bool = config.get('force-no-match', config_default['force-no-match'])
SPOTIFY_PLAYLIST_LIMIT : int  = config.get('spotify-playlist-limit', config_default['spotify-playlist-limit'])
DURATION_LIMIT         : int  = config.get('duration-limit', config_default['duration-limit'])

# Useful to point this out if left on accidentally
if FORCE_NO_MATCH:
    log(f'{plt.warn}NOTICE: force_no_match is set to True.')

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

# API Objects

# Connect to youtube music API
ytmusic = YTMusic()

# Connect to spotify API
with open('spotify_config.json', 'r') as f:
    scred = json.loads(f.read())['spotify']

client_credentials_manager = SpotifyClientCredentials(
    client_id=scred['client_id'],
    client_secret=scred['client_secret']
)
sp = spotipy.Spotify(client_credentials_manager = client_credentials_manager)

# Connect to soundcloud API
sc = sclib.SoundcloudAPI()

# For analyze()
keytable = {
    0: 'C major or A minor',
    1: 'C#/Db major or A#/Bb minor',
    2: 'D major or B minor',
    3: 'D#/Eb major or C minor',
    4: 'E major or C#/Db minor',
    5: 'F major or D minor',
    6: 'F#/Gb major or D#/Eb minor',
    7: 'G major or E minor',
    8: 'G#/Ab major or F minor',
    9: 'A major or F#/Gb minor',
    10: 'A#/Bb major or G minor',
    11: 'B major or G#/Ab minor',
}

### SETUP FINISH

# Define matching logic
def is_matching(reference: dict, ytresult: dict, mode='fuzz', **kwargs) -> bool:
    # mode is how exactly the code will determine a match
    # 'fuzz' = fuzzy matching, by default returns a match with a ratio of >75
    # 'strict' = checking for strings in other strings, how matching was done beforehand
    if mode not in ['fuzz', 'strict']: 
        log(f'{mode} is not a valid mode.')
        return

    # overrides the fuzzy matching threshold, default is 75%
    threshold = kwargs.get('threshold',75)
    title_threshold = kwargs.get('title_threshold',threshold)
    artist_threshold = kwargs.get('artist_threshold',threshold)
    album_threshold = kwargs.get('album_threshold',threshold)

    ignore_title = kwargs.get('ignore_title', False)
    ignore_artist = kwargs.get('ignore_artist', False)
    ignore_album = kwargs.get('ignore_album', False)

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
def isrc_search_test(playlist):
    # For testing, generally not a useful function
    tracks = spotify_playlist(playlist)
    yes=0
    no=0
    log('STARTING')
    for i in tracks:
        isrc = i['isrc']
        # For whatever reason, pytube seems to be more accurate here
        isrc_match = pytube.Search(isrc).results
        for match in isrc_match:
            print(Fore.CYAN+i['title']+f'{plt.reset} ... {plt.warn}'+match.title)
            if fuzz.ratio(match.title, i['title']) > 75:
                log(f'{plt.green} {tracks.index(i)+1}/{len(tracks)}: Cleared. {isrc}')
                yes+=1
                break
            elif isrc_match.index(match)==len(isrc_match)-1:
                no+=1
                log(f'{plt.error} {tracks.index(i)+1}/{len(tracks)}: Not cleared. {isrc}')
    log(f'{yes} successes / {no} fails')

def pytube_track_data(pytube_object: pytube.YouTube) -> dict:
    # This must be done in order for the description to load in
    try:
        pytube_object.bypass_age_gate()
        description_list = pytube_object.description.split('\n')
    except Exception as e:
        log(f'pytube description retrieval failed; using ytdl...', verbose=True)
        log(f'Cause of the above: {e}')
        description_list = ytdl.extract_info(pytube_object.watch_url)['description'].split('\n')

    if 'Provided to YouTube by' not in description_list[0]:
        # This function won't work if it doesn't follow the auto-generated template on most official song uploads
        log(f'{plt.warn} Unexpected description formatting. URL: {pytube_object.watch_url}')
        return None

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
    # For plain-text searching
    try:
        top_song = ytmusic.search(query=query, limit=1, filter='songs')[0]
    except IndexError:
        top_song = None

    try:
        top_video = ytmusic.search(query=query, limit=1, filter='videos')[0]
    except IndexError:
        top_video = None

    return top_song, top_video

def search_ytmusic_album(title: str, artist: str, year: str, upc: str=None) -> str|None:
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

# SoundCloud
def soundcloud_playlist(url: str) -> list:
    playlist = sc.resolve(url).tracks
    return playlist

# Spotify
def get_uri(url: str) -> str:
    return url.split("/")[-1].split("?")[0]

def spotify_playlist(url: str) -> list:
    playlist = sp.playlist(url)['tracks']['items']
    newlist = []
    for item in playlist:
        newlist.append({
            'title': item['track']['name'],
            'artist': item['track']['artists'][0]['name'],
            'album': item['track']['album']['name'],
            'isrc': item['track']['external_ids'].get('isrc', None),
            'url': item['track']['external_urls']['spotify'],
            'duration': round(item['track']['duration_ms'] / 1000)
        })
    return newlist

def spotify_track(url: str) -> dict:
    info = sp.track(url)
    return {
        'title': info['name'],
        'artist': info['artists'][0]['name'],
        'album': info['album']['name'],
        'isrc': info['external_ids'].get('isrc', None),
        'url': info['external_urls']['spotify'],
        'duration': round(info['duration_ms'] / 1000)
    }

def spotify_album(url: str) -> dict:
    info = sp.album(url)
    return {
        'title':info['name'], 
        'artist':info['artists'][0]['name'],
        'year':info['release_date'].split('-')[0],
        'upc':info['external_ids']['upc']
    }

def analyze_track(url: str) -> tuple:
    uri = get_uri(url)
    title = sp.track(uri)['name']
    artist = sp.track(uri)['artists'][0]['name']
    data = sp.audio_features(uri)[0]

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
    if type(result) == tuple and result[0] == 'unsure':
        log('Returning as unsure.')
        return result
    return result