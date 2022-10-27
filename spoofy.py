import json
import spotipy
from spotipy import SpotifyClientCredentials
from discord import Embed
from datetime import datetime
from inspect import currentframe, getframeinfo
from ytmusicapi import YTMusic

### TODO

debug=True
def logln():
	cf = currentframe()
	if debug: print('@ LINE ', cf.f_back.f_lineno)

def log(msg):
	if debug:
		print('[ spoofy.py ] '+msg)

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

# Youtube
def searchYT(**kwargs):
	query=''
	limit=5
	unsure=False

	if 'title' not in kwargs:
		print('spoofy.searchYT: "title" was not passed, aborting.')
		return False

	# Process kwargs
	title=kwargs['title']
	query+=title
	artist=kwargs['artist']
	query+=' '+artist
	if 'limit' in kwargs:
		limit=kwargs['limit']

	# Start search
	log(f'searchYT: Trying query \"{query}\" with a limit of {limit}')
	search_out=ytmusic.search(query=query,limit=limit,filter='songs')
	top=search_out[0]
	log('Checking for exact match...')
	# SET TO FALSE BEFORE GENERAL USE!
	force_no_match=False

	def is_matching(item):
		matchingArtist = artist.lower() in item['artists'][0]['name'].lower()
		matchingTitle = title.lower() in item['title'].lower() or (title.split(' - ')[0].lower() in item['title'].lower() and title.split(' - ')[1].lower() in item['title'].lower())
		desired = 'remix' in title.lower()
		found = 'remix' in item['title'].lower()
		remixcheck = False
		if (desired and found) or (not desired and not found):
			remixcheck=True
		else:
			remixcheck=False
		return (matchingArtist) and (matchingTitle) and (remixcheck)

	# Try user-uploaded videos if no song found
	if not is_matching(top) or force_no_match:
		log('Not found; checking for close match...')
		search_out=ytmusic.search(query=query,limit=limit,filter='videos')
		top=search_out[0]

		# If no close match is found, pass to the user
		if not is_matching(top) or force_no_match:
			log('Not found; marking for unsure.')
			unsure=True
		else:
			log('Close match check passed.')

	# Make new dicts with more relevant information
	results={}
	log('Creating results dictionary...')
	for result in search_out:
		results[search_out.index(result)] = {
		'title': result['title'],
		'artist': result['artists'][0]['name'],
		'url': 'https://www.youtube.com/watch?v='+result['videoId'],
		'duration': result['duration'],
		}

	# Ask for confirmation if no exact match found
	if unsure:
		log('searchYT is returning as unsure.')
		return 'unsure', results

	# Return top result if not specified otherwise
	if 'all' in kwargs:
		if kwargs['all']:
			return results
	else:
		return results[0]

# Spotify
def getURI(url):
	return url.split("/")[-1].split("?")[0]

def trackinfo(url):
	uri=getURI(url)
	info=sp.track(uri)
	title=info['name']
	# Only retrieves the first artist name
	artist=info['artists'][0]['name']
	return title, artist

def analyzetrack(url):
	uri=getURI(url)
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
	track=trackinfo(url)
	limit=5
	if 'limit' in kwargs:
		limit=kwargs['limit']

	result = searchYT(title=track[0],artist=track[1],limit=limit,**kwargs)
	if type(result)==tuple and result[0]=='unsure':
		log('spyt is returning as unsure.')
		return result
	return result