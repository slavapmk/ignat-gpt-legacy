import atexit
import json
import os

import lang
import messages

DATA_FOLDER = 'data'
DATA_FILE = f'{DATA_FOLDER}/data.json'
TOKENS_FILE = f'{DATA_FOLDER}/tokens.json'
DEFAULT_SETTINGS = {
    'auto_translator': True,
    'dan': False
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


# data = {}
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


def get_dialogue(chat_id: str):
    return data[chat_id]['dialogue']


def get_usage(chat_id, chat_name):
    prompt_size = lang.tokens_count(messages.parse_prompt(chat_name))
    if chat_id in data and 'usage' in data[chat_id]:
        tokens_count = data[chat_id]['usage']
    else:
        tokens_count = prompt_size
    return prompt_size, tokens_count


def set_usage(chat_id: str, new_usage: int):
    data[chat_id]['usage'] = new_usage


def reset_dialogue(chat_id: str):
    if chat_id in data:
        if 'dialogue' in data[chat_id]:
            del data[chat_id]['dialogue']
        if 'usage' in data[chat_id]:
            del data[chat_id]['usage']


def init_new_client(chat_id: str):
    data[chat_id] = {'settings': DEFAULT_SETTINGS.copy()}
