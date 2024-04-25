CLIENT_ID = input('Client ID: ')
CLIENT_SECRET = input('Client secret: ')

with open('spotify_config.json', 'w', encoding='utf-8') as f:
    f.write('{\n'+
    '    "spotify":\n'+
    '    {\n'+
    f'        "client_id": "{CLIENT_ID}",\n'+
    f'        "client_secret": "{CLIENT_SECRET}"\n'+
    '    }\n'+
    '}\n'
    )

input('Saved to spotify_config.json; press ENTER to exit...')
