import gzip
import logging
import collections
from difflib import unified_diff
from math import log
from os import PathLike
from pathlib import PurePath
from typing import (
    Counter, Dict, Iterable, Iterator, List, Literal, Optional, NamedTuple, Tuple, TypeVar,
    overload,
)

from .util import Corpus, CorpusSummary, Doc, PolyglotCorpus, load_corpus_summary, load_word_list

DEFAULT_NUM_KEYS = 5

T = TypeVar('T')
X = TypeVar('X')
Y = TypeVar('Y')


class TokenAssignment(NamedTuple):
    word: str
    topic: int


class TopicState(Corpus[TokenAssignment], Iterable[Doc[TokenAssignment]]):
    topic_state_path: PathLike
    _alpha: Optional[List[float]] = None
    _beta: Optional[float] = None

    def __init__(self, topic_state_path):
        self.topic_state_path = topic_state_path
        super().__init__(PurePath(topic_state_path).name, self)

    def __iter__(self) -> Iterator[Doc[TokenAssignment]]:
        return iter(load_token_assignments(self.topic_state_path))

    def _load(self):
        alpha_prefix = '#alpha : '
        beta_prefix = '#beta : '
        with gzip.open(self.topic_state_path, mode='rt', encoding='utf-8') as f:
            for line in f:
                if line.startswith(alpha_prefix):
                    self._alpha = [float(t) for t in line[len(alpha_prefix):].strip().split()]
                elif line.startswith(beta_prefix):
                    self._beta = float(line[len(beta_prefix):].strip())
                if self._alpha is not None and self._beta is not None:
                    break

    @property
    def alpha(self) -> List[float]:
        if self._alpha is None:
            self._load()
        if self._alpha is None:
            raise Exception(f'Failed to read alpha from topic state file {self.topic_state_path}')
        return self._alpha

    @property
    def beta(self) -> float:
        if self._beta is None:
            self._load()
        if self._beta is None:
            raise Exception(f'Failed to read beta from topic state file {self.topic_state_path}')
        return self._beta

    @property
    def num_topics(self) -> int:
        return len(self.alpha)


def check_corpus_alignment(corpus1_path: PathLike, corpus2_path: PathLike):
    return _check_corpus_alignment(PolyglotCorpus(corpus1_path), PolyglotCorpus(corpus2_path))


def _check_corpus_alignment(corpus1: Corpus, corpus2: Corpus, check_doc_ids=True):
    if check_doc_ids:
        corpus1_doc_infos = [f'{doc.doc_id} {doc.num_tokens}' for doc in corpus1.docs]
        corpus2_doc_infos = [f'{doc.doc_id} {doc.num_tokens}' for doc in corpus2.docs]
    else:
        corpus1_doc_infos = [f'{i} {doc.num_tokens}' for (i, doc) in enumerate(corpus1.docs)]
        corpus2_doc_infos = [f'{i} {doc.num_tokens}' for (i, doc) in enumerate(corpus2.docs)]

    if corpus1_doc_infos != corpus2_doc_infos:
        logging.warning(
            f'Corpora {corpus1.corpus_id}, {corpus2.corpus_id} do not align')
        for diff_line in unified_diff(
                corpus1_doc_infos, corpus2_doc_infos,
                fromfile=corpus1.corpus_id, tofile=corpus2.corpus_id):
            logging.warning(diff_line)
        raise Exception(
            f'Corpora {corpus1.corpus_id}, {corpus2.corpus_id} do not align')


def check_token_assignment_alignment(corpus_path: PathLike, topic_state_path: PathLike):
    return _check_corpus_alignment(
        PolyglotCorpus(corpus_path),
        TopicState(topic_state_path),
        check_doc_ids=False
    )


def load_token_assignments(input_path: PathLike) -> Iterable[Doc[TokenAssignment]]:
    doc: Optional[Doc[TokenAssignment]] = None
    prev_doc_num: int = -1
    with gzip.open(input_path, mode='rt', encoding='utf-8') as f:
        for line in f:
            if not line.startswith('#'):
                [doc_num_str, _1, _2, _3, word, topic_num_str] = line.strip().split()
                doc_num = int(doc_num_str)
                topic_num = int(topic_num_str)
                if doc_num != prev_doc_num:
                    if doc_num != prev_doc_num + 1:
                        raise Exception(
                            'Expected successive document numbers, '
                            f'but got {prev_doc_num} followed by {doc_num}')
                    if doc is not None:
                        yield doc
                    doc = Doc(str(doc_num), [[]])
                    prev_doc_num = doc_num

                if doc is None:
                    raise Exception(
                        'Encountered token assignment before first doc initialized... '
                        'is first doc id -1?')

                doc.sections[0].append(TokenAssignment(word=word, topic=topic_num))

    if doc is not None:
        yield doc


def load_topic_keys(
        input_path: PathLike,
        num_keys: int = DEFAULT_NUM_KEYS,
        stop_list_path: Optional[PathLike] = None) -> List[List[str]]:
    if stop_list_path is not None:
        stop_words = set(load_word_list(stop_list_path))
    else:
        stop_words = set()

    topic_keys = []
    with open(input_path, encoding='utf-8') as f:
        for line in f:
            (_, _, keys_str) = line.strip().split('\t')
            keys = [k for k in keys_str.split() if k not in stop_words]
            if len(keys) < num_keys:
                raise Exception(
                    f'Less than {num_keys} keys in keys file {input_path}'
                    f'using stop list {stop_list_path}')
            topic_keys.append(keys[:num_keys])

    return topic_keys


def infer_topic_keys(
        topic_state: TopicState,
        untreated_topic_state: TopicState,
        num_keys: int = DEFAULT_NUM_KEYS,
        stop_list_path: Optional[PathLike] = None) -> List[List[str]]:
    if stop_list_path is not None:
        stop_words = set(load_word_list(stop_list_path))
    else:
        stop_words = set()

    num_topics = topic_state.num_topics
    topic_words: List[Counter[str]] = [collections.Counter() for topic_num in range(num_topics)]
    for (doc, untr_doc) in zip(topic_state.docs, untreated_topic_state.docs):
        for (ta, untr_ta) in zip(doc.tokens, untr_doc.tokens):
            if untr_ta.word not in stop_words:
                topic_words[ta.topic][untr_ta.word] += 1
    return [
        [word for (word, _) in topic_words[topic_num].most_common(num_keys)]
        for topic_num in range(num_topics)
    ]


def _compute_coherence(
        corpus_summary: CorpusSummary[T],
        topic_keys_per_topic: List[List[T]],
        beta: float = 1.) -> float:
    return sum(
        sum(
            log(
                (corpus_summary.word_cooccur_counter[(topic_keys[ell], topic_keys[m])] + beta) /
                (corpus_summary.word_occur_counter[topic_keys[ell]] + beta)
            )
            for m in range(1, len(topic_keys))
            for ell in range(m)
        )
        for topic_keys in topic_keys_per_topic
    ) / len(topic_keys_per_topic)


def compute_coherence(
        corpus_summary_path: PathLike,
        topic_keys_path: PathLike,
        topic_state_path: PathLike,
        num_keys: int = DEFAULT_NUM_KEYS) -> Dict[str, float]:
    return dict(coherence=_compute_coherence(
        load_corpus_summary(corpus_summary_path),
        load_topic_keys(topic_keys_path, num_keys=num_keys),
        TopicState(topic_state_path).beta
    ))


def compute_coherence_treated(
        untreated_corpus_summary_path: PathLike,
        untreated_topic_state_path: PathLike,
        topic_state_path: PathLike,
        num_keys: int = DEFAULT_NUM_KEYS) -> Dict[str, float]:
    topic_state = TopicState(topic_state_path)
    return dict(coherence=_compute_coherence(
        load_corpus_summary(untreated_corpus_summary_path),
        infer_topic_keys(
            topic_state,
            TopicState(untreated_topic_state_path),
            num_keys=num_keys
        ),
        topic_state.beta
    ))


def compute_entropy(pmf: Dict[X, float]) -> float:
    return sum(-p * log(p) for p in pmf.values())


def compute_pmf(counts: Dict[X, int]) -> Dict[X, float]:
    total = sum(counts.values())
    return dict((x, c / total) for (x, c) in counts.items())


def compute_mi(entropy_x: float, entropy_y: float, entropy_xy: float) -> float:
    return entropy_x + entropy_y - entropy_xy


def compute_voi(joint_counts: Dict[Tuple[X, Y], int]) -> float:
    entropy_x = compute_entropy(compute_pmf(compute_marginal_counts(joint_counts, 0)))
    entropy_y = compute_entropy(compute_pmf(compute_marginal_counts(joint_counts, 1)))
    mi = compute_mi(entropy_x, entropy_y, compute_entropy(compute_pmf(joint_counts)))
    return entropy_x + entropy_y - 2 * mi


def compute_joint_topic_assignment_counts(
        topic_state_1: TopicState,
        topic_state_2: TopicState) -> Dict[Tuple[int, int], int]:
    counts: Counter[Tuple[int, int]] = collections.Counter()
    for (doc1, doc2) in zip(topic_state_1.docs, topic_state_2.docs):
        for (ta1, ta2) in zip(doc1.tokens, doc2.tokens):
            counts[(ta1.topic, ta2.topic)] += 1

    return counts


@overload
def compute_marginal_counts(
        joint_counts: Dict[Tuple[X, Y], int],
        index: Literal[0]) -> Dict[X, int]:
    pass


@overload
def compute_marginal_counts(
        joint_counts: Dict[Tuple[X, Y], int],
        index: Literal[1]) -> Dict[Y, int]:
    pass


def compute_marginal_counts(
        joint_counts,
        index):
    counts = collections.Counter()
    for (topic_pair, count) in joint_counts.items():
        counts[topic_pair[index]] += count

    return counts


def _compute_topic_assignment_voi(topic_state_1: TopicState, topic_state_2: TopicState) -> float:
    return compute_voi(compute_joint_topic_assignment_counts(topic_state_1, topic_state_2))


def compute_topic_assignment_voi(
        topic_state_1_path: PathLike,
        topic_state_2_path: PathLike) -> Dict[str, float]:
    return dict(voi=_compute_topic_assignment_voi(
        TopicState(topic_state_1_path),
        TopicState(topic_state_2_path),
    ))


def collect_subtask_scores(scores, output_path):
    with open(output_path, encoding='utf-8', mode='w') as f:
        f.write('subtask\tscore\n')
        for (subtask, score) in scores.items():
            f.write(f'{subtask}\t{score}\n')
