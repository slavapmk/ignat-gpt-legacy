import atexit
import json
import logging
import time

import openai
from aiogram import Bot, Dispatcher, types
from aiogram.utils import executor
from aiogram.utils.exceptions import CantParseEntities
from openai.error import OpenAIError

import lang
import messages
import tokens

DIALOGUES_FILE = 'dialogues.json'

openai.api_key = tokens.openai_token

logging.basicConfig(level=logging.INFO)

bot = Bot(token=tokens.telegram_token)
dp = Dispatcher(bot)


def keys_to_int(x):
    return {int(k): v for k, v in x.items()}


dialogue = {}
try:
    with open(DIALOGUES_FILE, 'r') as f:
        read = f.read()
        if read != '':
            dialogue = json.loads(read, object_hook=keys_to_int)
except IOError:
    print(messages.init_message)


def exit_handler():
    with open(DIALOGUES_FILE, 'w') as file_to_save:
        json.dump(dialogue, file_to_save)


atexit.register(exit_handler)


@dp.message_handler(commands=['start', 'help'])
async def send_welcome(message: types.Message):
    await message.reply(messages.help_message, parse_mode="Markdown")


@dp.message_handler(commands=['reset'])
async def reset(message: types.Message):
    if message.chat.id in dialogue:
        del dialogue[message.chat.id]
    await message.reply(messages.clear_dialogues_message)


@dp.message_handler(commands=['query'])
async def group(message: types.Message):
    await process(message, message.text[7:])


@dp.message_handler(commands=['tokens'])
async def group(message: types.Message):
    prompt = messages.parse_prompt(message.chat.full_name)
    if message.chat.id in dialogue:
        last = dialogue[message.chat.id]
    else:
        last = prompt

    prompt_count = lang.tokens_count(prompt)
    tokens_count = lang.tokens_count(last) - prompt_count
    await message.reply(
        await messages.tokens_command_message(prompt_count, tokens_count),
        parse_mode="Markdown")


@dp.message_handler()
async def process_pm(message: types.Message):
    if message.chat.type == 'private':
        await process(message, message.text)
    elif message.chat.type == 'group' or message.chat.type == 'super_group' or message.chat.type == 'supergroup':
        if message.text.startswith(f'{messages.name_russian}, ') or message.text.startswith(
                f'{messages.name_english}, '):
            await process(message, message.text[7:])


async def process(message: types.Message, text: str):
    text = text.strip()
    await message.chat.do(action='typing')
    if text == '':
        await message.reply(messages.empty_query)
        return
    if lang.is_russian(text):
        if len(text) >= 500:
            await message.reply(messages.long_query)
            return
        text = lang.translate(text, "ru|en")

    last = messages.parse_prompt(message.chat.full_name)
    if message.chat.id in dialogue:
        last = dialogue[message.chat.id]
    request = f'{last}\nHuman: {text}\n{messages.name_english}: '
    result_tokens_count = 4096 - lang.tokens_count(request)
    if result_tokens_count <= 10:
        await message.reply(messages.many_tokens)
        return
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
            response = openai.Completion.create(
                model="text-davinci-003",
                prompt=request,
                temperature=0.3,
                max_tokens=result_tokens_count,
                top_p=1,
                frequency_penalty=0.1,
                presence_penalty=1.4,
                stop=["Human:", f"{messages.name_english}:"],
                user=str(message.chat.id)
            )
            retry = False
            response_text = response['choices'][0]['text']
        except OpenAIError:
            retry = True
            i += 1

    send_text = response_text.strip()
    while send_text.startswith(f'{messages.name_english}:'):
        send_text = send_text[6:]
    send_text = send_text.strip()
    dialogue[message.chat.id] = f'{request}{send_text}'
    if send_text == messages.new_dialogues_id:
        dialogue[message.chat.id] = messages.parse_prompt(message.chat.full_name)
        await message.reply(messages.clear_dialogues_message)
    elif send_text == messages.help_message_id:
        await message.reply(messages.help_message, parse_mode='markdown')
    else:
        try:
            await message.reply(send_text, parse_mode='HTML')
        except CantParseEntities:
            await message.reply(messages.cant_send_with_fonts)
            await message.answer(send_text)
            print(messages.parse_error)


if __name__ == '__main__':
    executor.start_polling(dp)
