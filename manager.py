import atexit
import json
import os

import lang
import messages

DATA_FOLDER = 'data'
DATA_FILE = f'{DATA_FOLDER}/data.json'
TOKENS_FILE = f'{DATA_FOLDER}/tokens.json'
DEFAULT_CHAT = {
    'name': "",
    'dialogue': [],
    'last_settings': [],
    'settings': {
        'auto_translator': True,
        'dgpt': False
    },
    'usage': -1,
    'dan_count': 0
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


data = {}
try:
    with open(DATA_FILE, 'r') as rf:
        read = rf.read()
        if read != '':
            data = json.loads(read)
except IOError:
    print(messages.init_data)


def exit_handler():
    with open(DATA_FILE, 'w') as wf:
        json.dump(data, wf, sort_keys=True, indent=2)


atexit.register(exit_handler)


def fill_default(default: dict, to_fill: dict):
    for key in default:
        if key not in to_fill:
            to_fill[key] = default[key]
        elif isinstance(default[key], dict):
            fill_default(default[key], to_fill[key])


def clear_if_not_exist(default: dict, to_clear: dict):
    clear_keys = []
    for key in to_clear:
        if key not in default:
            clear_keys.append(key)
        elif isinstance(to_clear[key], dict):
            clear_if_not_exist(default[key], to_clear[key])
    for key in clear_keys:
        del to_clear[key]


def get_data(chat_id: str):
    default = DEFAULT_CHAT.copy()
    if chat_id not in data:
        data[chat_id] = default
    clear_if_not_exist(default, data[chat_id])
    fill_default(default, data[chat_id])
    return data[chat_id]


def get_usage(chat_id, chat_name, is_group):
    prompt_size = lang.tokens_count(messages.parse_prompt(chat_name, is_group))
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
