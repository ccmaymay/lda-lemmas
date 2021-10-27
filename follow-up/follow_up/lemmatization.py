import logging
import re
from os import PathLike
from typing import Iterable, TextIO

from .util import save_polyglot, parse_polyglot_tokens, Doc

UNKNOWN_LEMMA_RE = re.compile(r'<unknown>?')

XML_SENT_START_RE = re.compile(r'<s>')
XML_SENT_END_RE = re.compile(r'</s>')
XML_SEG_START_RE = re.compile(r'<seg>')
XML_SEG_END_RE = re.compile(r'</seg>')
XML_WORD_START_RE = re.compile(r'<w form="(?P<form>.+)" tag="(?P<tag>.+)">')
XML_WORD_END_RE = re.compile(r'</w>')


def parse_treetagger(lang: str, input_path: PathLike, output_path: PathLike):
    with open(input_path, encoding='utf-8') as f:
        return save_polyglot(output_path, _parse_treetagger(lang, f))


def _parse_treetagger(lang: str, f: TextIO) -> Iterable[Doc]:
    if lang == 'en':
        return parse_polyglot_tokens(parse_treetagger_to_tokens_tsv(f))
    elif lang == 'fa':
        return parse_polyglot_tokens(parse_treetagger_to_tokens_tsv(f))
    elif lang == 'ko':
        return parse_polyglot_tokens(parse_treetagger_to_tokens_xml(f))
    elif lang == 'ru':
        return parse_polyglot_tokens(parse_treetagger_to_tokens_tsv(f))
    else:
        raise Exception(f'Unrecognized treetagger parser language {lang}')


def parse_treetagger_to_tokens_tsv(f: TextIO) -> Iterable[str]:
    for line in f:
        line = line.strip()
        if line:
            line_tokens = line.split('\t')
            if len(line_tokens) == 3:
                (word, _, lemma) = line_tokens
                if UNKNOWN_LEMMA_RE.fullmatch(lemma):
                    yield word
                else:
                    yield lemma

            else:
                logging.warning(f'Unexpected number of tokens in line: {line_tokens}')


def parse_treetagger_to_tokens_xml(f: TextIO) -> Iterable[str]:
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
                    if UNKNOWN_LEMMA_RE.fullmatch(lemma):
                        if word is not None:
                            yield word
                    else:
                        yield lemma

                else:
                    logging.warning(f'Unexpected number of tokens in line: {line_tokens}')
