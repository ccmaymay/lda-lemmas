from pathlib import Path

import pycountry  # type: ignore

from follow_up.util import subsample
from follow_up.conversion import convert_polyglot_to_mallet
from follow_up.lemmatization import parse_treetagger, lemmatize_polyglot, parse_udpipe

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
            'uptodate': [True],  # up-to-date as long as targets exist
            'actions': [f'tar -C {DATA_ROOT} -xvJf {input_path}'],
            'targets': [output_path],
        }


def task_subsample():
    for lang in LANGUAGES:
        input_path = DATA_ROOT / lang / 'full.txt'
        output_path = DATA_ROOT / lang / 'sub.txt'
        yield {
            'name': lang,
            'uptodate': [True],  # up-to-date as long as targets exist
            'task_dep': [f'untar:{lang}'],  # ensure untar has been run at least once
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
            'uptodate': [True],  # up-to-date as long as targets exist
            'task_dep': [f'subsample:{lang}'],  # ensure subsample has been run at least once
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
            'uptodate': [True],  # up-to-date as long as targets exist
            'task_dep': [f'lemmatize_treetagger:{lang}'],  # ensure has been run at least once
            'actions': [(parse_treetagger, (), dict(
                lang=lang,
                input_path=input_path,
                output_path=output_path
            ))],
            'targets': [output_path],
        }


def task_lemmatize_polyglot():
    for lang in LANGUAGES:
        input_path = DATA_ROOT / lang / 'sub.txt'
        output_path = input_path.with_suffix('.lem-polyglot.txt')
        yield {
            'name': lang,
            'uptodate': [True],  # up-to-date as long as targets exist
            'task_dep': [f'subsample:{lang}'],  # ensure subsample has been run at least once
            'actions': [(lemmatize_polyglot, (), dict(
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
            'uptodate': [True],  # up-to-date as long as targets exist
            'task_dep': [f'subsample:{lang}'],  # ensure subsample has been run at least once
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
            'uptodate': [True],  # up-to-date as long as targets exist
            'task_dep': [f'lemmatize_udpipe:{lang}'],  # ensure has been run at least once
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
            DATA_ROOT / lang / 'sub.txt',
            DATA_ROOT / lang / 'sub.lem-polyglot.txt',
            DATA_ROOT / lang / 'sub.lem-treetagger.parsed.txt',
            DATA_ROOT / lang / 'sub.lem-udpipe.parsed.txt',
        ]
        prev_tasks = [
            f'subsample:{lang}',
            f'lemmatize_polyglot:{lang}',
            f'parse_treetagger:{lang}',
            f'parse_udpipe:{lang}',
        ]
        for (input_path, prev_task) in zip(input_paths, prev_tasks):
            output_path = input_path.with_suffix('.mallet.txt')
            yield {
                'name': f'{lang}-{input_path.stem}',
                'uptodate': [True],  # up-to-date as long as targets exist
                'task_dep': [prev_task],  # ensure prev task has been run at least once
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
            DATA_ROOT / lang / 'sub.mallet.txt',
            DATA_ROOT / lang / 'sub.lem-polyglot.mallet.txt',
            DATA_ROOT / lang / 'sub.lem-treetagger.parsed.mallet.txt',
            DATA_ROOT / lang / 'sub.lem-udpipe.parsed.mallet.txt',
        ]
        for input_path in input_paths:
            name = f'{lang}-{input_path.stem}'
            prev_task = f'to_mallet:{name}'
            output_path = input_path.with_suffix('.dat')
            yield {
                'name': name,
                'uptodate': [True],  # up-to-date as long as targets exist
                'task_dep': [prev_task],  # ensure prev task has been run at least once
                'actions': [
                    f'{MALLET_PROGRAM} import-file --input {input_path} --output {output_path}'
                ],
                'targets': [output_path],
            }
