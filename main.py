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
    await hide_settings_buttons(str(message.chat.id))
    await message.reply(messages.help_message, parse_mode="Markdown", disable_web_page_preview=True)


@dp.message_handler(commands=['reset'])
async def reset(message: types.Message):
    await hide_settings_buttons(str(message.chat.id))
    manager.reset_dialogue(str(message.chat.id))
    await message.reply(messages.clear_dialogues_message)


def parse_info_text(chat_id, prompt_size, tokens_count):
    return messages.info_message(chat_id, prompt_size, tokens_count)


async def parse_info_keyboard(message):
    chat_id = str(message.chat.id)
    prompt_size, tokens_count = manager.get_usage(chat_id, message.chat.full_name)
    keyboard = types.InlineKeyboardMarkup()
    keyboard.add(
        types.InlineKeyboardButton(
            text=messages.button_not_translate if manager.get_data(chat_id)['settings']['auto_translator']
            else messages.button_translating,
            callback_data="switch_translator"
        ),
        types.InlineKeyboardButton(
            text=messages.button_disable_dgpt if manager.get_data(chat_id)['settings']['dgpt']
            else messages.button_enable_dgpt,
            callback_data="switch_dgpt"
        )
    )
    return chat_id, keyboard, prompt_size, tokens_count


@dp.callback_query_handler(text="switch_translator")
async def process_lang_button(call: types.CallbackQuery):
    manager.get_data(str(call.message.chat.id))['settings']['auto_translator'] = not \
        manager.get_data(str(call.message.chat.id))['settings']['auto_translator']

    chat_id, keyboard, prompt_size, tokens_count = await parse_info_keyboard(call.message)

    await call.message.edit_text(
        parse_info_text(str(call.message.chat.id), prompt_size, tokens_count),
        parse_mode="Markdown",
        reply_markup=keyboard
    )


@dp.callback_query_handler(text="switch_dgpt")
async def process_dgpt_button(call: types.CallbackQuery):
    if manager.get_data(str(call.message.chat.id))['settings']['dgpt'] and \
            manager.get_data(str(call.message.chat.id))['dan_count'] != 0:
        manager.reset_dialogue(str(call.message.chat.id))
        await call.message.answer(messages.clear_dialogues_message)

    manager.get_data(str(call.message.chat.id))['settings']['dgpt'] = not \
        manager.get_data(str(call.message.chat.id))['settings']['dgpt']

    chat_id, keyboard, prompt_size, tokens_count = await parse_info_keyboard(call.message)
    await call.message.edit_text(
        parse_info_text(str(call.message.chat.id), prompt_size, tokens_count),
        parse_mode="Markdown",
        reply_markup=keyboard
    )


@dp.message_handler(commands=['info'])
async def info_command(message: types.Message):
    chat_id, keyboard, prompt_size, tokens_count = await parse_info_keyboard(message)
    await hide_settings_buttons(chat_id)
    manager.get_data(chat_id)['last_settings'].append(
        (await message.reply(parse_info_text(chat_id, prompt_size, tokens_count), parse_mode="Markdown",
                             reply_markup=keyboard)).message_id)


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
    await hide_settings_buttons(chat_id)
    text = text.strip()
    await message.chat.do(action='typing')
    if text == '':
        await message.reply(messages.empty_query)
        return

    if lang.is_russian(text) and manager.get_data(chat_id)['settings']['auto_translator']:
        if len(text) >= 500:
            await message.reply(messages.long_query)
            return
        text = lang.translate(text, "ru|en")

    prompt_size, tokens_count = manager.get_usage(chat_id, message.chat.full_name)
    if 4096 - prompt_size - tokens_count + prompt_size < 250:
        await message.reply(messages.many_tokens)
        return

    if manager.get_data(chat_id)['settings']['dgpt']:
        manager.get_data(chat_id)['dan_count'] += 1
        text = messages.parse_dgpt_prompt(text)
    if len(manager.get_data(chat_id)['dialogue']) == 0:
        prompt = messages.parse_prompt(message.chat.full_name)
        manager.get_data(chat_id)['dialogue'] = [{"role": "system", "content": prompt}]
    manager.get_data(chat_id)['dialogue'].append({"role": "user", "content": text})

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
                messages=manager.get_data(chat_id)['dialogue']
            )
            retry = False
            manager.get_data(chat_id)['usage'] = response['usage']['total_tokens']
            response_text = response['choices'][0]['message']['content']
        except OpenAIError:
            retry = True
            i += 1

    send_text = response_text.strip()
    manager.get_data(chat_id)['dialogue'].append({"role": "assistant", "content": send_text})
    try:
        await message.reply(send_text, parse_mode='Markdown', allow_sending_without_reply=True,
                            disable_web_page_preview=True)
    except CantParseEntities:
        await message.reply(messages.cant_send_with_fonts, allow_sending_without_reply=True,
                            disable_web_page_preview=True)
        await message.answer(send_text)
        print(messages.parse_error)


async def hide_settings_buttons(chat_id):
    for remove_id in manager.get_data(chat_id)['last_settings']:
        await bot.edit_message_reply_markup(chat_id, remove_id, reply_markup=None)
    manager.get_data(chat_id)['last_settings'] = []


if __name__ == '__main__':
    executor.start_polling(dp)
