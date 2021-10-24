from polyglot.text import Text  # type: ignore

from .util import load_polyglot, Doc


def lemmatize_polyglot(lang, input_path, output_path):
    for doc in load_polyglot(input_path):
        yield Doc(doc.name, [
            [morpheme for word in sentence.words for morpheme in word.morphemes]
            for sentence in Text(doc.text, hint_language_code=lang).sentences
        ])
