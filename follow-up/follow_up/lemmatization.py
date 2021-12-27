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


@dataclass
class LemmaData(object):
    form: str
    lemma: Optional[str] = None
    pos: Optional[str] = None

    def get_form(self) -> str:
        return self.form

    def get_lemma(self) -> str:
        # back off to word form
        return self.lemma if self.lemma is not None else self.form


def parse_treetagger(lang: str, input_path: PathLike, output_path: PathLike):
    with open(input_path, encoding='utf-8') as f:
        save_polyglot(output_path, _parse_treetagger(lang, f))


def _parse_treetagger(lang: str, f: TextIO) -> Iterable[Doc[str]]:
    if lang == 'ko':
        return parse_polyglot_lemmas(
            [
                LemmaData(
                    form=token.form,
                    lemma=(
                        token.lemma.split('_')[0]
                        if token.lemma is not None and token.pos is not None and '_' in token.pos
                        else token.lemma
                    ),
                    pos=token.pos
                )
                for token in section
            ]
            for section in parse_treetagger_to_tokens(f)
        )
    else:
        return parse_polyglot_lemmas(parse_treetagger_to_tokens(f))


def parse_treetagger_to_tokens(f: TextIO) -> Iterable[List[LemmaData]]:
    sentence: List[LemmaData] = []
    for line in f:
        line = line.strip()
        if line:
            if SENT_START_RE.fullmatch(line):
                pass

            elif SENT_END_RE.fullmatch(line):
                if sentence:
                    yield sentence
                    sentence = []

            else:
                line_tokens = line.split('\t')
                if len(line_tokens) == 3:
                    (form, pos, lemma) = line_tokens
                    if UNKNOWN_LEMMA_RE.fullmatch(lemma):
                        sentence.append(LemmaData(form=form, pos=pos))
                    else:
                        sentence.append(LemmaData(form=form, pos=pos, lemma=lemma))
                elif SGML_TAG_RE.fullmatch(line) is not None:
                    sentence.append(LemmaData(form=line))
                else:
                    logging.warning(f'Unexpected number of tokens in line: {line_tokens}')

    if sentence:
        yield sentence


def parse_polyglot_lemmas(tokens: Iterable[List[LemmaData]]) -> Iterable[Doc[str]]:
    doc: Optional[Doc[str]] = None
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
        if token['lemma'] == '_':
            yield LemmaData(form=token['form'], pos=token['upos'])
        else:
            yield LemmaData(form=token['form'], pos=token['upos'], lemma=token['lemma'])


def parse_udpipe(lang: str, input_path: PathLike, output_path: PathLike):
    with open(input_path, encoding='utf-8') as f:
        save_polyglot(output_path, _parse_udpipe(lang, f))


def _parse_udpipe(lang: str, f: TextIO) -> Iterable[Doc[str]]:
    if lang == 'ko':
        return parse_polyglot_lemmas(
            [
                LemmaData(
                    form=token['form'],
                    lemma=(
                        token['lemma'].strip('+').split('+')[0]
                        if (
                            token['lemma'] is not None and
                            token['xpos'] is not None and
                            '+' in token['xpos']
                        ) else token['lemma']
                    ) if token['lemma'] != '_' else None,
                    pos=token['upos']
                )
                for token in sentence
            ]
            for sentence in conllu.parse_incr(f)
        )
    else:
        return parse_polyglot_lemmas(
            list(_parse_conllu_sentence(sentence))
            for sentence in conllu.parse_incr(f)
        )
