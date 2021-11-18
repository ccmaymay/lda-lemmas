import requests
import uuid
from typing import List, NamedTuple

MAX_NUM_LOOKUP_WORDS = 10


class BackTranslation(NamedTuple):
    source: str
    frequency: int


class WordTranslation(NamedTuple):
    source: str
    target: str
    confidence: float
    back_translations: List[BackTranslation]


def translate(
        words: List[str],
        from_lang: str,
        to_lang: str,
        subscription_key: str) -> List[List[WordTranslation]]:
    if any(len(word) > 100 for word in words):
        raise Exception('Words must be at most 100 characters each')

    url = 'https://api.cognitive.microsofttranslator.com/dictionary/lookup'
    params = {
        'api-version': '3.0',
        'from': from_lang,
        'to': to_lang,
    }

    word_translations = []
    for start_word_idx in range(0, len(words), MAX_NUM_LOOKUP_WORDS):
        headers = {
            'Ocp-Apim-Subscription-Key': subscription_key,
            'Ocp-Apim-Subscription-Region': 'global',
            'Content-type': 'application/json',
            'X-ClientTraceId': str(uuid.uuid4())
        }
        source_words = words[start_word_idx:start_word_idx + MAX_NUM_LOOKUP_WORDS]
        body = [{'text': word} for word in source_words]
        request = requests.post(url, params=params, headers=headers, json=body)
        response = request.json()
        if isinstance(response, list):
            word_translations += [
                [
                    WordTranslation(
                        source=item['normalizedSource'],
                        target=translation['normalizedTarget'],
                        confidence=translation['confidence'],
                        back_translations=[
                            BackTranslation(
                                source=bt['normalizedText'],
                                frequency=bt['frequencyCount']
                            )
                            for bt in translation['backTranslations']
                        ],
                    )
                    for translation in item['translations']
                ]
                for item in response
            ]
        elif isinstance(response, dict) and 'error' in response:
            error_message = response['error']['message']
            error_code = response['error']['code']
            raise Exception(f'Received API error code {error_code}: {error_message}')
        else:
            raise Exception(f'Received unrecognized API response {response}')

    return word_translations
