import platform
from pathlib import Path

import pycountry  # type: ignore

from follow_up.util import subsample
from follow_up.conversion import convert_polyglot_to_mallet
from follow_up.evaluation import (
    check_corpus_alignment, check_token_assignment_alignment,
    print_coherence, print_coherence_lemmatized,
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

DATA_SET_FILENAMES = (
    'sub.txt',
    'sub.lem-treetagger.parsed.txt',
    'sub.lem-udpipe.parsed.txt',
)

NUM_TOPICS = 100
NUM_ITERATIONS = 1000
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
            'actions': [f'tar -C {DATA_ROOT} -xvJf {input_path}'],
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
            'actions': [
                ' '.join((
                    f'{program_path}',
                    '--tag',
                    '--immediate',
                    '--input=horizontal',
                    f'--outfile={output_path}',
                    f'{model_path}',
                    f'{input_path}',
                ))
            ],
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
                'name': f'{lang}-{input_path.stem}',
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
            name = f'{lang}-{input_path.stem}'
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
            name = f'{lang}-{input_path.stem}'
            output_path = input_path.with_suffix('.dat')
            yield {
                'name': name,
                'file_dep': [input_path],
                'actions': [
                    ' '.join((
                        f'{MALLET_PROGRAM}',
                        'import-file',
                        '--input', f'{input_path}',
                        '--output', f'{output_path}',
                        '--keep-sequence',
                        '--preserve-case',
                        '--token-regex', '[^ ]+',
                    ))
                ],
                'targets': [output_path],
            }


def task_mallet_train():
    for lang in LANGUAGES:
        input_paths = [
            (DATA_ROOT / lang / filename).with_suffix('.mallet.dat')
            for filename in DATA_SET_FILENAMES
        ]
        for input_path in input_paths:
            name = f'{lang}-{input_path.stem}'
            output_model_path = input_path.with_suffix('.topic-model.dat')
            output_state_path = input_path.with_suffix('.topic-model.state.txt.gz')
            output_topic_keys_path = input_path.with_suffix('.topic-model.keys.txt')
            yield {
                'name': name,
                'file_dep': [input_path],
                'actions': [
                    ' '.join((
                        f'{MALLET_PROGRAM}',
                        'train-topics',
                        '--num-topics', f'{NUM_TOPICS}',
                        '--num-iterations', f'{NUM_ITERATIONS}',
                        '--optimize-interval', f'{OPTIMIZE_INTERVAL}',
                        '--input', f'{input_path}',
                        '--output-model', f'{output_model_path}',
                        '--output-state', f'{output_state_path}',
                        '--output-topic-keys', f'{output_topic_keys_path}',
                    ))
                ],
                'targets': [output_model_path, output_state_path, output_topic_keys_path],
            }


def task_check_token_assignment_alignment():
    for lang in LANGUAGES:
        corpus_paths = [
            DATA_ROOT / lang / filename
            for filename in DATA_SET_FILENAMES
        ]
        for corpus_path in corpus_paths:
            state_path = corpus_path.with_suffix('.mallet.topic-model.state.txt.gz')
            yield {
                'name': f'{lang}-{corpus_path.stem}',
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
            topic_keys_path = corpus_path.with_suffix('.mallet.topic-model.keys.txt')
            state_path = corpus_path.with_suffix('.mallet.topic-model.state.txt.gz')
            output_path = corpus_path.with_suffix('.mallet.topic-model.coherence.txt')
            name = f'{lang}-{corpus_path.stem}'
            yield {
                'name': name,
                'file_dep': [corpus_path, state_path, topic_keys_path],
                'task_dep': [f'check_token_assignment_alignment:{name}'],
                'actions': [(
                    print_coherence_lemmatized if is_lemmatized else print_coherence,
                    (),
                    dict(
                        corpus_path=corpus_path,
                        topic_keys_path=topic_keys_path,
                        topic_state_path=state_path,
                        output_path=output_path,
                    ),
                )],
                'targets': [output_path],
            }
            is_lemmatized = True
