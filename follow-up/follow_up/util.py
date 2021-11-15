import collections
import json
import re
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


@dataclass(frozen=True)
class CorpusSummary(Generic[T]):
    corpus_id: str
    num_docs: int
    vocab: List[T]
    word_cooccur: Counter[Tuple[T, T]]

    @cached_property
    def word_index(self) -> Dict[T, int]:
        return dict((word, i) for (i, word) in enumerate(self.vocab))

    @cached_property
    def word_occur(self) -> Counter[T]:
        return collections.Counter(dict(
            (word1, c) for ((word1, word2), c) in self.word_cooccur.items()
            if word1 == word2
        ))

    def save(self, path: PathLike):
        with open(path, mode='w') as f:
            json.dump(
                dict(
                    corpus_id=self.corpus_id,
                    num_docs=self.num_docs,
                    vocab=self.vocab,
                    word_cooccur=dict(self.word_cooccur),
                ),
                f
            )


def load_corpus_summary(path: PathLike) -> CorpusSummary:
    with open(path) as f:
        archive = json.load(f)
    return CorpusSummary(
        corpus_id=archive['corpus_id'],
        num_docs=archive['num_docs'],
        vocab=archive['vocab'],
        word_cooccur=collections.Counter(archive['word_cooccur']),
    )


@dataclass(frozen=True)
class Corpus(Generic[T]):
    corpus_id: str
    docs: Iterable[Doc[T]]

    @cached_property
    def summary(self) -> CorpusSummary[T]:
        num_docs: int = 0
        vocab: List[T] = []
        word_cooccur: Counter[Tuple[T, T]] = collections.Counter()
        for doc in self.docs:
            num_docs += 1
            for word in doc.tokens:
                if word not in vocab:
                    vocab.append(word)
            for (word1, word2) in product(set(doc.tokens), repeat=2):
                word_cooccur[(word1, word2)] += 1

        return CorpusSummary(
            corpus_id=self.corpus_id,
            num_docs=num_docs,
            vocab=vocab,
            word_cooccur=word_cooccur,
        )


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


def convert_polyglot_to_mallet(lang: str, input_path: PathLike, output_path: PathLike):
    with open(output_path, encoding='utf-8', mode='w') as f:
        for doc in load_polyglot(input_path):
            f.write(doc.to_mallet(lang) + '\n')


def lowercase_polyglot(input_path: PathLike, output_path: PathLike):
    save_polyglot(output_path, (
        Doc(doc.doc_id, [[token.lower() for token in section] for section in doc.sections])
        for doc in load_polyglot(input_path)
    ))


def summarize_corpus(input_path: PathLike, output_path: PathLike):
    PolyglotCorpus(input_path).summary.save(output_path)


def compute_common_words(input_path: PathLike, output_path: PathLike, num_words: int):
    with open(output_path, encoding='utf-8', mode='w') as f:
        for (word, _) in load_corpus_summary(input_path).word_occur.most_common(num_words):
            f.write(word + '\n')
