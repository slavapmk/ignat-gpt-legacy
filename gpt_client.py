import atexit
import json
import logging

import openai
from aiogram import Bot, Dispatcher, types
from aiogram.utils import executor
from openai.error import RateLimitError, Timeout, TryAgain

import config

openai.api_key = config.openai_token

logging.basicConfig(level=logging.INFO)

bot = Bot(token=config.telegram_token)
dp = Dispatcher(bot)


def keys_to_int(x):
    return {int(k): v for k, v in x.items()}


dialogue = {}
try:
    with open('../gpt/dialogues.json', 'r') as f:
        read = f.read()
        if read != '':
            dialogue = json.loads(read, object_hook=keys_to_int)
except IOError:
    print('Init new dialogues')


def exit_handler():
    with open('../gpt/dialogues.json', 'w') as file_to_save:
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
    result_size = 4048 - len(request)
    if result_size <= 100:
        await replied_message.edit_text('Диалог слишком длинный. Пожалуйста начните заного (/reset).')
        return
    first = True
    retry = False
    i = 1
    while first or retry:
        first = False
        try:
            response = openai.Completion.create(
                model="text-davinci-003",
                prompt=request,
                temperature=0.9,
                max_tokens=result_size,
                top_p=1,
                frequency_penalty=0.9,
                presence_penalty=0.6,
                stop=[" Human:", " AI:"],
                user=str(message.chat.id)
            )
            retry = False
            response_text = response['choices'][0]['text']
        except RateLimitError or Timeout or TryAgain:
            retry = True
            i += 1
            await replied_message.edit_text(f'Обработка - попытка {i}')
        except openai.error.OpenAIError as e:
            await replied_message.edit_text(f"OpenAI API returned an Error: {e}")
            return

    while response_text.startswith('\n'):
        response_text = response_text[1:]
    dialogue[message.chat.id] = f'{request}{response_text}'
    send_text = response_text
    while send_text.startswith('AI: '):
        send_text = send_text[3:]
    while send_text.startswith(' '):
        send_text = send_text[1:]

    await replied_message.edit_text(send_text)


if __name__ == '__main__':
    executor.start_polling(dp)
