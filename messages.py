help_message = "*Это бот-клиент для OpenAI GPT-3.5 (ChatGPT)* - умной текстовой нейросети. " \
               "Всё что тебе нужно - это отправить сообщение, и я тебе на него отвечу. " \
               "Я общаюсь в пределе одного диалога, то есть у меня есть своеобразная \"памать\". " \
               "Если нужно начать новый диалог, то воспользуйся командой /reset.\n" \
               "*Пример:* `Как дела?`\n" \
               "Если вы используете бота в групповом чате, то все запросы выполняйте через /query или " \
               "обращайтесь по имени.\n" \
               "*Пример:* `/query Как дела?` или `Игнат, Как дела?`\n" \
               "*Примечание*: максимальный размер диалога примерно 4000 токенов. Где 1 токен - примерно 4 символа " \
               "(Вы можете использовать команду /tokens для информации). " \
               "По этому, если диалог слишком длинный, то его нужно будет сбросить " \
               "(Мы сообщим, если диалог слишком длинный)\n" \
               "[Исходный код](https://github.com/slavapmk/chat-gpt-telegram)"
ai_prompt = "You are responsible for the chatbot in telegram. Therefore you must send messages in format for " \
            "Telegram with using only this tags " \
            "(No tags other than these not allowed):\n" \
            "*bold \\*text*\n" \
            "_italic \\*text_\n" \
            "__underline__\n" \
            "[inline URL](http://www.example.com/)\n" \
            "```python\n" \
            "pre-formatted fixed-width code block written in the Python programming language\n" \
            "```\n" \
            "Instead of * and _, use \\* and \\_"
name_russian = 'Игнат'
name_english = 'Ignat'

init_data = 'Init new data file'
clear_dialogues_message = 'Диалог сброшен.'
empty_query = 'Мы не можем обработать пустой запрос'
long_query = 'Запрос слишком длинный. Переформулируйте его до 500 символов, либо повторите на английском.'
many_tokens = 'Лимит диалога превышен. Пожалуйста начните его заного (/reset).'
cant_send_with_fonts = "Сообщение не может быть отправлено со всеми шрифтами."
parse_error = 'Parse error'


async def tokens_command_message(tokens_count, prompt_size):
    spent_tokens = tokens_count - prompt_size
    max_tokens = 4096 - prompt_size
    res_message = f'Вы потратили *{spent_tokens}* токенов из *{max_tokens}*. ' \
                  f'Осталось *{max_tokens - spent_tokens}* токенов'
    return res_message
