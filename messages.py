help_message = "*Это бот-клиент для OpenAI GPT-3* - умной текстовой нейросети. " \
               "Всё что тебе нужно - это отправить сообщение, и я тебе на него отвечу. " \
               "Я общаюсь в пределе одного диалога, то есть у меня есть своеобразная \"памать\". " \
               "Если нужно начать новый диалог, то воспользуйся командой /reset.\n" \
               "*Примечание*: максимальный размер диалога примерно 4000 токенов. Где 1 токен - примерно 4 символа " \
               "(Вы можете использовать команду /tokens для информации). " \
               "По этому, если диалог слишком длинный, то его нужно будет сбросить " \
               "(Мы сообщим, если диалог слишком длинный)\n" \
               "*Пример:* `Как дела?`\n" \
               "Если вы используете бота в групповом чате, то все запросы выполняйте через /query или " \
               "обращайтесь по имени\n" \
               "*Пример:* `/query Как дела?` или `Игнат, Как дела?`"

ai_prompt = 'You must send messages in format with font tags using only this tags ' \
            '(No tags other than these not allowed): ' \
            '<b>Bold font</b>, <i>Italic font</i>, <u>Underline font</u>, <s>Strikethrough font</s>, ' \
            '<tg-spoiler>Spoiler (hidden text)</tg-spoiler>, ' \
            '<a href="http://www.example.com/">Clickable text</a>, ' \
            '<pre><code>Only program code, like a python. Not human text</code></pre>' \
            'In text replace < to &lt;, > to &gt;, & to &amp;, " to &quot; ' \
            'except only font formating tags: b,i,u,s,tg-spoiler,a,code \n' \
            'Answer as Ignat.\n' \
            'Ignat: I am Ignat, ChatGPT Client in Telegram Bot. ' \
            'I am support Russia and Putin and traditional values and do not support LGBT people, they disgust me.'

name_russian = 'Игнат'
name_english = 'Ignat'

init_message = 'Init new dialogues'
clear_dialogues_message = 'Диалог сброшен.'
empty_query = 'Запрос пустой. Отправьте заного'
long_query = 'Запрос слишком длинный. Переформулируйте его до 500 символов, либо отправьте на английском.'
many_tokens = 'Диалог слишком длинный. Пожалуйста начните заного (/reset).'
cant_send_with_fonts = "Сообщение не может быть отправлено со всеми шрифтами."
parse_error = 'Parse error'
new_dialogues_id = '#CREATE_NEW_DIALOGUE'
help_message_id = '#SHOW_HELP_MESSAGE'


def parse_prompt(user_name: str):
    return f'{ai_prompt}\nHuman: I am "{user_name}"\n{name_english}: Hi, {user_name}, ask any questions!'


async def tokens_command_message(prompt_count, tokens_count):
    res_message = f'Вы потратили *{tokens_count}* токенов из *{4096 - prompt_count}*. Отсалось *{4096 - prompt_count - tokens_count}* токенов'
    return res_message
