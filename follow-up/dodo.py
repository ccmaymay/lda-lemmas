from pathlib import Path

import pycountry  # type: ignore

from follow_up.util import subsample
from follow_up.conversion import convert_polyglot_to_mallet
from follow_up.lemmatization import parse_treetagger, parse_udpipe

DATA_ROOT = Path('polyglot')
TREETAGGER_ROOT = Path('treetagger')
UDPIPE_ROOT = Path('udpipe')
UDPIPE_BIN = UDPIPE_ROOT / 'bin-linux64'
UDPIPE_MODELS = {
    'en': UDPIPE_ROOT / 'english-ewt-ud-2.5-191206.udpipe',
    'fa': UDPIPE_ROOT / 'persian-seraji-ud-2.5-191206.udpipe',
    'ko': UDPIPE_ROOT / 'korean-kaist-ud-2.5-191206.udpipe',
    'ru': UDPIPE_ROOT / 'russian-syntagrus-ud-2.5-191206.udpipe',
}
MALLET_ROOT = Path('mallet')
MALLET_PROGRAM = MALLET_ROOT / 'bin' / 'mallet'

MAX_NUM_DOCS = 200000

DATA_SET_FILENAMES = (
    'sub.txt',
    'sub.lem-treetagger.parsed.txt',
    'sub.lem-udpipe.parsed.txt',
)

NUM_TOPICS = 100
NUM_ITERATIONS = 100
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
        program_path = TREETAGGER_ROOT / f'cmd/tree-tagger-{lang_name}'
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


def task_to_mallet():
    for lang in LANGUAGES:
        input_paths = [
            DATA_ROOT / lang / filename
            for filename in DATA_SET_FILENAMES
        ]
        for input_path in input_paths:
            output_path = input_path.with_suffix('.mallet.txt')
            yield {
                'name': f'{lang}-{input_path.stem}',
                'file_dep': [input_path],
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
            output_state_path = input_path.with_suffix('.topic-state.txt.gz')
            output_keys_path = input_path.with_suffix('.topic-keys.txt.gz')
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
                        '--output-state', f'{output_state_path}',
                        '--output-topic-keys', f'{output_keys_path}',
                    ))
                ],
                'targets': [output_state_path, output_keys_path],
            }
