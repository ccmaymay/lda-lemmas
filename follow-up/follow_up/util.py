import re
from collections import Counter
from dataclasses import dataclass
from itertools import product
from functools import cached_property
from os import PathLike
from pathlib import PurePath
from random import sample
from typing import Callable, Dict, Iterable, List, Optional, TypeVar

DOC_ID_RE = re.compile(r'\[\[(?P<doc_id>\d+)\]\]')
DOC_ID_NUM_TOKENS_LIST = (5, 3, 1)  # [ [ id ] ], [[ id ]], [[id]]

T = TypeVar('T')


@dataclass
class Doc(object):
    doc_id: str
    sections: List[List[str]]

    @property
    def num_tokens(self) -> int:
        return len(self.tokens)

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


@dataclass
class Corpus(object):
    name: str
    docs: List[Doc]

    @cached_property
    def vocab(self) -> List[str]:
        _vocab: List[str] = []
        for doc in self.docs:
            for section in doc.sections:
                for word in section:
                    if word not in _vocab:
                        _vocab.append(word)

        return _vocab

    @cached_property
    def word_ids(self) -> Dict[str, int]:
        return dict((word, word_id) for (word_id, word) in enumerate(self.vocab))

    @cached_property
    def word_occur(self) -> Counter:
        counter: Counter = Counter()
        for doc in self.docs:
            for word in set(doc.tokens):
                counter[word] += 1

        return counter

    @cached_property
    def word_cooccur(self) -> Counter:
        counter: Counter = Counter()
        for doc in self.docs:
            for (word1, word2) in product(set(doc.tokens), repeat=2):
                counter[(word1, word2)] += 1

        return counter

    def save(self, output_path: PathLike):
        save_polyglot(output_path, self.docs)

    @classmethod
    def load(cls, input_path: PathLike):
        return cls(PurePath(input_path).name, list(load_polyglot(input_path)))


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

    for num_tokens in DOC_ID_NUM_TOKENS_LIST:
        if len(tokens) >= num_tokens:
            doc_id = get_doc_id(''.join(key(t) for t in tokens[-num_tokens:]))
            if doc_id is not None:
                for _ in range(num_tokens):
                    tokens.pop()
                return doc_id

    return None


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


def load_topic_state(input_path: PathLike):
    raise NotImplementedError()
