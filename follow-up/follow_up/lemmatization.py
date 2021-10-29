import logging
import re
from dataclasses import dataclass
from os import PathLike
from typing import Iterable, Optional, TextIO

from .util import load_polyglot, save_polyglot, Doc, consume_doc_id_tokens

UNKNOWN_LEMMA_RE = re.compile(r'<unknown>?')

XML_SENT_START_RE = re.compile(r'<s>')
XML_SENT_END_RE = re.compile(r'</s>')
XML_SEG_START_RE = re.compile(r'<seg>')
XML_SEG_END_RE = re.compile(r'</seg>')
XML_WORD_START_RE = re.compile(r'<w form="(?P<form>.+)" tag="(?P<tag>.+)">')
XML_WORD_END_RE = re.compile(r'</w>')


@dataclass
class LemmaData(object):
    word: str
    pos: Optional[str]
    lemma: Optional[str]

    def get_word(self) -> str:
        return self.word

    def get_lemma(self) -> str:
        # back off to word form
        return self.lemma if self.lemma is not None else self.word


def lemmatize_docs_polyglot(lang: str, docs: Iterable[Doc]) -> Iterable[Doc]:
    # Load polyglot dynamically because dependencies are problematic
    from polyglot.load import load_morfessor_model  # type: ignore
    model = load_morfessor_model(lang=lang)

    for doc in docs:
        lem_doc = Doc(doc.doc_id, [])
        for section in doc.sections:
            try:
                lem_doc.sections.append(model.viterbi_segment(' '.join(section))[0])
            except Exception:
                logging.exception('Caught exception from polyglot lemmatizer')

        if lem_doc.tokens:
            yield lem_doc


def lemmatize_polyglot(lang: str, input_path: PathLike, output_path: PathLike):
    return save_polyglot(output_path, lemmatize_docs_polyglot(lang, load_polyglot(input_path)))


def parse_treetagger(lang: str, input_path: PathLike, output_path: PathLike):
    with open(input_path, encoding='utf-8') as f:
        return save_polyglot(output_path, _parse_treetagger(lang, f))


def _parse_treetagger(lang: str, f: TextIO) -> Iterable[Doc]:
    if lang == 'en':
        return parse_polyglot_lemmas(parse_treetagger_to_tokens_tsv(f))
    elif lang == 'fa':
        return parse_polyglot_lemmas(parse_treetagger_to_tokens_tsv(f))
    elif lang == 'ko':
        return parse_polyglot_lemmas(parse_treetagger_to_tokens_xml(f))
    elif lang == 'ru':
        return parse_polyglot_lemmas(parse_treetagger_to_tokens_tsv(f))
    else:
        raise Exception(f'Unrecognized treetagger parser language {lang}')


def parse_treetagger_to_tokens_tsv(f: TextIO) -> Iterable[LemmaData]:
    for line in f:
        line = line.strip()
        if line:
            line_tokens = line.split('\t')
            if len(line_tokens) == 3:
                (word, pos, lemma) = line_tokens
                if UNKNOWN_LEMMA_RE.fullmatch(lemma):
                    yield LemmaData(word=word, pos=pos, lemma=None)
                else:
                    yield LemmaData(word=word, pos=pos, lemma=lemma)

            else:
                logging.warning(f'Unexpected number of tokens in line: {line_tokens}')


def parse_treetagger_to_tokens_xml(f: TextIO) -> Iterable[LemmaData]:
    word = None
    for line in f:
        line = line.strip()
        if line:
            word_start_match = XML_WORD_START_RE.fullmatch(line)
            if XML_SENT_START_RE.fullmatch(line) or XML_SENT_END_RE.fullmatch(line):
                pass  # long hair, don't care
            elif XML_SEG_START_RE.fullmatch(line) or XML_SEG_END_RE.fullmatch(line):
                pass
            elif word_start_match:
                word = word_start_match.group('form')
            elif XML_WORD_END_RE.fullmatch(line):
                word = None
            else:
                line_tokens = line.split()
                if len(line_tokens) == 2:
                    (lemma, _) = line_tokens
                    if word is not None:
                        if UNKNOWN_LEMMA_RE.fullmatch(lemma):
                            yield LemmaData(word=word, pos=None, lemma=None)
                        else:
                            yield LemmaData(word=word, pos=None, lemma=lemma)

                else:
                    logging.warning(f'Unexpected number of tokens in line: {line_tokens}')


def parse_polyglot_lemmas(tokens: Iterable[LemmaData]) -> Iterable[Doc]:
    doc_id = None
    doc_tokens = []
    for token in tokens:
        doc_tokens.append(token)

        new_doc_id = consume_doc_id_tokens(doc_tokens, key=LemmaData.get_word)
        if new_doc_id is not None:
            if doc_id is not None and doc_tokens:
                yield Doc(doc_id, [[d.get_lemma() for d in doc_tokens]])

            doc_id = new_doc_id
            doc_tokens = []

    if doc_id is not None and doc_tokens:
        yield Doc(doc_id, [[d.get_lemma() for d in doc_tokens]])
