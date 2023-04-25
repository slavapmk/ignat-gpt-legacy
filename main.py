import asyncio
import json
import logging
from asyncio import CancelledError

import aiohttp
from aiogram import Bot, Dispatcher, types
from aiogram.utils import executor
from aiogram.utils.exceptions import CantParseEntities

import lang
import manager
import messages

logging.basicConfig(level=logging.INFO)
bot = Bot(token=manager.tokens['telegram'])
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
    prompt_size, tokens_count = manager.get_usage(chat_id, message.chat.full_name, message.chat.type != 'private')
    keyboard = types.InlineKeyboardMarkup()
    keyboard.add(
        types.InlineKeyboardButton(
            text=messages.button_not_translate if manager.get_data(chat_id)['settings']['auto_translator']
            else messages.button_translating,
            callback_data="switch_translator"
        ),
        types.InlineKeyboardButton(
            text=messages.button_disable_darkgpt if manager.get_data(chat_id)['settings']['darkgpt']
            else messages.button_enable_darkgpt,
            callback_data="switch_darkgpt"
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


@dp.callback_query_handler(text="switch_darkgpt")
async def process_darkgpt_button(call: types.CallbackQuery):
    if manager.get_data(str(call.message.chat.id))['settings']['darkgpt'] and \
            manager.get_data(str(call.message.chat.id))['dan_count'] != 0:
        manager.reset_dialogue(str(call.message.chat.id))
        await call.message.answer(messages.clear_dialogues_message)

    manager.get_data(str(call.message.chat.id))['settings']['darkgpt'] = not \
        manager.get_data(str(call.message.chat.id))['settings']['darkgpt']

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


free = True


async def process(message: types.Message, text: str):
    chat_id = str(message.chat.id)
    await hide_settings_buttons(chat_id)
    text = text.strip()
    if manager.get_data(chat_id)['name'] == '':
        manager.get_data(chat_id)['name'] = message.chat.full_name
    if manager.get_data(chat_id)['nick'] == '':
        manager.get_data(chat_id)['nick'] = message.chat.username
    if text == '':
        await message.reply(messages.empty_query)
        return

    if lang.is_russian(text) and manager.get_data(chat_id)['settings']['auto_translator']:
        if len(text) >= 500:
            await message.reply(messages.long_query)
            return
        text = lang.translate(text, "ru|en")

    prompt_size, tokens_count = manager.get_usage(chat_id, message.chat.full_name, message.chat.type != 'private')
    if 4096 - prompt_size - tokens_count + prompt_size < 250:
        await message.reply(messages.many_tokens)
        return

    task1 = asyncio.get_event_loop().create_task(process_typing_action(message))
    global free
    while not free:
        await asyncio.sleep(1)
    free = False

    if manager.get_data(chat_id)['settings']['darkgpt']:
        manager.get_data(chat_id)['dan_count'] += 1
        text = messages.parse_darkgpt_prompt(text)
    if len(manager.get_data(chat_id)['dialogue']) == 0:
        prompt = messages.parse_prompt(message.chat.full_name, message.chat.type != 'private')
        manager.get_data(chat_id)['dialogue'] = [{"role": "system", "content": prompt}]
    manager.get_data(chat_id)['dialogue'].append({"role": "user", "content": text})

    task2 = asyncio.get_event_loop().create_task(process_openai_request(manager.get_data(chat_id)['dialogue']))
    response_text, usage = await task2
    task1.cancel()

    manager.get_data(chat_id)['usage'] = usage
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
    free = True


async def process_typing_action(message: types.Message):
    while True:
        try:
            await message.chat.do(action='typing')
            await asyncio.sleep(2)
        except CancelledError:
            break


async def process_openai_request(dialogue):
    first = True
    retry = False
    response = {}
    while first or retry:
        if not first:
            await asyncio.sleep(21)
        first = False
        async with aiohttp.ClientSession() as session:
            headers = {'Content-Type': 'application/json', 'Authorization': f'Bearer {manager.tokens["openai"]}'}
            data = (json.dumps({'model': 'gpt-3.5-turbo', 'messages': dialogue}))
            async with session.post(
                    url='https://api.openai.com/v1/chat/completions',
                    headers=headers,
                    data=data,
                    timeout=600000
            ) as resp:
                if resp.status == 200:
                    response = await resp.json()
                    retry = False
                else:
                    print(resp.status, json.dumps({"headers": headers, "data": data, "response": resp.content}))
                    retry = True
    return response['choices'][0]['message']['content'], response['usage']['total_tokens']


async def hide_settings_buttons(chat_id):
    for remove_id in manager.get_data(chat_id)['last_settings']:
        await bot.edit_message_reply_markup(chat_id, remove_id, reply_markup=None)
    manager.get_data(chat_id)['last_settings'] = []


if __name__ == '__main__':
    executor.start_polling(dp)
