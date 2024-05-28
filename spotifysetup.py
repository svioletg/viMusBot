CLIENT_ID = input('Client ID: ')
CLIENT_SECRET = input('Client secret: ')

with open('spotify_config.json', 'w', encoding='utf-8') as f:
    f.write(f"""
{
    "spotify":
    {
        "client_id": "{CLIENT_ID}",
        "client_secret": "{CLIENT_SECRET}"
    }
}

""")

input('Saved to spotify_config.json; press ENTER to exit...')
