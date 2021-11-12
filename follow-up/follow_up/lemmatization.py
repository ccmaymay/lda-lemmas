import logging
import re
from dataclasses import dataclass
from os import PathLike
from typing import Iterable, List, Optional, TextIO

import conllu

from .util import save_polyglot, Doc, get_doc_id

# treetagger treats <> as SGML, so we allow for that here as well:
SGML_TAG_RE = re.compile(r'<.*>')

UNKNOWN_LEMMA_RE = re.compile(r'<unknown>')

SENT_START_RE = re.compile(r'<s>')
SENT_END_RE = re.compile(r'</s>')
SEG_START_RE = re.compile(r'<seg>')
SEG_END_RE = re.compile(r'</seg>')
WORD_START_RE = re.compile(r'<w form="(?P<form>.+)" tag="(?P<tag>.+)">')
WORD_END_RE = re.compile(r'</w>')

DOC_ID_NUM_TOKENS_KO_TT = 5


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
    if lang == 'ko':
        return parse_polyglot_lemmas(parse_treetagger_to_tokens_korean(f))
    else:
        return parse_polyglot_lemmas(parse_treetagger_to_tokens(f))


def parse_treetagger_to_tokens(f: TextIO) -> Iterable[List[LemmaData]]:
    sentence: List[LemmaData] = []
    for line in f:
        line = line.strip()
        if line:
            if SENT_START_RE.fullmatch(line) or SENT_END_RE.fullmatch(line):
                if sentence:
                    yield sentence
                    sentence = []

            else:
                line_tokens = line.split('\t')
                if len(line_tokens) == 3:
                    (form, _, lemma) = line_tokens
                    if UNKNOWN_LEMMA_RE.fullmatch(lemma):
                        sentence.append(LemmaData(form=form, lemma=None))
                    else:
                        sentence.append(LemmaData(form=form, lemma=lemma))
                elif len(line_tokens) == 1 and SGML_TAG_RE.fullmatch(line_tokens[0]) is not None:
                    sentence.append(LemmaData(form=form, lemma=None))
                else:
                    logging.warning(f'Unexpected number of tokens in line: {line_tokens}')

    if sentence:
        yield sentence


def parse_treetagger_to_tokens_korean(f: TextIO) -> Iterable[List[LemmaData]]:
    form = None
    sentence: List[LemmaData] = []
    for line in f:
        line = line.strip()
        if line:
            word_start_match = WORD_START_RE.fullmatch(line)

            if SENT_START_RE.fullmatch(line):
                pass

            elif SENT_END_RE.fullmatch(line):
                if sentence:
                    yield sentence
                    sentence = []

            elif SEG_START_RE.fullmatch(line):
                pass

            elif SEG_END_RE.fullmatch(line):
                # ensure doc id gets its own sentence
                if len(sentence) >= DOC_ID_NUM_TOKENS_KO_TT:
                    doc_id_sentence = sentence[-DOC_ID_NUM_TOKENS_KO_TT:]
                    doc_id = get_doc_id(''.join(token.get_form() for token in doc_id_sentence))
                    if doc_id is not None:
                        yield doc_id_sentence
                        sentence = sentence[:-DOC_ID_NUM_TOKENS_KO_TT]

            elif word_start_match:
                form = word_start_match.group('form')

            elif WORD_END_RE.fullmatch(line):
                form = None

            else:
                line_tokens = line.split()
                if len(line_tokens) == 2:
                    (lemma, _) = line_tokens
                    if form is not None:
                        if UNKNOWN_LEMMA_RE.fullmatch(lemma):
                            sentence.append(LemmaData(form=form, lemma=None))
                        else:
                            sentence.append(LemmaData(form=form, lemma=lemma))
                else:
                    logging.warning(f'Unexpected number of tokens in line: {line_tokens}')

    if sentence:
        yield sentence


def parse_polyglot_lemmas(tokens: Iterable[List[LemmaData]]) -> Iterable[Doc]:
    doc = None
    for sent_tokens in tokens:
        doc_id = get_doc_id(''.join(token.get_form() for token in sent_tokens))
        if doc_id is not None:
            if doc is not None and doc.tokens:
                yield doc
            doc = Doc(doc_id, [])
        elif doc is not None and sent_tokens:
            doc.sections.append([token.get_lemma() for token in sent_tokens])

    if doc is not None and doc.tokens:
        yield doc


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
                list(_parse_conllu_sentence(sentence))
                for sentence in conllu.parse_incr(f)
            )
        )
