import atexit
import json
import logging

import openai
from aiogram import Bot, Dispatcher, types
from aiogram.utils import executor
from openai.error import RateLimitError, Timeout, TryAgain

import config
import translate

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
                        "Если вы используете бота в групповом чате, то все запросы выполняйте через /query или "
                        "обращайтесь по имени\n"
                        "Например: `/query Как дела?` или `Ибрагим, Как дела?`", parse_mode="Markdown"
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
    text = text.strip()
    await message.chat.do(action='typing')
    if text == '':
        await message.reply('Запрос пустой. Отправьте заного')
        return
    if len(text) >= 500:
        await message.reply('Запрос слишком длинный. Переформулируйте его до 500 символов.')
        return
    text = translate.auto_english(text)
    last = 'AI: Start Messaging'
    if message.chat.id in dialogue:
        last = dialogue[message.chat.id]
    request = f'{last}\nHuman: {text}\n'
    result_size = 4048 - len(request)
    if result_size <= 100:
        await message.reply('Диалог слишком длинный. Пожалуйста начните заного (/reset).')
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
                frequency_penalty=0.1,
                presence_penalty=0.6,
                stop=[" Human:", " AI:"],
                user=str(message.chat.id)
            )
            retry = False
            response_text = response['choices'][0]['text']
        except RateLimitError or Timeout or TryAgain:
            retry = True
            i += 1
        except openai.error.OpenAIError as e:
            await message.reply(f"OpenAI API returned an Error: {e}")
            return

    send_text = response_text.strip()
    while send_text.startswith('AI: '):
        send_text = send_text[3:]
    send_text = send_text.strip()
    dialogue[message.chat.id] = f'{request}AI: {send_text}'

    await message.reply(send_text)


if __name__ == '__main__':
    executor.start_polling(dp)
