import logging
import re
from dataclasses import dataclass
from os import PathLike
from typing import Iterable, Optional, TextIO

import conllu

from .util import save_polyglot, Doc, consume_doc_id_tokens

UNKNOWN_LEMMA_RE = re.compile(r'<unknown>?')

XML_SENT_START_RE = re.compile(r'<s>')
XML_SENT_END_RE = re.compile(r'</s>')
XML_SEG_START_RE = re.compile(r'<seg>')
XML_SEG_END_RE = re.compile(r'</seg>')
XML_WORD_START_RE = re.compile(r'<w form="(?P<form>.+)" tag="(?P<tag>.+)">')
XML_WORD_END_RE = re.compile(r'</w>')


@dataclass
class LemmaData(object):
    form: str
    lemma: Optional[str]

    def get_form(self) -> str:
        return self.form

    def get_lemma(self) -> str:
        # back off to word form
        return self.lemma if self.lemma is not None else self.form


def parse_treetagger(lang: str, input_path: PathLike, output_path: PathLike):
    with open(input_path, encoding='utf-8') as f:
        save_polyglot(output_path, _parse_treetagger(lang, f))


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
                (form, _, lemma) = line_tokens
                if UNKNOWN_LEMMA_RE.fullmatch(lemma):
                    yield LemmaData(form=form, lemma=None)
                else:
                    yield LemmaData(form=form, lemma=lemma)

            else:
                logging.warning(f'Unexpected number of tokens in line: {line_tokens}')


def parse_treetagger_to_tokens_xml(f: TextIO) -> Iterable[LemmaData]:
    form = None
    for line in f:
        line = line.strip()
        if line:
            word_start_match = XML_WORD_START_RE.fullmatch(line)
            if XML_SENT_START_RE.fullmatch(line) or XML_SENT_END_RE.fullmatch(line):
                pass  # long hair, don't care
            elif XML_SEG_START_RE.fullmatch(line) or XML_SEG_END_RE.fullmatch(line):
                pass
            elif word_start_match:
                form = word_start_match.group('form')
            elif XML_WORD_END_RE.fullmatch(line):
                form = None
            else:
                line_tokens = line.split()
                if len(line_tokens) == 2:
                    (lemma, _) = line_tokens
                    if form is not None:
                        if UNKNOWN_LEMMA_RE.fullmatch(lemma):
                            yield LemmaData(form=form, lemma=None)
                        else:
                            yield LemmaData(form=form, lemma=lemma)

                else:
                    logging.warning(f'Unexpected number of tokens in line: {line_tokens}')


def parse_polyglot_lemmas(tokens: Iterable[LemmaData]) -> Iterable[Doc]:
    doc_id = None
    doc_tokens = []
    for token in tokens:
        doc_tokens.append(token)

        new_doc_id = consume_doc_id_tokens(doc_tokens, key=LemmaData.get_form)
        if new_doc_id is not None:
            if doc_id is not None and doc_tokens:
                yield Doc(doc_id, [[d.get_lemma() for d in doc_tokens]])

            doc_id = new_doc_id
            doc_tokens = []

    if doc_id is not None and doc_tokens:
        yield Doc(doc_id, [[d.get_lemma() for d in doc_tokens]])


def _parse_conllu_sentence(sentence: conllu.TokenList) -> Iterable[LemmaData]:
    for token in sentence:
        # TODO: does this catch all unknowns?
        if token['lemma'] == '_':
            yield LemmaData(form=token['form'], lemma=None)
        else:
            yield LemmaData(form=token['form'], lemma=token['lemma'])


def parse_udpipe(lang: str, input_path: PathLike, output_path: PathLike):
    with open(input_path, encoding='utf-8') as f:
        save_polyglot(
            output_path,
            parse_polyglot_lemmas(
                lemma_data
                for sentence in conllu.parse_incr(f)
                for lemma_data in _parse_conllu_sentence(sentence)
            )
        )
