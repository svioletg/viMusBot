import spotipy
from spotipy import SpotifyClientCredentials
from discord import Embed
from datetime import datetime
from inspect import currentframe, getframeinfo

debug=False
def logln():
	cf = currentframe()
	if debug: print('@ LINE ', cf.f_back.f_lineno)

def log(msg):
	if debug:
		print(msg)

# Set up spotify
creds = open('spotify.txt').read().split('\n')
spotid = creds[0]
spotsecret = creds[1]
client_credentials_manager = SpotifyClientCredentials(client_id=spotid,client_secret=spotsecret)
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

def getURI(url):
	return url.split("/")[-1].split("?")[0]

def analyzetrack(url):
	uri=getURI(url)
	title=sp.track(uri)['name']
	artist=sp.track(uri)['artists'][0]['name']
	data=sp.audio_features(uri)[0]

	embed=Embed(title=f'Spotify data for {title} by {artist}', description='Things like key, tempo, and time signature are estimated, and therefore not necessarily accurate.', color=0x00FF00)

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
	embed.add_field(name='Key',value=data['key'])
	data.pop('key')
	embed.add_field(name='Tempo',value=data['tempo'])
	data.pop('tempo')
	embed.add_field(name='Time Signature',value=data['time_signature'])
	data.pop('time_signature')

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
		log(i)
		log(data[i])
		log(value)
		embed.add_field(name=i.title(),value=value)

	return embed