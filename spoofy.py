import time
import sys
import os
import json
import spotipy
import colorama
from colorama import Fore, Back, Style
from palette import Palette
from spotipy import SpotifyClientCredentials
from discord import Embed
from datetime import datetime
from inspect import currentframe, getframeinfo
from ytmusicapi import YTMusic

_here = os.path.basename(__file__)

### TODO

# Personal debug logging
colorama.init(autoreset=True)
plt = Palette()

logtimeA = time.time()
logtimeB = time.time()

print_logs='quiet' not in sys.argv

def logln():
	cf = currentframe()
	if print_logs: print('@ LINE ', cf.f_back.f_lineno)

def log(msg):
	global logtimeA
	global logtimeB
	logtimeB = time.time()
	elapsed = logtimeB-logtimeA
	called_from = ' '+sys._getframe().f_back.f_code.co_name+':'
	if called_from==' <module>:': called_from=''
	if print_logs:
		print(f'{plt.file[_here]}[ {_here} ]{plt.reset}{plt.func}{called_from}{plt.reset} {msg}{plt.reset} {plt.timer} {round(elapsed,3)}s')
	logtimeA = time.time()

log('Imported.')

force_no_match=False
if 'fnm' in sys.argv: force_no_match=True
if force_no_match: log(f'{plt.warn}force_no_match is set to True.')

# Connect to youtube music API
ytmusic = YTMusic()

# Connect to spotify API
scred = json.loads(open('config.json').read())['spotify']
client_credentials_manager = SpotifyClientCredentials(client_id=scred['client_id'], client_secret=scred['client_secret'])
sp = spotipy.Spotify(client_credentials_manager = client_credentials_manager)

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

# Define matching logic
def is_matching(reference,ytresult,**kwargs):
	title=reference[0]
	artist=reference[1]
	album=reference[2]
	if 'ignore_album' in kwargs: matching_album = True; log('Ignoring album match.')
	else: matching_album = album.lower() in ytresult['album']['name'].lower()
	if 'ignore_artist' in kwargs: matching_artist = True; log('Ignoring artist match.')
	else: matching_artist = artist.lower() in ytresult['artists'][0]['name'].lower()
	matching_title = title.lower() in ytresult['title'].lower() or (title.split(' - ')[0].lower() in ytresult['title'].lower() and title.split(' - ')[1].lower() in ytresult['title'].lower())
	# Do not count tracks that are specific/alternate version,
	# unless said keyword matches the original Spotify title
	alternate_desired = any(i in title.lower() for i in ['remix', 'cover', 'version'])
	alternate_found = any(i in ytresult['title'].lower() for i in ['remix', 'cover', 'version'])
	alternate_check = False
	alternate_check = (alternate_desired and alternate_found) or (not alternate_desired and not alternate_found)
	return (matching_album) and (matching_artist) and (matching_title) and (alternate_check)

# Youtube
def search_ytmusic_text(query, **kwargs):
	# For plain-text searching
	top_song=ytmusic.search(query=query,limit=1,filter='songs')[0]
	top_video=ytmusic.search(query=query,limit=1,filter='songs')[0]
	return top_song, top_video

def search_ytmusic(title, artist, album, **kwargs):
	global force_no_match
	unsure=False

	# Process kwargs
	reference=[title, artist, album]
	query=f'{title} {album}'
	# The search limit doesn't actually seem to work, investigate this
	limit=20
	if 'limit' in kwargs: limit=kwargs['limit']
	from_playlist=False
	if 'from_playlist' in kwargs: from_playlist = kwargs['from_playlist']

	# Start search
	log(f'Trying query \"{query}\" with a limit of {limit}')
	search_out=ytmusic.search(query=query,limit=limit,filter='songs')
	# Remove videos over a certain length
	duration_limit = 5 # in hours
	for i in search_out:
		if int(i['duration_seconds'])>duration_limit*60*60: search_out.pop(search_out.index(i))

	log('Checking for exact match...')
	if force_no_match: log(f'{plt.warn}force_no_match is set to True.')

	# Check for matches
	match=None
	def match_found():
		return match!=None and not force_no_match

	for i in search_out[:5]:
		if is_matching(reference,i,ignore_artist=True):
			log('Song match found.')
			match=i
			break

	if not match_found():
		log('Not found; checking for close match...')
		# Check user-uploaded videos
		search_out=ytmusic.search(query=query,limit=limit,filter='videos')
		for i in search_out:
			if int(i['duration_seconds'])>duration_limit*60*60: search_out.pop(search_out.index(i))
		# If no close match is found, pass to the user
		for i in search_out[:5]:
			if is_matching(reference,i,ignore_artist=True,ignore_album=True):
				log('Video match found.')
				match=i
				break

	if not match_found() and not from_playlist:
		# Do not prompt for confirmation in the middle of queuing a playlist
		log('No match. Returning unsure.')
		unsure=True

	# Make new dict with more relevant information
	results={}
	try:
		if match_found():
			match={
				'title': search_out[search_out.index(match)]['title'],
				'artist': search_out[search_out.index(match)]['artists'][0]['name'],
				'url': 'https://www.youtube.com/watch?v='+search_out[search_out.index(match)]['videoId'],
				'duration': search_out[search_out.index(match)]['duration'],
			}
			# Return match
			log('Returning match.')
			return match
		else:
			log('Creating results dictionary...')
			for result in search_out:
				results[search_out.index(result)] = {
				'title': result['title'],
				'artist': result['artists'][0]['name'],
				'url': 'https://www.youtube.com/watch?v='+result['videoId'],
				'duration': result['duration'],
				}
		
			# Ask for confirmation if no exact match found
			if from_playlist:
				# Don't prompt for confirmation for playlist items
				# Will select the top result
				return results[0]
			if unsure:
				log('Returning as unsure.')
				return 'unsure', results
	except Exception as e:
		print(e)
		raise e

# Spotify
def get_uri(url):
	return url.split("/")[-1].split("?")[0]

def track_info(url):
	uri=get_uri(url)
	info=sp.track(uri)
	title=info['name']
	# Only retrieves the first artist name
	artist=info['artists'][0]['name']
	album=info['album']['name']
	return title, artist, album

def playlist_info(url, kind):
	if kind=='playlist': info=sp.playlist_items(url)
	if kind=='album': info=sp.album_tracks(url)
	tracks=[]
	for i in info['items']:
		if kind=='playlist': i=i['track']
		tracks.append([i['name'], i['artists'][0]['name']])
	return tracks

def analyze_track(url):
	uri=get_uri(url)
	title=sp.track(uri)['name']
	artist=sp.track(uri)['artists'][0]['name']
	data=sp.audio_features(uri)[0]

	embed=Embed(title=f'Spotify data for {title} by {artist}', description='Things like key, tempo, and time signature are estimated, and therefore not necessarily accurate.', color=0x00FF00)

	# Nicer formatting
	data['tempo']=str(int(data['tempo']))+'bpm'
	data['key']=keytable[data['key']]
	data['time_signature']=str(data['time_signature'])+'/4'
	data['loudness']=str(data['loudness'])+'dB'

	# Replace ms duration with readable duration
	ms=data['duration_ms']
	hours = int(ms/(1000*60*60))
	minutes = int(ms/(1000*60)%60)
	seconds = int(ms/1000%60)

	# Don't include hours if less than one
	hours=str(hours)
	hours+=':'
	if float(hours[:-1])<1:
		hours=''
	length = f'{hours}{minutes}:{seconds:02d}'
	data['duration']=length
	data.pop('duration_ms')

	# Ignore technical/non-useful information
	skip=['type', 'id', 'uri', 'track_href', 'analysis_url', 'mode']

	# Assemble embed object
	# Put key, time sig, and tempo at the top
	embed.add_field(name='Key',value=data['key']); data.pop('key')
	embed.add_field(name='Tempo',value=data['tempo']); data.pop('tempo')
	embed.add_field(name='Time Signature',value=data['time_signature']); data.pop('time_signature')

	# Add the rest
	for i in data:
		if i in skip:
			continue

		value=data[i]
		# Change decimals to percentages
		# Exclude loudness
		if type(data[i])==int or type(data[i])==float:
			if data[i]<1 and i!='loudness':
				value=str(round(data[i]*100,2))+'%'

		value=str(value)
		embed.add_field(name=i.title(),value=value)

	return embed

def spyt(url, **kwargs):
	log('spyt() called.')
	limit=20
	if 'limit' in kwargs:
		limit=kwargs['limit']

	if '/playlist/' in url or '/album/' in url:
		log('playlist detected')
		tracks=playlist_info(url,kind=url.split('/')[3])
		playlist=[]
		for track in tracks:
			result = search_ytmusic(title=track[0],artist=track[1],album=track[2],limit=limit,from_playlist=True,**kwargs)
			playlist.append(result)
		return playlist
	else:
		log('not a playlist')
		track=track_info(url)
		result = search_ytmusic(title=track[0],artist=track[1],album=track[2],limit=limit,**kwargs)
		if type(result)==tuple and result[0]=='unsure':
			log('Returning as unsure.')
			return result
		return result