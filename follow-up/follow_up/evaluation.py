import gzip
import logging
from collections import Counter
from dataclasses import dataclass
from difflib import unified_diff
from math import log
from os import PathLike
from pathlib import PurePath
from typing import Any, List, Optional

from .util import Corpus, Doc, load_polyglot_corpus

DEFAULT_NUM_KEYS = 5


@dataclass
class TokenAssignment(object):
    word: str
    topic: int


@dataclass
class TopicState(object):
    alpha: List[float]
    beta: float
    assignments: List[Doc[TokenAssignment]]


def check_corpus_alignment(corpus1_path: PathLike, corpus2_path: PathLike):
    return _check_corpus_alignment(
        load_polyglot_corpus(corpus1_path),
        load_polyglot_corpus(corpus2_path)
    )


def _check_corpus_alignment(corpus1: Corpus, corpus2: Corpus):
    corpus1_doc_infos = [f'{doc.doc_id} {doc.num_tokens}' for doc in corpus1.docs]
    corpus2_doc_infos = [f'{doc.doc_id} {doc.num_tokens}' for doc in corpus2.docs]
    if corpus1_doc_infos != corpus2_doc_infos:
        logging.warning(
            f'Corpora {corpus1.corpus_id}, {corpus2.corpus_id} do not align')
        for diff_line in unified_diff(
                corpus1_doc_infos, corpus2_doc_infos,
                fromfile=corpus1.corpus_id, tofile=corpus2.corpus_id):
            logging.warning(diff_line)
        raise Exception(
            f'Corpora {corpus1.corpus_id}, {corpus2.corpus_id} do not align')


def check_token_assignment_alignment(
        corpus_path: PathLike,
        topic_state_path: PathLike):
    corpus = load_polyglot_corpus(corpus_path)
    token_assignments_corpus: Corpus[TokenAssignment] = Corpus(
        PurePath(topic_state_path).name,
        load_topic_state(topic_state_path).assignments
    )
    # the token assignments file doesn't contain doc ids, so we just copy them from corpus
    for (ta_doc, doc) in zip(token_assignments_corpus.docs, corpus.docs):
        ta_doc.doc_id = doc.doc_id
    return _check_corpus_alignment(corpus, token_assignments_corpus)


def load_topic_state(input_path: PathLike) -> TopicState:
    alpha: Optional[List[float]] = None
    beta: Optional[float] = None
    docs: List[Doc[TokenAssignment]] = []
    alpha_prefix = '#alpha : '
    beta_prefix = '#beta : '
    with gzip.open(input_path, mode='rt', encoding='utf-8') as f:
        for line in f:
            if line.startswith(alpha_prefix):
                alpha = [float(t) for t in line[len(alpha_prefix):].strip().split()]
            elif line.startswith(beta_prefix):
                beta = float(line[len(beta_prefix):].strip())
            elif not line.startswith('#'):
                [doc_num_str, _1, _2, _3, word, topic_num_str] = line.strip().split()
                doc_num = int(doc_num_str)
                topic_num = int(topic_num_str)
                while doc_num >= len(docs):
                    docs.append(Doc(str(len(docs)), [[]]))
                docs[doc_num].sections[0].append(TokenAssignment(word=word, topic=topic_num))

    if alpha is None:
        raise Exception(f'Failed to extract alpha from topic state file {input_path}')
    elif beta is None:
        raise Exception(f'Failed to extract beta from topic state file {input_path}')
    else:
        return TopicState(alpha=alpha, beta=beta, assignments=docs)


def load_topic_keys(input_path: PathLike, num_keys: int = DEFAULT_NUM_KEYS) -> List[List[str]]:
    topic_keys = []
    with open(input_path, encoding='utf-8') as f:
        for line in f:
            (_, _, keys_str) = line.strip().split('\t')
            keys = keys_str.split()[:num_keys]
            if len(keys) != num_keys:
                raise Exception(f'Failed to extract {num_keys} keys from keys file {input_path}')
            topic_keys.append(keys)

    return topic_keys


def infer_topic_keys(
        token_assignment_docs: List[Doc[TokenAssignment]],
        num_topics: int,
        num_keys: int = DEFAULT_NUM_KEYS) -> List[List[str]]:
    return [
        [
            word
            for (word, _) in Counter(
                token_assignment.word
                for doc in token_assignment_docs
                for token_assignment in doc.tokens
                if token_assignment.topic == topic_num
            ).most_common(num_keys)
        ]
        for topic_num in range(num_topics)
    ]


def compute_coherence(
        corpus: Corpus,
        topic_keys_per_topic: List[List[str]],
        beta: float = 1.) -> float:
    return sum(
        sum(
            log(
                (corpus.word_cooccur[(key2, key1)] + beta) /
                (corpus.word_occur[key2] + beta)
            )
            for key1 in topic_keys[1:]
            for key2 in topic_keys[:-1]
        )
        for topic_keys in topic_keys_per_topic
    ) / len(topic_keys_per_topic)


def print_to_optional_file(s: Any, path: Optional[PathLike], *args, **kwargs):
    if path is not None:
        with open(path, *args, **kwargs) as f:
            print(s, file=f)
    else:
        print(s)


def print_coherence(
        corpus_path: PathLike,
        topic_keys_path: PathLike,
        topic_state_path: PathLike,
        output_path: Optional[PathLike] = None,
        num_keys: int = DEFAULT_NUM_KEYS):
    coherence = compute_coherence(
        load_polyglot_corpus(corpus_path),
        load_topic_keys(topic_keys_path, num_keys=num_keys),
        load_topic_state(topic_state_path).beta
    )
    print_to_optional_file(coherence, output_path, mode='w')


def print_coherence_lemmatized(
        corpus_path: PathLike,
        topic_keys_path: PathLike,
        topic_state_path: PathLike,
        output_path: Optional[PathLike] = None,
        num_keys: int = DEFAULT_NUM_KEYS):
    topic_state = load_topic_state(topic_state_path)
    coherence = compute_coherence(
        load_polyglot_corpus(corpus_path),
        infer_topic_keys(
            topic_state.assignments,
            num_topics=len(topic_state.alpha),
            num_keys=num_keys
        ),
        topic_state.beta
    )
    print_to_optional_file(coherence, output_path, mode='w')
