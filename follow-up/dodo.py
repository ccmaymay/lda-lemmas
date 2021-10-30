from pathlib import Path

import pycountry  # type: ignore

from follow_up.util import subsample
from follow_up.conversion import convert_polyglot_to_mallet
from follow_up.lemmatization import parse_treetagger, lemmatize_polyglot

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
            # consider up-to-date as long as target files exist
            'uptodate': [True],
            'actions': [f'tar -C {DATA_ROOT} -xvJf {input_path}'],
            'targets': [output_path],
        }


def task_to_mallet():
    for lang in LANGUAGES:
        input_paths = [
            DATA_ROOT / lang / 'sub.txt',
            DATA_ROOT / lang / 'sub.lem-polyglot.txt',
            DATA_ROOT / lang / 'sub.lem-treetagger.parsed.txt',
        ]
        prev_tasks = [
            f'subsample:{lang}',
            f'lemmatize_polyglot:{lang}',
            f'parse_treetagger:{lang}',
        ]
        for (input_path, prev_task) in zip(input_paths, prev_tasks):
            output_path = input_path.with_suffix('.mallet.txt')
            yield {
                'name': f'{lang}-{input_path.stem}',
                # consider up-to-date as long as target files exist
                'uptodate': [True],
                # ensure other task happens first without affecting uptodateness
                'task_dep': [prev_task],
                'actions': [(convert_polyglot_to_mallet, (), dict(
                    lang=lang,
                    input_path=input_path,
                    output_path=output_path
                ))],
                'targets': [output_path],
            }


def task_subsample():
    for lang in LANGUAGES:
        input_path = DATA_ROOT / lang / 'full.txt'
        output_path = DATA_ROOT / lang / 'sub.txt'
        yield {
            'name': lang,
            # consider up-to-date as long as target files exist
            'uptodate': [True],
            # ensure untar happens first without affecting uptodateness
            'task_dep': [f'untar:{lang}'],
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
            # consider up-to-date as long as target files exist
            'uptodate': [True],
            # ensure subsample happens first without affecting uptodateness
            'task_dep': [f'subsample:{lang}'],
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
            # consider up-to-date as long as target files exist
            'uptodate': [True],
            # ensure lemmatize happens first without affecting uptodateness
            'task_dep': [f'lemmatize_treetagger:{lang}'],
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
            # consider up-to-date as long as target files exist
            'uptodate': [True],
            # ensure subsample happens first without affecting uptodateness
            'task_dep': [f'subsample:{lang}'],
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
        program_path = UDPIPE_BIN / f'udpipe'
        model_path = UDPIPE_MODELS[lang]
        yield {
            'name': lang,
            # consider up-to-date as long as target files exist
            'uptodate': [True],
            # ensure subsample happens first without affecting uptodateness
            'task_dep': [f'subsample:{lang}'],
            'actions': [
                f'{program_path} '
                f'--tag --immediate --input=horizontal --outfile={output_path} '
                f'{model_path} '
                f'{input_path}'
            ],
            'targets': [output_path],
        }
