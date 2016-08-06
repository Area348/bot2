import requests
url = 'https://mattijnkreuzen.nl/tg_users/telegramusers.php'


def authenticate_chat(tg_user_id, chat_id, SLEUTEL, username="unkown", chat_naam="unkown"):
    data = {
        'tg_user_id': tg_user_id,
        'chat_id': chat_id,
        'SLEUTEL': SLEUTEL,
        'username': username,
        'chat_naam': chat_naam
    }
    r = requests.post(url=url, json=data)
    json = r.json()
    return json['verified']
