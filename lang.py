import json
import string

import requests
import tiktoken

ru_alphabet_lowercase = 'абвгдеёжзийклмнопрстуфхцчшщъыьэюя'
ru_alphabet_uppercase = ru_alphabet_lowercase.upper()
ru_alphabet = ru_alphabet_lowercase + ru_alphabet_uppercase
symbols = string.punctuation + string.digits + ' '


def count_alph(text: str, alph: str):
    i = 0
    for char in alph:
        i += text.count(char)
    return i


def remove_symbols(text: str, blacklist: str):
    for char in blacklist:
        text = text.replace(char, '')
    return text


def is_russian(text: str):
    text = remove_symbols(text, symbols)
    if len(text) == 0:
        return False
    return count_alph(text, ru_alphabet) / len(text) * 100 >= 50


def tokens_count(text: str):
    return len(tiktoken.encoding_for_model("gpt-3.5-turbo").encode(text))


def translate(text: str, lang_pair: str):
    return json.loads(
        requests.request(
            "get",
            "https://api.mymemory.translated.net/get",
            params={
                "q": text,
                "langpair": lang_pair,
                "de": "slavapmk@gmail.com"
            }
        ).text
    )['responseData']['translatedText']
