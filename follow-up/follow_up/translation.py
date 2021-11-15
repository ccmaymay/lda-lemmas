import requests
import uuid
from typing import List


def translate(
        input_texts: List[str], from_lang: str, to_lang: str, subscription_key: str) -> List[str]:
    url = 'https://api.cognitive.microsofttranslator.com/translate'
    params = {
        'api-version': '3.0',
        'from': from_lang,
        'to': to_lang,
    }
    headers = {
        'Ocp-Apim-Subscription-Key': subscription_key,
        'Ocp-Apim-Subscription-Region': 'global',
        'Content-type': 'application/json',
        'X-ClientTraceId': str(uuid.uuid4())
    }
    body = [{'text': text} for text in input_texts]
    request = requests.post(url, params=params, headers=headers, json=body)
    response = request.json()
    return [item['translations'][0]['text'] for item in response]
