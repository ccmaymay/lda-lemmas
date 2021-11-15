import requests
import uuid
from typing import List

MAX_NUM_LOOKUP_WORDS = 10


def translate(words: List[str], from_lang: str, to_lang: str, subscription_key: str) -> List[str]:
    if any(len(word) > 100 for word in words):
        raise Exception('Words must be at most 100 characters each')

    url = 'https://api.cognitive.microsofttranslator.com/dictionary/lookup'
    params = {
        'api-version': '3.0',
        'from': from_lang,
        'to': to_lang,
    }

    translated_words = []
    for start_word_idx in range(0, len(words), MAX_NUM_LOOKUP_WORDS):
        headers = {
            'Ocp-Apim-Subscription-Key': subscription_key,
            'Ocp-Apim-Subscription-Region': 'global',
            'Content-type': 'application/json',
            'X-ClientTraceId': str(uuid.uuid4())
        }
        body = [
            {'text': word}
            for word in words[start_word_idx:start_word_idx + MAX_NUM_LOOKUP_WORDS]
        ]
        request = requests.post(url, params=params, headers=headers, json=body)
        response = request.json()
        translated_words += [item['translations'][0]['normalizedTarget'] for item in response]

    return translated_words
