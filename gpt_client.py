import atexit
import json
import logging

import openai
from aiogram import Bot, Dispatcher, types
from aiogram.utils import executor

import config

openai.api_key = config.openai_token

logging.basicConfig(level=logging.INFO)

bot = Bot(token=config.telegram_token)
dp = Dispatcher(bot)


def keys_to_int(x):
    return {int(k): v for k, v in x.items()}


dialogue = {}
try:
    with open('dialogues.json', 'r') as f:
        read = f.read()
        if read != '':
            dialogue = json.loads(read, object_hook=keys_to_int)
except IOError:
    print('Init new dialogues')


def exit_handler():
    with open('dialogues.json', 'w') as file_to_save:
        json.dump(dialogue, file_to_save)


atexit.register(exit_handler)


@dp.message_handler(commands=['start', 'help'])
async def send_welcome(message: types.Message):
    await message.reply("Это бот-клиент для OpenAI ChatGPT - умной нейросети-чатбот. "
                        "Всё что тебе нужно - это отправить сообщение, и я тебе на него отвечу. "
                        "Если нужно начать новый диалог, то воспользуйся командой /reset.\n"
                        "*Примечание*: максимальный размер диалога 4000. "
                        "По этому, если диалог слишком длинный, то его нужно будет сбросить самостоятельно "
                        "(Мы сообщим, если диалог слишком длинный)\n"
                        "Если вы используете бота в групповом чате, то все запросы выполняйте через /query\n"
                        "Например: `/query Как дела?`", parse_mode="Markdown"
                        )


@dp.message_handler(commands=['reset'])
async def reset(message: types.Message):
    dialogue[message.chat.id] = 'AI: Start Messaging'
    await message.reply("Диалог сброшен.")


@dp.message_handler(commands=['query'])
async def group(message: types.Message):
    await process(message, message.text[7:])


@dp.message_handler()
async def process_pm(message: types.Message):
    if message.chat.type == 'private':
        await process(message, message.text)
    elif message.chat.type == 'group' or message.chat.type == 'super_group' or message.chat.type == 'supergroup':
        if message.text.startswith('Игнат, ') or message.text.startswith('Ignat, '):
            await process(message, message.text[7:])


async def process(message: types.Message, text: str):
    replied_message = await message.reply('Обработка')

    last = 'AI: Start Messaging'
    if message.chat.id in dialogue:
        last = dialogue[message.chat.id]
    request = f'{last}\nHuman: {text}\n'
    len_request_ = 4048 - len(request)
    if len_request_ <= 100:
        await replied_message.edit_text('Диалог слишком длинный. Пожалуйста начните заного.')
        return
    response = openai.Completion.create(
        model="text-davinci-003",
        prompt=request,
        temperature=0.9,
        max_tokens=len_request_,
        top_p=1,
        frequency_penalty=0.9,
        presence_penalty=0.6,
        stop=[" Human:", " AI:"],
        user=str(message.chat.id)
    )['choices'][0]['text']
    if response.startswith('\n'):
        response = response[1:]
    dialogue[message.chat.id] = f'{request}{response}'

    await replied_message.edit_text(response[4:])


if __name__ == '__main__':
    executor.start_polling(dp)
