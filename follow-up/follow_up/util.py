import re
from dataclasses import dataclass
from os import PathLike
from typing import Iterable, List, Optional

DOC_ID_RE = re.compile(r'\[\[(?P<doc_id>\d+)\]\]')
DOC_ID_NUM_TOKENS = 5


def get_doc_id(line: str) -> Optional[str]:
    match = DOC_ID_RE.fullmatch(line)
    if match is None:
        return None
    else:
        return match.group('doc_id')


def consume_doc_id_tokens(tokens: List[str]) -> Optional[str]:
    if len(tokens) >= DOC_ID_NUM_TOKENS:
        doc_id = get_doc_id(''.join(tokens[-DOC_ID_NUM_TOKENS:]))
        if doc_id is None:
            return None
        else:
            for _ in range(DOC_ID_NUM_TOKENS):
                tokens.pop()
            return doc_id
    else:
        return None


@dataclass
class Doc(object):
    doc_id: str
    sections: List[List[str]]

    @property
    def tokens(self) -> List[str]:
        return [
            token
            for section in self.sections
            for token in section
        ]

    @property
    def text(self) -> str:
        return ''.join(
            ' '.join(section) + '\n'
            for section in self.sections
        )

    @property
    def flat_text(self) -> str:
        return ' '.join(self.tokens)

    def to_mallet(self, cls: str) -> str:
        return f'{self.doc_id} {cls} {self.flat_text}'

    def to_polyglot(self) -> str:
        return f'[[{self.doc_id}]]\n{self.text}'


def load_polyglot(input_path: PathLike) -> Iterable[Doc]:
    with open(input_path, encoding='utf-8') as f:
        prev_line = None
        doc = None
        for line in f:
            line = line.strip()
            doc_id = get_doc_id(line)
            if not prev_line and doc_id is not None:
                if doc is not None and doc.tokens:
                    yield doc
                doc = Doc(doc_id, [])
            elif doc is not None and line:
                doc.sections.append(line.split())

            prev_line = line

        if doc is not None and doc.tokens:
            yield doc


def save_polyglot(output_path: PathLike, docs: Iterable[Doc]):
    with open(output_path, encoding='utf-8', mode='w') as f:
        for doc in docs:
            f.write(doc.to_polyglot() + '\n')


def parse_polyglot_tokens(tokens: Iterable[str]) -> Iterable[Doc]:
    doc_id = None
    doc_tokens = []
    for token in tokens:
        doc_tokens.append(token)

        new_doc_id = consume_doc_id_tokens(doc_tokens)
        if new_doc_id is not None:
            if doc_id is not None and doc_tokens:
                yield Doc(doc_id, [doc_tokens])

            doc_id = new_doc_id
            doc_tokens = []

    if doc_id is not None and doc_tokens:
        yield Doc(doc_id, [doc_tokens])
