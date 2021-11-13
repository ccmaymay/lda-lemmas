import gzip
import logging
import collections
from dataclasses import dataclass
from difflib import unified_diff
from math import log
from os import PathLike
from pathlib import PurePath
from typing import Any, Counter, Dict, List, Literal, Optional, Tuple, TypeVar, overload

from .util import Corpus, Doc, load_polyglot_corpus

DEFAULT_NUM_KEYS = 5

T = TypeVar('T')
U = TypeVar('U')


@dataclass
class TokenAssignment(object):
    word: str
    topic: int


@dataclass
class TopicState(object):
    alpha: List[float]
    beta: float
    assignments: List[Doc[TokenAssignment]]

    @property
    def num_topics(self) -> int:
        return len(self.alpha)


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
        topic_state: TopicState,
        num_topics: int,
        num_keys: int = DEFAULT_NUM_KEYS) -> List[List[str]]:
    return [
        [
            word
            for (word, _) in collections.Counter(
                token_assignment.word
                for doc in topic_state.assignments
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
            topic_state,
            num_topics=topic_state.num_topics,
            num_keys=num_keys
        ),
        topic_state.beta
    )
    print_to_optional_file(coherence, output_path, mode='w')


def compute_entropy(pmf: Dict[T, float]) -> float:
    return sum(-p * log(p) for p in pmf.values())


def compute_pmf(counts: Dict[T, int]) -> Dict[T, float]:
    total = sum(counts.values())
    return dict((t, c / total) for (t, c) in counts.items())


def compute_mi(entropy_x: float, entropy_y: float, entropy_xy: float) -> float:
    return entropy_x + entropy_y - entropy_xy


def compute_voi(joint_counts: Dict[Tuple[T, U], int]) -> float:
    entropy_x = compute_entropy(compute_pmf(compute_marginal_counts(joint_counts, 0)))
    entropy_y = compute_entropy(compute_pmf(compute_marginal_counts(joint_counts, 1)))
    mi = compute_mi(entropy_x, entropy_y, compute_entropy(compute_pmf(joint_counts)))
    return entropy_x + entropy_y - 2 * mi


def compute_joint_topic_assignment_counts(
        topic_state_1: TopicState,
        topic_state_2: TopicState) -> Dict[Tuple[int, int], int]:
    counts: Counter[Tuple[int, int]] = collections.Counter()
    for (doc1, doc2) in zip(topic_state_1.assignments, topic_state_2.assignments):
        for (ta1, ta2) in zip(doc1.tokens, doc2.tokens):
            counts[(ta1.topic, ta2.topic)] += 1

    return counts


@overload
def compute_marginal_counts(
        joint_counts: Dict[Tuple[T, U], int],
        index: Literal[0]) -> Dict[T, int]:
    pass


@overload
def compute_marginal_counts(
        joint_counts: Dict[Tuple[T, U], int],
        index: Literal[1]) -> Dict[U, int]:
    pass


def compute_marginal_counts(
        joint_counts,
        index):
    counts = collections.Counter()
    for (topic_pair, count) in joint_counts.items():
        counts[topic_pair[index]] += count

    return counts


def compute_topic_assignment_voi(
        topic_state_1: TopicState,
        topic_state_2: TopicState) -> float:
    return compute_voi(compute_joint_topic_assignment_counts(topic_state_1, topic_state_2))


def print_topic_assignment_voi(
        topic_state_1_path: PathLike,
        topic_state_2_path: PathLike,
        output_path: Optional[PathLike] = None):
    voi = compute_topic_assignment_voi(
        load_topic_state(topic_state_1_path),
        load_topic_state(topic_state_2_path),
    )
    print_to_optional_file(voi, output_path, mode='w')
