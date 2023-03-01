import json
import requests

import lang_utils


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


def auto_english(text: str):
    if not lang_utils.is_russian(text):
        return text
    return translate(text, "ru|en")
