import atexit
import json
import logging
import os
import time

import openai
from aiogram import Bot, Dispatcher, types
from aiogram.utils import executor
from aiogram.utils.exceptions import CantParseEntities
from openai.error import OpenAIError

import lang
import messages

DATA_FOLDER = 'data'
DATA_FILE = f'{DATA_FOLDER}/data.json'
TOKENS_FILE = f'{DATA_FOLDER}/tokens.json'

os.makedirs(DATA_FOLDER, exist_ok=True)

tokens = {'telegram': '', 'openai': ''}

try:
    with open(TOKENS_FILE, 'r') as rf:
        read = rf.read()
        if read != '':
            tokens = json.loads(read)
except IOError:
    with open(TOKENS_FILE, 'w') as file:
        json.dump(tokens, file, sort_keys=True, indent=4)
    print("Insert tokens")
    exit()
if tokens['telegram'] == '' or tokens['openai'] == '':
    print("Insert tokens")
    exit()

logging.basicConfig(level=logging.INFO)
bot = Bot(token=tokens['telegram'])
openai.api_key = tokens['openai']
dp = Dispatcher(bot)


def keys_to_int(x):
    return {int(k): v for k, v in x.items()}


dialogues = {}
usages = {}
prompt_sizes = {}
try:
    with open(DATA_FILE, 'r') as rf:
        read = rf.read()
        if read != '':
            data = json.loads(read)
            dialogues = data['dialogues']
            usages = data['usage']
            prompt_sizes = data['prompt_sizes']
except IOError:
    print(messages.init_data)


def exit_handler():
    with open(DATA_FILE, 'w') as wf:
        json.dump({'dialogues': dialogues, 'usage': usages, 'prompt_sizes': prompt_sizes},
                  wf, sort_keys=True, indent=4)


atexit.register(exit_handler)


@dp.message_handler(commands=['start', 'help'])
async def send_welcome(message: types.Message):
    await message.reply(messages.help_message, parse_mode="Markdown", disable_web_page_preview=True)


@dp.message_handler(commands=['reset'])
async def reset(message: types.Message):
    if str(message.chat.id) in dialogues:
        del dialogues[str(message.chat.id)]
    if str(message.chat.id) in usages:
        del usages[str(message.chat.id)]
    if str(message.chat.id) in prompt_sizes:
        del prompt_sizes[str(message.chat.id)]
    await message.reply(messages.clear_dialogues_message)


@dp.message_handler(commands=['query'])
async def group(message: types.Message):
    await process(message, message.get_args())


@dp.message_handler(commands=['nt'])
async def group(message: types.Message):
    await process(message, message.get_args(), False)


@dp.message_handler(commands=['tokens'])
async def group(message: types.Message):
    tokens_count = 0
    if str(message.chat.id) in usages:
        tokens_count = usages[str(message.chat.id)]
    if str(message.chat.id) in prompt_sizes:
        prompt_size = prompt_sizes[str(message.chat.id)]
    else:
        prompt = messages.ai_prompt + f"\nUser's name is \"{message.chat.full_name}\""
        prompt_size = lang.tokens_count(prompt)
        tokens_count = prompt_size
    await message.reply(
        await messages.tokens_command_message(tokens_count, prompt_size),
        parse_mode="Markdown")


@dp.message_handler()
async def process_pm(message: types.Message):
    if message.chat.type == 'private':
        await process(message, message.text)
    elif message.chat.type == 'group' or message.chat.type == 'super_group' or message.chat.type == 'supergroup':
        if message.text.startswith(f'{messages.name_russian}, ') or message.text.startswith(
                f'{messages.name_english}, '):
            await process(message, message.text[7:])


async def process(message: types.Message, text: str, auto_translate=True):
    text = text.strip()
    await message.chat.do(action='typing')
    if text == '':
        await message.reply(messages.empty_query)
        return
    if lang.is_russian(text) and auto_translate:
        if len(text) >= 500:
            await message.reply(messages.long_query)
            return
        text = lang.translate(text, "ru|en")

    if str(message.chat.id) not in dialogues:
        prompt = messages.ai_prompt + f"\nUser's name is \"{message.chat.full_name}\""
        prompt_sizes[str(message.chat.id)] = lang.tokens_count(prompt)
        dialogues[str(message.chat.id)] = [{"role": "system", "content": prompt}]
    dialogues[str(message.chat.id)].append({"role": "user", "content": text})
    first = True
    retry = False
    i = 1
    response_text = ''
    while first or retry:
        if not first:
            time.sleep(5)
        first = False
        await message.chat.do(action='typing')
        try:
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=dialogues[str(message.chat.id)]
            )
            retry = False
            usages[str(message.chat.id)] = response['usage']['total_tokens']
            response_text = response['choices'][0]['message']['content']
        except OpenAIError:
            retry = True
            i += 1

    send_text = response_text.strip()
    dialogues[str(message.chat.id)].append({"role": "assistant", "content": send_text})
    try:
        await message.reply(send_text, parse_mode='Markdown', allow_sending_without_reply=True,
                            disable_web_page_preview=True)
    except CantParseEntities:
        await message.reply(messages.cant_send_with_fonts, allow_sending_without_reply=True,
                            disable_web_page_preview=True)
        await message.answer(send_text)
        print(messages.parse_error)


if __name__ == '__main__':
    executor.start_polling(dp)
