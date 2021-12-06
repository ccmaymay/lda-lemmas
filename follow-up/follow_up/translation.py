import json
import os
import requests
import uuid
from os import PathLike
from typing import Any, Dict, Iterable, List, Optional, Type, TypeVar

T = TypeVar('T')

MAX_NUM_LOOKUP_WORDS = 10
MAX_LOOKUP_WORD_LEN = 100


def api_request(
        url: str,
        return_type: Type[T],
        params: Optional[Dict[str, str]] = None,
        headers: Optional[Dict[str, str]] = None,
        body: Any = None) -> T:
    request = requests.post(url, params=params, headers=headers, json=body)
    response = request.json()
    if isinstance(response, return_type):
        return response
    elif isinstance(response, dict) and 'error' in response:
        error_message = response['error']['message']
        error_code = response['error']['code']
        raise Exception(f'Received API error code {error_code}: {error_message}')
    else:
        raise Exception(f'Received unrecognized API response {response}')


def translate(
        words: List[str],
        from_lang: str,
        to_lang: str,
        subscription_key: Optional[str] = None) -> Iterable[Dict]:
    if subscription_key is None:
        subscription_key = os.environ['AZURE_SUBSCRIPTION_KEY']
    if any(len(word) > MAX_LOOKUP_WORD_LEN for word in words):
        raise Exception(
            f'Words with more than {MAX_LOOKUP_WORD_LEN} characters cannot be translated')
    return (
        word_translation
        for start_word_idx in range(0, len(words), MAX_NUM_LOOKUP_WORDS)
        for word_translation in api_request(
            'https://api.cognitive.microsofttranslator.com/dictionary/lookup',
            list,
            params={
                'api-version': '3.0',
                'from': from_lang,
                'to': to_lang,
            },
            headers={
                'Ocp-Apim-Subscription-Key': subscription_key,
                'Ocp-Apim-Subscription-Region': 'global',
                'Content-type': 'application/json',
                'X-ClientTraceId': str(uuid.uuid4()),
            },
            body=[
                {'text': word}
                for word in words[start_word_idx:start_word_idx + MAX_NUM_LOOKUP_WORDS]
            ],
        )
    )


def translate_words(
        input_path: PathLike,
        output_path: PathLike,
        from_lang: str,
        to_lang: str):
    with open(input_path, encoding='utf-8') as f:
        words = [line.strip() for line in f]
    with open(output_path, mode='w', encoding='utf-8') as f:
        for word_translation in translate(words, from_lang=from_lang, to_lang=to_lang):
            f.write(json.dumps(word_translation) + '\n')
