import re
import collections
from dataclasses import dataclass
from itertools import product
from functools import cached_property
from os import PathLike
from pathlib import PurePath
from random import sample
from typing import Counter, Dict, Generic, Iterable, Iterator, List, Optional, Tuple, TypeVar

DOC_ID_RE = re.compile(r'\[\[(?P<doc_id>\d+)\]\]')

T = TypeVar('T')


@dataclass
class Doc(Generic[T]):
    doc_id: str
    sections: List[List[T]]

    @property
    def num_tokens(self) -> int:
        return len(self.tokens)

    @property
    def tokens(self) -> List[T]:
        return [
            token
            for section in self.sections
            for token in section
        ]

    @property
    def text(self) -> str:
        return ''.join(
            ' '.join(str(t) for t in section) + '\n'
            for section in self.sections
        )

    @property
    def flat_text(self) -> str:
        return ' '.join(str(t) for t in self.tokens)

    def to_mallet(self, cls: str) -> str:
        return f'{self.doc_id} {cls} {self.flat_text}'

    def to_polyglot(self) -> str:
        return f'[[{self.doc_id}]]\n{self.text}'


@dataclass
class Corpus(Generic[T]):
    corpus_id: str
    docs: Iterable[Doc[T]]

    @cached_property
    def vocab(self) -> List[T]:
        _vocab: List[T] = []
        for doc in self.docs:
            for section in doc.sections:
                for word in section:
                    if word not in _vocab:
                        _vocab.append(word)

        return _vocab

    @cached_property
    def word_ids(self) -> Dict[T, int]:
        return dict((word, word_id) for (word_id, word) in enumerate(self.vocab))

    @cached_property
    def word_occur(self) -> Counter[T]:
        return Counter(dict(
            (word1, count) for ((word1, word2), count) in self.word_cooccur.items()
            if word1 == word2
        ))

    @cached_property
    def word_cooccur(self) -> Counter[Tuple[T, T]]:
        counter: Counter[Tuple[T, T]] = collections.Counter()
        for doc in self.docs:
            for (word1, word2) in product(set(doc.tokens), repeat=2):
                counter[(word1, word2)] += 1

        return counter


class PolyglotCorpus(Corpus[str], Iterable[Doc[str]]):
    corpus_path: PathLike

    def __init__(self, corpus_path: PathLike):
        self.corpus_path = corpus_path
        super().__init__(PurePath(corpus_path).name, self)

    def __iter__(self) -> Iterator[Doc[str]]:
        return iter(load_polyglot(self.corpus_path))


def get_doc_id(line: str) -> Optional[str]:
    match = DOC_ID_RE.fullmatch(line)
    if match is None:
        return None
    else:
        return match.group('doc_id')


def load_polyglot(input_path: PathLike) -> Iterable[Doc[str]]:
    with open(input_path, encoding='utf-8') as f:
        prev_line = None
        doc: Optional[Doc[str]] = None
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


def save_polyglot(output_path: PathLike, docs: Iterable[Doc[str]]):
    with open(output_path, encoding='utf-8', mode='w') as f:
        for doc in docs:
            f.write(doc.to_polyglot() + '\n')


def subsample(input_path: PathLike, output_path: PathLike, max_num_docs: int):
    doc_ids = set(sample([doc.doc_id for doc in load_polyglot(input_path)], k=max_num_docs))
    save_polyglot(output_path, (doc for doc in load_polyglot(input_path) if doc.doc_id in doc_ids))


def convert_polyglot_to_mallet(lang, input_path, output_path):
    with open(output_path, encoding='utf-8', mode='w') as f:
        for doc in load_polyglot(input_path):
            f.write(doc.to_mallet(lang) + '\n')
