import string

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
