import gzip
import logging
import collections
from difflib import unified_diff
from math import log
from os import PathLike
from pathlib import PurePath
from typing import Counter, Dict, Iterable, Iterator, List, Optional, NamedTuple, Set, TypeVar

import numpy as np

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


def compute_topic_assignments(topic_state_path: PathLike, topic_assignments_path: PathLike):
    np.save(
        topic_assignments_path,
        np.array([
            ta.topic
            for doc in TopicState(topic_state_path).docs
            for ta in doc.tokens
        ], dtype=np.uint))


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
        stop_list_paths: Optional[List[PathLike]] = None) -> List[List[str]]:
    stop_words = load_stop_words(stop_list_paths)

    topic_keys = []
    with open(input_path, encoding='utf-8') as f:
        for line in f:
            (_, _, keys_str) = line.strip().split('\t')
            keys = [k for k in keys_str.split() if k not in stop_words]
            if len(keys) < num_keys:
                raise Exception(
                    f'Less than {num_keys} keys in keys file {input_path}'
                    f'using stop lists {stop_list_paths}')
            topic_keys.append(keys[:num_keys])

    return topic_keys


def collect_keys(input_paths: List[PathLike], output_path: PathLike):
    keys = set()
    for input_path in input_paths:
        with open(input_path, encoding='utf-8') as f:
            for line in f:
                keys.update(line.split('\t')[-1].split(' '))

    with open(output_path, mode='w', encoding='utf-8') as f:
        for key in sorted(keys):
            f.write(key + '\n')


def filter_keys(
        input_path: PathLike,
        output_path: PathLike,
        stop_list_paths: Optional[List[PathLike]] = None):
    stop_words = load_stop_words(stop_list_paths)

    with open(input_path) as in_f, open(output_path, mode='w') as out_f:
        for line in in_f:
            (index_str, alpha_str, keys_str) = line.strip().split('\t')
            keys_str = ' '.join([key for key in keys_str.split() if key not in stop_words])
            out_f.write('\t'.join((index_str, alpha_str, keys_str)) + '\n')


def load_stop_words(stop_list_paths: Optional[List[PathLike]]) -> Set[str]:
    stop_words = set()
    if stop_list_paths is not None:
        for stop_list_path in stop_list_paths:
            stop_words.update(load_word_list(stop_list_path))
    return stop_words


def infer_topic_keys(
        topic_state: TopicState,
        untreated_topic_state: TopicState,
        num_keys: int = DEFAULT_NUM_KEYS,
        untreated_stop_list_path: Optional[PathLike] = None) -> List[List[str]]:
    if untreated_stop_list_path is not None:
        untreated_stop_words = set(load_word_list(untreated_stop_list_path))
    else:
        untreated_stop_words = set()

    num_topics = topic_state.num_topics
    topic_words: List[Counter[str]] = [collections.Counter() for topic_num in range(num_topics)]
    for (doc, untr_doc) in zip(topic_state.docs, untreated_topic_state.docs):
        for (ta, untr_ta) in zip(doc.tokens, untr_doc.tokens):
            if untr_ta.word not in untreated_stop_words:
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
        num_keys: int = DEFAULT_NUM_KEYS,
        stop_list_path: Optional[PathLike] = None) -> Dict[str, float]:
    topic_state = TopicState(topic_state_path)
    stop_list_paths = ([stop_list_path] if stop_list_path is not None else None)
    return dict(coherence=_compute_coherence(
        load_corpus_summary(corpus_summary_path),
        load_topic_keys(topic_keys_path, num_keys=num_keys, stop_list_paths=stop_list_paths),
        topic_state.beta,
    ))


def compute_coherence_treated(
        untreated_corpus_summary_path: PathLike,
        untreated_topic_state_path: PathLike,
        topic_state_path: PathLike,
        num_keys: int = DEFAULT_NUM_KEYS,
        untreated_stop_list_path: Optional[PathLike] = None) -> Dict[str, float]:
    topic_state = TopicState(topic_state_path)
    return dict(coherence=_compute_coherence(
        load_corpus_summary(untreated_corpus_summary_path),
        infer_topic_keys(
            topic_state,
            TopicState(untreated_topic_state_path),
            num_keys=num_keys,
            untreated_stop_list_path=untreated_stop_list_path,
        ),
        topic_state.beta
    ))


def compute_entropy(pmf: np.ndarray) -> float:
    pmf_pos = pmf[pmf > 0]
    return - (pmf_pos * np.log(pmf_pos)).sum()


def compute_pmf(counts: np.ndarray) -> np.ndarray:
    return counts / counts.sum()


def compute_mi(entropy_x: float, entropy_y: float, entropy_xy: float) -> float:
    return entropy_x + entropy_y - entropy_xy


def compute_voi(joint_counts: np.ndarray) -> float:
    entropy_x = compute_entropy(compute_pmf(joint_counts.sum(axis=0)))
    entropy_y = compute_entropy(compute_pmf(joint_counts.sum(axis=1)))
    mi = compute_mi(entropy_x, entropy_y, compute_entropy(compute_pmf(joint_counts)))
    return entropy_x + entropy_y - 2 * mi


def compute_joint_topic_assignment_counts(
        topic_assignments_1: np.ndarray,
        topic_assignments_2: np.ndarray) -> np.ndarray:
    if topic_assignments_1.shape != topic_assignments_2.shape:
        raise Exception(
            'Expected same topic assignment shapes but got '
            f'{topic_assignments_1.shape} and {topic_assignments_2.shape}')
    if len(topic_assignments_1.shape) != 1:
        raise Exception(
            f'Expected flat topic assignments but got shape {topic_assignments_1.shape}')
    num_topics_1 = int(topic_assignments_1.max() + 1)
    num_topics_2 = int(topic_assignments_2.max() + 1)
    counts: np.ndarray = np.zeros((num_topics_1, num_topics_2))
    for i in range(topic_assignments_1.shape[0]):
        counts[topic_assignments_1[i], topic_assignments_2[i]] += 1

    return counts


def _compute_topic_assignment_voi(
        topic_assignments_1: np.ndarray,
        topic_assignments_2: np.ndarray) -> float:
    return compute_voi(compute_joint_topic_assignment_counts(
        topic_assignments_1,
        topic_assignments_2,
    ))


def compute_topic_assignment_voi(
        topic_assignments_1_path: PathLike,
        topic_assignments_2_path: PathLike) -> Dict[str, float]:
    return dict(voi=_compute_topic_assignment_voi(
        np.load(topic_assignments_1_path),
        np.load(topic_assignments_2_path),
    ))


def collect_subtask_scores(scores, output_path):
    with open(output_path, encoding='utf-8', mode='w') as f:
        f.write('subtask\tscore\n')
        for (subtask, score) in scores.items():
            f.write(f'{subtask}\t{score}\n')
