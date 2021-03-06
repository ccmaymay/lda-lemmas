import platform
from itertools import product
from os import PathLike
from pathlib import Path
from typing import Optional

import pycountry  # type: ignore

from follow_up.util import (
    subsample, convert_polyglot_to_mallet, lowercase_polyglot, compute_common_words,
    summarize_corpus, extract_corpus_stats, collect_corpus_stats,
)
from follow_up.evaluation import (
    check_corpus_alignment, check_token_assignment_alignment,
    compute_coherence_treated, compute_topic_assignment_voi, collect_subtask_scores,
    compute_coherence, compute_topic_assignments, collect_keys, filter_keys
)
from follow_up.lemmatization import parse_treetagger, parse_udpipe
from follow_up.translation import translate_words, translate_keys

DATA_ROOT = Path('polyglot')

UDPIPE_ROOT = Path('udpipe')
UDPIPE_MODELS = {
    'en': UDPIPE_ROOT / 'english-ewt-ud-2.5-191206.udpipe',
    'fa': UDPIPE_ROOT / 'persian-seraji-ud-2.5-191206.udpipe',
    'ko': UDPIPE_ROOT / 'korean-kaist-ud-2.5-191206.udpipe',
    'ru': UDPIPE_ROOT / 'russian-syntagrus-ud-2.5-191206.udpipe',
}
if platform.system() == 'Linux':
    UDPIPE_BIN = UDPIPE_ROOT / 'bin-linux64'
elif platform.system() == 'Darwin':
    UDPIPE_BIN = UDPIPE_ROOT / 'bin-osx'
elif platform.system() == 'Windows':
    UDPIPE_BIN = UDPIPE_ROOT / 'bin-win64'
else:
    # For other systems, assume the correct dir has been linked/copied to "bin"
    UDPIPE_BIN = UDPIPE_ROOT / 'bin'

MALLET_ROOT = Path('mallet')
MALLET_PROGRAM = MALLET_ROOT / 'bin' / 'mallet'

MAX_NUM_DOCS = 200000

CASED_DATA_SET_FILENAMES = (
    'sub.txt',
    'sub.lem-treetagger.parsed.txt',
    'sub.lem-udpipe.parsed.txt',
)
DATA_SET_FILENAMES = tuple(
    filename[:-len('.txt')] + '.lower.txt'
    for filename in CASED_DATA_SET_FILENAMES
)

NUM_TOPICS = 100
NUM_ITERATIONS = 1000
NUM_TRIALS = 10
OPTIMIZE_INTERVAL = 10

NUM_STOP_WORDS = 200
MIN_WORD_LENGTH = 4
FILTER_NON_ALPHA = True

LANGUAGES = ('en', 'fa', 'ko', 'ru')
LANGUAGE_NAMES = dict(
    (lang.alpha_2, lang.name.lower())
    for lang in pycountry.languages
    if hasattr(lang, 'alpha_2')
)


def task_untar():
    for lang in LANGUAGES:
        input_path = DATA_ROOT / f'{lang}_wiki_text.tar.lzma'
        output_path = DATA_ROOT / lang / 'full.txt'
        yield {
            'name': lang,
            'file_dep': [input_path],
            'actions': [['tar', '-C', f'{DATA_ROOT}', '-xvJf', f'{input_path}']],
            'targets': [output_path],
        }


def task_subsample():
    for lang in LANGUAGES:
        input_path = DATA_ROOT / lang / 'full.txt'
        output_path = DATA_ROOT / lang / 'sub.txt'
        yield {
            'name': lang,
            'file_dep': [input_path],
            'actions': [(subsample, (), dict(
                input_path=input_path,
                output_path=output_path,
                max_num_docs=MAX_NUM_DOCS,
            ))],
            'targets': [output_path],
        }


def task_lemmatize_treetagger():
    for lang in LANGUAGES:
        lang_name = LANGUAGE_NAMES[lang]
        input_path = DATA_ROOT / lang / 'sub.txt'
        output_path = input_path.with_suffix('.lem-treetagger.txt')
        program_path = f'./tree-tagger-{lang_name}'
        yield {
            'name': lang,
            'file_dep': [input_path],
            'actions': [
                f'{program_path} < {input_path} > {output_path}'
            ],
            'targets': [output_path],
        }


def task_parse_treetagger():
    for lang in LANGUAGES:
        input_path = DATA_ROOT / lang / 'sub.lem-treetagger.txt'
        output_path = input_path.with_suffix('.parsed.txt')
        yield {
            'name': lang,
            'file_dep': [input_path],
            'actions': [(parse_treetagger, (), dict(
                lang=lang,
                input_path=input_path,
                output_path=output_path
            ))],
            'targets': [output_path],
        }


def task_lemmatize_udpipe():
    for lang in LANGUAGES:
        input_path = DATA_ROOT / lang / 'sub.txt'
        output_path = input_path.with_suffix('.lem-udpipe.txt')
        program_path = UDPIPE_BIN / 'udpipe'
        model_path = UDPIPE_MODELS[lang]
        yield {
            'name': lang,
            'file_dep': [input_path, model_path],
            'actions': [[
                f'{program_path}',
                '--tag',
                '--immediate',
                '--input=horizontal',
                f'--outfile={output_path}',
                f'{model_path}',
                f'{input_path}',
            ]],
            'targets': [output_path],
        }


def task_parse_udpipe():
    for lang in LANGUAGES:
        input_path = DATA_ROOT / lang / 'sub.lem-udpipe.txt'
        output_path = input_path.with_suffix('.parsed.txt')
        yield {
            'name': lang,
            'file_dep': [input_path],
            'actions': [(parse_udpipe, (), dict(
                lang=lang,
                input_path=input_path,
                output_path=output_path
            ))],
            'targets': [output_path],
        }


def task_lowercase():
    for lang in LANGUAGES:
        input_paths = [
            DATA_ROOT / lang / filename
            for filename in CASED_DATA_SET_FILENAMES
        ]
        for input_path in input_paths:
            output_path = input_path.with_suffix('.lower.txt')
            name = f'{lang}.{input_path.stem}'
            yield {
                'name': name,
                'file_dep': [input_path],
                'actions': [(lowercase_polyglot, (), dict(
                    input_path=input_path,
                    output_path=output_path
                ))],
                'targets': [output_path],
            }


def task_summarize_corpus():
    for lang in LANGUAGES:
        input_paths = [
            DATA_ROOT / lang / filename
            for filename in DATA_SET_FILENAMES
        ]
        for input_path in input_paths:
            output_path = input_path.with_suffix('.summary.npz')
            name = f'{lang}.{input_path.stem}'
            yield {
                'name': name,
                'file_dep': [input_path],
                'actions': [(summarize_corpus, (), dict(
                    input_path=input_path,
                    output_path=output_path,
                ))],
                'targets': [output_path],
            }


def task_compute_common_words():
    for lang in LANGUAGES:
        corpus_paths = [
            DATA_ROOT / lang / filename
            for filename in DATA_SET_FILENAMES
        ]
        for corpus_path in corpus_paths:
            input_path = corpus_path.with_suffix('.summary.npz')
            output_path = corpus_path.with_suffix('.common-words.txt')
            name = f'{lang}.{corpus_path.stem}'
            yield {
                'name': name,
                'file_dep': [input_path],
                'actions': [(compute_common_words, (), dict(
                    input_path=input_path,
                    output_path=output_path,
                    num_words=NUM_STOP_WORDS,
                ))],
                'targets': [output_path],
            }


def task_check_corpus_alignment():
    for lang in LANGUAGES:
        orig_input_path = DATA_ROOT / lang / DATA_SET_FILENAMES[0]
        input_paths = [
            DATA_ROOT / lang / filename
            for filename in DATA_SET_FILENAMES
        ]
        for input_path in input_paths:
            # Create a trivial task for the original (unlemmatized) corpus to simplify later tasks
            is_non_trivial = (input_path != orig_input_path)
            yield {
                'name': f'{lang}.{input_path.stem}',
                'file_dep': [orig_input_path, input_path] if is_non_trivial else [input_path],
                'actions': [(check_corpus_alignment, (), dict(
                    corpus1_path=orig_input_path,
                    corpus2_path=input_path,
                ))] if is_non_trivial else ['true'],
                'uptodate': [True],  # up-to-date iff action has succeeded
            }


def task_to_mallet():
    for lang in LANGUAGES:
        input_paths = [
            DATA_ROOT / lang / filename
            for filename in DATA_SET_FILENAMES
        ]
        for input_path in input_paths:
            output_path = input_path.with_suffix('.mallet.txt')
            name = f'{lang}.{input_path.stem}'
            yield {
                'name': name,
                'file_dep': [input_path],
                'task_dep': [f'check_corpus_alignment:{name}'],
                'actions': [(convert_polyglot_to_mallet, (), dict(
                    lang=lang,
                    input_path=input_path,
                    output_path=output_path
                ))],
                'targets': [output_path],
            }


def task_mallet_import():
    for lang in LANGUAGES:
        corpus_paths = [
            DATA_ROOT / lang / filename
            for filename in DATA_SET_FILENAMES
        ]
        for corpus_path in corpus_paths:
            name = f'{lang}.{corpus_path.stem}'
            input_path = corpus_path.with_suffix('.mallet.txt')
            output_path = corpus_path.with_suffix('.mallet.dat')
            yield {
                'name': name,
                'file_dep': [input_path],
                'actions': [[
                    f'{MALLET_PROGRAM}',
                    'import-file',
                    '--input', f'{input_path}',
                    '--output', f'{output_path}',
                    '--keep-sequence',
                    '--preserve-case',
                    '--token-regex', '[^ ]+',
                    '--line-regex', '^(\\S+) (\\S+) (.*)$',
                ]],
                'targets': [output_path],
            }


def task_mallet_train():
    for lang in LANGUAGES:
        corpus_paths = [
            DATA_ROOT / lang / filename
            for filename in DATA_SET_FILENAMES
        ]
        for corpus_path in corpus_paths:
            for trial in range(NUM_TRIALS):
                input_path = corpus_path.with_suffix('.mallet.dat')
                topic_model_name = f'topic-model-{NUM_TOPICS}-{trial}'
                name = f'{lang}.{corpus_path.stem}.{topic_model_name}'
                output_state_path = input_path.with_suffix(f'.{topic_model_name}.state.txt.gz')
                output_topic_keys_path = input_path.with_suffix(f'.{topic_model_name}.keys.txt')
                yield {
                    'name': name,
                    'file_dep': [input_path],
                    'actions': [[
                        f'{MALLET_PROGRAM}',
                        'train-topics',
                        '--num-topics', f'{NUM_TOPICS}',
                        '--num-iterations', f'{NUM_ITERATIONS}',
                        '--optimize-interval', f'{OPTIMIZE_INTERVAL}',
                        '--num-top-words', f'{NUM_STOP_WORDS + 100}',
                        '--input', f'{input_path}',
                        '--output-state', f'{output_state_path}',
                        '--output-topic-keys', f'{output_topic_keys_path}',
                    ]],
                    'targets': [output_state_path, output_topic_keys_path],
                }


def task_check_token_assignment_alignment():
    for lang in LANGUAGES:
        corpus_paths = [
            DATA_ROOT / lang / filename
            for filename in DATA_SET_FILENAMES
        ]
        for corpus_path in corpus_paths:
            for trial in range(NUM_TRIALS):
                topic_model_name = f'topic-model-{NUM_TOPICS}-{trial}'
                name = f'{lang}.{corpus_path.stem}.{topic_model_name}'
                state_path = corpus_path.with_suffix(f'.mallet.{topic_model_name}.state.txt.gz')
                yield {
                    'name': name,
                    'file_dep': [corpus_path, state_path],
                    'actions': [(check_token_assignment_alignment, (), dict(
                        corpus_path=corpus_path,
                        topic_state_path=state_path,
                    ))],
                    'uptodate': [True],  # up-to-date iff action has succeeded
                }


def task_compute_coherence():
    for lang in LANGUAGES:
        corpus_paths = [
            DATA_ROOT / lang / filename
            for filename in DATA_SET_FILENAMES
        ]
        # First entry in DATA_SET_FILENAMES is unlemmatized corpus
        untreated_state_path: Optional[PathLike] = None
        untreated_corpus_summary_path: Optional[PathLike] = None
        untreated_stop_list_path: Optional[PathLike] = None
        for trial in range(NUM_TRIALS):
            for corpus_path in corpus_paths:
                topic_model_name = f'topic-model-{NUM_TOPICS}-{trial}'
                dep_name = f'{lang}.{corpus_path.stem}.{topic_model_name}'
                name = f'{dep_name}.stop-top-200'
                state_path = corpus_path.with_suffix(f'.mallet.{topic_model_name}.state.txt.gz')
                if untreated_state_path is None:
                    untreated_state_path = state_path
                if untreated_corpus_summary_path is None:
                    untreated_corpus_summary_path = corpus_path.with_suffix('.summary.npz')
                if untreated_stop_list_path is None:
                    untreated_stop_list_path = corpus_path.with_suffix('.common-words.txt')
                yield {
                    'name': name,
                    'file_dep': [
                        untreated_corpus_summary_path,
                        untreated_state_path,
                        untreated_stop_list_path,
                        state_path,
                    ],
                    'task_dep': [f'check_token_assignment_alignment:{dep_name}'],
                    'actions': [(
                        compute_coherence_treated, (), dict(
                            untreated_corpus_summary_path=untreated_corpus_summary_path,
                            untreated_topic_state_path=untreated_state_path,
                            topic_state_path=state_path,
                            untreated_stop_list_path=untreated_stop_list_path,
                        ),
                    )],
                }


def task_compute_topic_assignments():
    for lang in LANGUAGES:
        corpus_paths = [
            DATA_ROOT / lang / filename
            for filename in DATA_SET_FILENAMES
        ]
        for corpus_path in corpus_paths:
            for trial in range(NUM_TRIALS):
                tm_name = f'topic-model-{NUM_TOPICS}-{trial}'
                name = f'{lang}.{corpus_path.stem}.{tm_name}'
                state_path = corpus_path.with_suffix(f'.mallet.{tm_name}.state.txt.gz')
                assignments_path = corpus_path.with_suffix(f'.mallet.{tm_name}.assignments.npy')
                yield {
                    'name': name,
                    'file_dep': [state_path],
                    'task_dep': [f'check_token_assignment_alignment:{name}'],
                    'actions': [(
                        compute_topic_assignments, (), dict(
                            topic_state_path=state_path,
                            topic_assignments_path=assignments_path,
                        ),
                    )],
                    'targets': [assignments_path],
                }


def task_compute_voi():
    for lang in LANGUAGES:
        corpus_paths = [
            DATA_ROOT / lang / filename
            for filename in DATA_SET_FILENAMES
        ]
        for (corpus_1_path, corpus_2_path) in product(corpus_paths, repeat=2):
            for (trial1, trial2) in product(range(NUM_TRIALS), repeat=2):
                tm_1_name = f'topic-model-{NUM_TOPICS}-{trial1}'
                tm_2_name = f'topic-model-{NUM_TOPICS}-{trial2}'
                name = f'{lang}.{corpus_1_path.stem}.{tm_1_name}.{corpus_2_path.stem}.{tm_2_name}'
                ta_1_path = corpus_1_path.with_suffix(f'.mallet.{tm_1_name}.assignments.npy')
                ta_2_path = corpus_2_path.with_suffix(f'.mallet.{tm_2_name}.assignments.npy')
                yield {
                    'name': name,
                    'file_dep': [ta_1_path, ta_2_path],
                    'actions': [(
                        compute_topic_assignment_voi, (), dict(
                            topic_assignments_1_path=ta_1_path,
                            topic_assignments_2_path=ta_2_path,
                        ),
                    )],
                }


def task_collect_coherence():
    output_path = DATA_ROOT / 'coherence.tsv'
    return {
        'getargs': {'scores': ('compute_coherence', 'coherence')},
        'actions': [(collect_subtask_scores, (), dict(output_path=output_path))],
        'targets': [output_path],
    }


def task_collect_voi():
    output_path = DATA_ROOT / 'voi.tsv'
    return {
        'getargs': {'scores': ('compute_voi', 'voi')},
        'actions': [(collect_subtask_scores, (), dict(output_path=output_path))],
        'targets': [output_path],
    }


def task_compute_coherence_sanity():
    for lang in LANGUAGES:
        corpus_paths = [
            DATA_ROOT / lang / filename
            for filename in DATA_SET_FILENAMES
        ]
        for trial in range(NUM_TRIALS):
            for corpus_path in corpus_paths:
                topic_model_name = f'topic-model-{NUM_TOPICS}-{trial}'
                dep_name = f'{lang}.{corpus_path.stem}.{topic_model_name}'
                name = f'{dep_name}.stop-top-200'
                topic_keys_path = corpus_path.with_suffix(f'.mallet.{topic_model_name}.keys.txt')
                state_path = corpus_path.with_suffix(f'.mallet.{topic_model_name}.state.txt.gz')
                corpus_summary_path = corpus_path.with_suffix('.summary.npz')
                stop_list_path = corpus_path.with_suffix('.common-words.txt')
                yield {
                    'name': name,
                    'file_dep': [
                        corpus_summary_path,
                        topic_keys_path,
                        state_path,
                        stop_list_path,
                    ],
                    'task_dep': [f'check_token_assignment_alignment:{dep_name}'],
                    'actions': [(
                        compute_coherence, (), dict(
                            corpus_summary_path=corpus_summary_path,
                            topic_keys_path=topic_keys_path,
                            topic_state_path=state_path,
                            stop_list_path=stop_list_path,
                        ),
                    )],
                }


def task_collect_coherence_sanity():
    output_path = DATA_ROOT / 'coherence-sanity.tsv'
    return {
        'getargs': {'scores': ('compute_coherence_sanity', 'coherence')},
        'actions': [(collect_subtask_scores, (), dict(output_path=output_path))],
        'targets': [output_path],
    }


def task_collect_keys():
    for lang in LANGUAGES:
        output_path = DATA_ROOT / lang / 'keys.txt'
        input_paths = [
            (DATA_ROOT / lang / filename).with_suffix(
                f'.mallet.topic-model-{NUM_TOPICS}-{trial}.keys.txt'
            )
            for filename in DATA_SET_FILENAMES
            for trial in range(NUM_TRIALS)
        ]
        yield {
            'name': lang,
            'file_dep': input_paths,
            'actions': [(
                collect_keys, (), dict(
                    input_paths=input_paths,
                    output_path=output_path,
                ),
            )],
            'targets': [output_path],
        }


def task_translate_collected_keys():
    for lang in LANGUAGES:
        if lang != 'en':
            input_path = DATA_ROOT / lang / 'keys.txt'
            output_path = input_path.with_suffix('.translated.jsonl')
            yield {
                'name': lang,
                'file_dep': [input_path],
                'actions': [(
                    translate_words, (), dict(
                        input_path=input_path,
                        output_path=output_path,
                        from_lang=lang,
                        to_lang='en',
                    ),
                )],
                'targets': [output_path],
            }


def task_translate_keys():
    for lang in LANGUAGES:
        if lang != 'en':
            corpus_paths = [
                DATA_ROOT / lang / filename
                for filename in DATA_SET_FILENAMES
            ]
            translations_source_path = DATA_ROOT / lang / 'keys.txt'
            translations_target_path = translations_source_path.with_suffix('.translated.jsonl')
            for trial in range(NUM_TRIALS):
                for corpus_path in corpus_paths:
                    topic_model_name = f'topic-model-{NUM_TOPICS}-{trial}'
                    name = f'{lang}.{corpus_path.stem}.{topic_model_name}'
                    keys_path = corpus_path.with_suffix(f'.mallet.{topic_model_name}.keys.txt')
                    translated_keys_path = keys_path.with_suffix('.translated.txt')
                    yield {
                        'name': name,
                        'file_dep': [
                            keys_path,
                            translations_source_path,
                            translations_target_path,
                        ],
                        'actions': [(
                            translate_keys, (), dict(
                                keys_path=keys_path,
                                translated_keys_path=translated_keys_path,
                                translations_source_path=translations_source_path,
                                translations_target_path=translations_target_path,
                            ),
                        )],
                        'targets': [translated_keys_path],
                    }


def task_filter_translated_keys():
    en_stop_list_paths = [
        (DATA_ROOT / 'en' / filename).with_suffix('.common-words.txt')
        for filename in DATA_SET_FILENAMES
    ]
    for lang in LANGUAGES:
        if lang != 'en':
            corpus_paths = [
                DATA_ROOT / lang / filename
                for filename in DATA_SET_FILENAMES
            ]
            for trial in range(NUM_TRIALS):
                for corpus_path in corpus_paths:
                    topic_model_name = f'topic-model-{NUM_TOPICS}-{trial}'
                    dep_name = f'{lang}.{corpus_path.stem}.{topic_model_name}'
                    name = f'{dep_name}.stop-top-200'
                    input_path = corpus_path.with_suffix(
                        f'.mallet.{topic_model_name}.keys.translated.txt')
                    output_path = input_path.with_suffix('.filtered.txt')
                    yield {
                        'name': name,
                        'file_dep': [input_path] + en_stop_list_paths,
                        'actions': [(
                            filter_keys, (), dict(
                                input_path=input_path,
                                output_path=output_path,
                                stop_list_paths=en_stop_list_paths,
                                min_word_length=MIN_WORD_LENGTH,
                                filter_non_alpha=FILTER_NON_ALPHA,
                            ),
                        )],
                        'targets': [output_path],
                    }


def task_filter_keys():
    for lang in LANGUAGES:
        corpus_paths = [
            DATA_ROOT / lang / filename
            for filename in DATA_SET_FILENAMES
        ]
        stop_list_paths = [
            corpus_path.with_suffix('.common-words.txt')
            for corpus_path in corpus_paths
        ]
        for trial in range(NUM_TRIALS):
            for corpus_path in corpus_paths:
                topic_model_name = f'topic-model-{NUM_TOPICS}-{trial}'
                dep_name = f'{lang}.{corpus_path.stem}.{topic_model_name}'
                name = f'{dep_name}.stop-top-200'
                input_path = corpus_path.with_suffix(f'.mallet.{topic_model_name}.keys.txt')
                output_path = input_path.with_suffix('.filtered.txt')
                yield {
                    'name': name,
                    'file_dep': [input_path] + stop_list_paths,
                    'actions': [(
                        filter_keys, (), dict(
                            input_path=input_path,
                            output_path=output_path,
                            stop_list_paths=stop_list_paths,
                            min_word_length=MIN_WORD_LENGTH,
                            filter_non_alpha=FILTER_NON_ALPHA,
                        ),
                    )],
                    'targets': [output_path],
                }


def task_extract_corpus_stats():
    for lang in LANGUAGES:
        corpus_paths = [
            DATA_ROOT / lang / filename
            for filename in DATA_SET_FILENAMES
        ]
        for corpus_path in corpus_paths:
            input_path = corpus_path.with_suffix('.summary.npz')
            name = f'{lang}.{corpus_path.stem}'
            yield {
                'name': name,
                'file_dep': [input_path],
                'actions': [(extract_corpus_stats, (), dict(corpus_summary_path=input_path))],
            }


def task_collect_corpus_stats():
    output_path = DATA_ROOT / 'corpus-stats.tsv'
    return {
        'getargs': {'stat_dicts': ('extract_corpus_stats', None)},
        'actions': [(collect_corpus_stats, (), dict(output_path=output_path))],
        'targets': [output_path],
    }
