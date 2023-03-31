import atexit
import json
import os

import lang
import messages

DATA_FOLDER = 'data'
DATA_FILE = f'{DATA_FOLDER}/data.json'
TOKENS_FILE = f'{DATA_FOLDER}/tokens.json'
DEFAULT_CHAT = {
    "dialogue": [],
    "last_settings": [],
    "settings": {
        'auto_translator': True,
        'dan': False
    },
    "usage": -1,
    "dan_count": 0
}

os.makedirs(DATA_FOLDER, exist_ok=True)

tokens = {'telegram': '', 'openai': ''}

try:
    with open(TOKENS_FILE, 'r') as rf:
        read = rf.read()
        if read != '':
            tokens = json.loads(read)
except IOError:
    with open(TOKENS_FILE, 'w') as file:
        json.dump(tokens, file, sort_keys=True, indent=2)
    print("Insert tokens")
    exit()
if tokens['telegram'] == '' or tokens['openai'] == '':
    print("Insert tokens")
    exit()


def keys_to_int(x):
    return {int(k): v for k, v in x.items()}


data1 = {}
try:
    with open(DATA_FILE, 'r') as rf:
        read = rf.read()
        if read != '':
            data1 = json.loads(read)
except IOError:
    print(messages.init_data)


def exit_handler():
    with open(DATA_FILE, 'w') as wf:
        json.dump(data1, wf, sort_keys=True, indent=2)


atexit.register(exit_handler)


def get_data(chat_id: str):
    if chat_id not in data1:
        data1[chat_id] = DEFAULT_CHAT.copy()
    return data1[chat_id]


def get_usage(chat_id, chat_name):
    prompt_size = lang.tokens_count(messages.parse_prompt(chat_name))
    tokens_count = get_data(chat_id)['usage']
    if tokens_count == -1:
        tokens_count = prompt_size
    return prompt_size, tokens_count


def set_usage(chat_id: str, new_usage: int):
    get_data(chat_id)['usage'] = new_usage


def reset_dialogue(chat_id: str):
    get_data(chat_id)['dialogue'] = DEFAULT_CHAT['dialogue']
    get_data(chat_id)['usage'] = DEFAULT_CHAT['usage']
    get_data(chat_id)['dan_count'] = DEFAULT_CHAT['dan_count']
