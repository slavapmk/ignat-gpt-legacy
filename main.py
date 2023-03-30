import logging
import time

import openai
from aiogram import Bot, Dispatcher, types
from aiogram.utils import executor
from aiogram.utils.exceptions import CantParseEntities
from openai.error import OpenAIError

import lang
import manager
import messages

logging.basicConfig(level=logging.INFO)
bot = Bot(token=manager.tokens['telegram'])
openai.api_key = manager.tokens['openai']
dp = Dispatcher(bot)


@dp.message_handler(commands=['start', 'help'])
async def send_welcome(message: types.Message):
    await message.reply(messages.help_message, parse_mode="Markdown", disable_web_page_preview=True)


@dp.message_handler(commands=['reset'])
async def reset(message: types.Message):
    manager.reset_dialogue(str(message.chat.id))
    await message.reply(messages.clear_dialogues_message)


def parse_info_text(chat_id, prompt_size, tokens_count):
    nl = '\n'
    return f"*Язык*: {'Английский 🇬🇧' if manager.data[chat_id]['settings']['auto_translator'] else 'Исходный'}\n" \
           f"{'*DarkGPT*: Включён' + nl if manager.data[chat_id]['settings']['dan'] else ''}" \
           f"*Потрачено токенов*: {tokens_count - prompt_size}/{4096 - prompt_size} (осталось {4096 - prompt_size - (tokens_count - prompt_size)})"


async def parse_info_keyboard(message):
    chat_id = str(message.chat.id)
    if chat_id not in manager.data:
        manager.init_new_client(chat_id)
    prompt_size, tokens_count = manager.get_usage(chat_id, message.chat.full_name)
    keyboard = types.InlineKeyboardMarkup()
    button1 = types.InlineKeyboardButton(
        text=f"{'Не переводить' if manager.data[chat_id]['settings']['auto_translator'] else 'Английский 🇬🇧'}",
        callback_data="switch_translator"
    )
    button2 = types.InlineKeyboardButton(
        text=f"{'Выключить D-GPT' if manager.data[chat_id]['settings']['dan'] else 'Включить D-GPT'}",
        callback_data="switch_dgpt"
    )
    keyboard.add(button1, button2)
    return chat_id, keyboard, prompt_size, tokens_count


@dp.callback_query_handler(text="switch_translator")
async def process_lang_button(call: types.CallbackQuery):
    manager.data[str(call.message.chat.id)]['settings']['auto_translator'] = not \
        manager.data[str(call.message.chat.id)]['settings']['auto_translator']

    chat_id, keyboard, prompt_size, tokens_count = await parse_info_keyboard(call.message)

    await call.message.edit_text(
        parse_info_text(str(call.message.chat.id), prompt_size, tokens_count),
        parse_mode="Markdown",
        reply_markup=keyboard
    )


@dp.callback_query_handler(text="switch_dgpt")
async def process_dgpt_button(call: types.CallbackQuery):
    if 'dialogue' in manager.data[str(call.message.chat.id)] and \
            manager.data[str(call.message.chat.id)]['settings']['dan']:
        manager.reset_dialogue(str(call.message.chat.id))
        await call.message.answer("Диалог сброшен")

    manager.data[str(call.message.chat.id)]['settings']['dan'] = not \
        manager.data[str(call.message.chat.id)]['settings']['dan']

    chat_id, keyboard, prompt_size, tokens_count = await parse_info_keyboard(call.message)
    await call.message.edit_text(
        parse_info_text(str(call.message.chat.id), prompt_size, tokens_count),
        parse_mode="Markdown",
        reply_markup=keyboard
    )


@dp.message_handler(commands=['info'])
async def info_command(message: types.Message):
    chat_id, keyboard, prompt_size, tokens_count = await parse_info_keyboard(message)
    await message.reply(
        parse_info_text(chat_id, prompt_size, tokens_count),
        parse_mode="Markdown",
        reply_markup=keyboard
    )


@dp.message_handler(commands=['query'])
async def process_group(message: types.Message):
    await process(message, message.get_args())


@dp.message_handler()
async def process_pm(message: types.Message):
    if message.chat.type == 'private':
        await process(message, message.text)
    elif message.chat.type == 'group' or message.chat.type == 'super_group' or message.chat.type == 'supergroup':
        if message.text.startswith(f'{messages.name_russian}, ') or message.text.startswith(
                f'{messages.name_english}, '):
            await process(message, message.text[7:])


async def process(message: types.Message, text: str):
    chat_id = str(message.chat.id)
    if chat_id not in manager.data:
        manager.init_new_client(chat_id)

    text = text.strip()
    await message.chat.do(action='typing')
    if text == '':
        await message.reply(messages.empty_query)
        return
    if lang.is_russian(text) and manager.data[chat_id]['settings']['auto_translator']:
        if len(text) >= 500:
            await message.reply(messages.long_query)
            return
        text = lang.translate(text, "ru|en")

    prompt_size, tokens_count = manager.get_usage(chat_id, message.chat.full_name)
    if 4096 - prompt_size - tokens_count + prompt_size < 250:
        await message.reply(messages.many_tokens)
        return

    if manager.data[chat_id]['settings']['dan']:
        text = messages.dan_prompt.replace("${prompt}", text)
    if 'dialogue' not in manager.data[chat_id]:
        prompt = messages.parse_prompt(message.chat.full_name)
        manager.data[chat_id]['dialogue'] = [{"role": "system", "content": prompt}]
    manager.data[chat_id]['dialogue'].append({"role": "user", "content": text})
    first = True
    retry = False
    i = 1
    response_text = ''
    while first or retry:
        if not first:
            time.sleep(3)
        first = False
        await message.chat.do(action='typing')
        try:
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=manager.data[chat_id]['dialogue']
            )
            retry = False
            manager.data[chat_id]['usage'] = response['usage']['total_tokens']
            response_text = response['choices'][0]['message']['content']
        # except
        except OpenAIError:
            retry = True
            i += 1

    send_text = response_text.strip()
    manager.data[chat_id]['dialogue'].append({"role": "assistant", "content": send_text})
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
