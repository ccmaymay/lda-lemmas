import logging
from collections import Counter
from difflib import unified_diff
from math import log
from os import PathLike
from typing import List, NamedTuple

from .util import Corpus


class TokenAssignment(NamedTuple):
    word: str
    topic: int


def check_corpus_alignment(corpus1_path: PathLike, corpus2_path: PathLike):
    corpus1 = Corpus.load(corpus1_path)
    corpus2 = Corpus.load(corpus2_path)

    corpus1_doc_infos = [f'{doc.doc_id} {doc.num_tokens}' for doc in corpus1.docs]
    corpus2_doc_infos = [f'{doc.doc_id} {doc.num_tokens}' for doc in corpus2.docs]
    if corpus1_doc_infos != corpus2_doc_infos:
        logging.warning(
            f'Corpora {corpus1.name}, {corpus2.name} do not align')
        for diff_line in unified_diff(
                corpus1_doc_infos, corpus2_doc_infos,
                fromfile=corpus1.name, tofile=corpus2.name):
            logging.warning(diff_line)
        raise Exception(
            f'Corpora {corpus1.name}, {corpus2.name} do not align')


def check_corpus_token_assignment_alignment(
        corpus: Corpus,
        token_assignments: List[List[TokenAssignment]]):
    raise NotImplementedError()


def load_token_assignments(input_path: PathLike) -> List[List[TokenAssignment]]:
    token_assignments: List[List[TokenAssignment]] = []
    with open(input_path, encoding='utf-8') as f:
        for line in f:
            if not line.startswith('#'):
                [doc_num_str, _1, _2, _3, word, topic_num_str] = line.strip().split()
                doc_num = int(doc_num_str)
                topic_num = int(topic_num_str)
                while doc_num >= len(token_assignments):
                    token_assignments.append([])
                token_assignments[doc_num].append(TokenAssignment(word=word, topic=topic_num))

    return token_assignments


def infer_topic_keys(
        token_assignments: List[List[TokenAssignment]],
        num_topics: int,
        num_keys=5) -> List[List[str]]:
    return [
        [
            word
            for (word, _) in Counter(
                token_assignment.word
                for doc_token_assignments in token_assignments
                for token_assignment in doc_token_assignments
                if token_assignment.topic == topic_num
            ).most_common(num_keys)
        ]
        for topic_num in range(num_topics)
    ]


def coherence(
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
