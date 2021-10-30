import re
from dataclasses import dataclass
from os import PathLike
from random import sample
from typing import Callable, Iterable, List, Optional, TypeVar

DOC_ID_RE = re.compile(r'\[\[(?P<doc_id>\d+)\]\]')
DOC_ID_NUM_TOKENS = 5

T = TypeVar('T')


def get_doc_id(line: str) -> Optional[str]:
    match = DOC_ID_RE.fullmatch(line)
    if match is None:
        return None
    else:
        return match.group('doc_id')


def consume_doc_id_tokens(tokens: List[T], key=Optional[Callable[[T], str]]) -> Optional[str]:
    if key is None:
        def _key(t: str) -> str:
            return t
        key = _key

    if len(tokens) >= DOC_ID_NUM_TOKENS:
        doc_id = get_doc_id(''.join(key(t) for t in tokens[-DOC_ID_NUM_TOKENS:]))
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


def subsample(input_path: PathLike, output_path: PathLike, max_num_docs: int):
    doc_ids = set(sample([doc.doc_id for doc in load_polyglot(input_path)], k=max_num_docs))
    save_polyglot(output_path, (doc for doc in load_polyglot(input_path) if doc.doc_id in doc_ids))
