import platform
from itertools import product
from pathlib import Path

import pycountry  # type: ignore

from follow_up.util import subsample, convert_polyglot_to_mallet, lowercase_polyglot
from follow_up.evaluation import (
    check_corpus_alignment, check_token_assignment_alignment,
    compute_coherence, compute_coherence_lemmatized, compute_topic_assignment_voi,
    collect_subtask_scores,
)
from follow_up.lemmatization import parse_treetagger, parse_udpipe

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
NUM_TRIALS = 1
OPTIMIZE_INTERVAL = 10

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
        input_paths = [
            (DATA_ROOT / lang / filename).with_suffix('.mallet.txt')
            for filename in DATA_SET_FILENAMES
        ]
        for input_path in input_paths:
            name = f'{lang}.{input_path.stem}'
            output_path = input_path.with_suffix('.dat')
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
                    '--line-regex', '^(\S+) (\S+) (.*)$',
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
                output_model_path = input_path.with_suffix(f'.{topic_model_name}.dat')
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
                        '--input', f'{input_path}',
                        '--output-model', f'{output_model_path}',
                        '--output-state', f'{output_state_path}',
                        '--output-topic-keys', f'{output_topic_keys_path}',
                    ]],
                    'targets': [output_model_path, output_state_path, output_topic_keys_path],
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
        is_lemmatized = False
        for corpus_path in corpus_paths:
            for trial in range(NUM_TRIALS):
                topic_model_name = f'topic-model-{NUM_TOPICS}-{trial}'
                name = f'{lang}.{corpus_path.stem}.{topic_model_name}'
                topic_keys_path = corpus_path.with_suffix(f'.mallet.{topic_model_name}.keys.txt')
                state_path = corpus_path.with_suffix(f'.mallet.{topic_model_name}.state.txt.gz')
                yield {
                    'name': name,
                    'file_dep': [corpus_path, state_path, topic_keys_path],
                    'task_dep': [f'check_token_assignment_alignment:{name}'],
                    'actions': [(
                        compute_coherence_lemmatized if is_lemmatized else compute_coherence,
                        (),
                        dict(
                            corpus_path=corpus_path,
                            topic_keys_path=topic_keys_path,
                            topic_state_path=state_path,
                        ),
                    )],
                }
                is_lemmatized = True


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
                name1 = f'{lang}.{corpus_1_path.stem}.{tm_1_name}'
                name2 = f'{lang}.{corpus_2_path.stem}.{tm_2_name}'
                name = f'{lang}.{corpus_1_path.stem}.{tm_1_name}.{corpus_2_path.stem}.{tm_2_name}'
                state_1_path = corpus_1_path.with_suffix(f'.mallet.{tm_1_name}.state.txt.gz')
                state_2_path = corpus_2_path.with_suffix(f'.mallet.{tm_2_name}.state.txt.gz')
                yield {
                    'name': name,
                    'file_dep': [state_1_path, state_2_path],
                    'task_dep': [
                        f'check_token_assignment_alignment:{name1}',
                        f'check_token_assignment_alignment:{name2}',
                    ],
                    'actions': [(
                        compute_topic_assignment_voi, (), dict(
                            topic_state_1_path=state_1_path,
                            topic_state_2_path=state_2_path,
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
