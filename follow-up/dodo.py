from pathlib import Path

import pycountry  # type: ignore

from follow_up.util import subsample
from follow_up.conversion import convert_polyglot_to_mallet
from follow_up.lemmatization import parse_treetagger, lemmatize_polyglot

DATA_ROOT = 'polyglot'
TREETAGGER_ROOT = 'treetagger'
MAX_NUM_DOCS = 200000

LANGUAGES = ('en', 'fa', 'ko', 'ru')
LANGUAGE_NAMES = dict(
    (lang.alpha_2, lang.name.lower())
    for lang in pycountry.languages
    if hasattr(lang, 'alpha_2')
)


def task_untar():
    data_root_path = Path(DATA_ROOT)
    for lang in LANGUAGES:
        input_path = data_root_path / f'{lang}_wiki_text.tar.lzma'
        output_path = data_root_path / lang / 'full.txt'
        yield {
            'name': lang,
            # consider up-to-date as long as target files exist
            'uptodate': [True],
            'actions': [f'tar -C {DATA_ROOT} -xvJf {input_path}'],
            'targets': [output_path],
        }


def task_to_mallet():
    data_root_path = Path(DATA_ROOT)
    for lang in LANGUAGES:
        input_paths = [
            data_root_path / lang / 'sub.txt',
            data_root_path / lang / 'sub.lem-polyglot.txt',
            data_root_path / lang / 'sub.lem-treetagger.parsed.txt',
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
    data_root_path = Path(DATA_ROOT)
    for lang in LANGUAGES:
        input_path = data_root_path / lang / 'full.txt'
        output_path = data_root_path / lang / 'sub.txt'
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
    data_root_path = Path(DATA_ROOT)
    for lang in LANGUAGES:
        lang_name = LANGUAGE_NAMES[lang]
        input_path = data_root_path / lang / 'sub.txt'
        output_path = input_path.with_suffix('.lem-treetagger.txt')
        yield {
            'name': lang,
            # consider up-to-date as long as target files exist
            'uptodate': [True],
            # ensure subsample happens first without affecting uptodateness
            'task_dep': [f'subsample:{lang}'],
            'actions': [
                f'treetagger/cmd/tree-tagger-{lang_name} < {input_path} > {output_path}'
            ],
            'targets': [output_path],
        }


def task_parse_treetagger():
    data_root_path = Path(DATA_ROOT)
    for lang in LANGUAGES:
        input_path = data_root_path / lang / 'sub.lem-treetagger.txt'
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
    data_root_path = Path(DATA_ROOT)
    for lang in LANGUAGES:
        input_path = data_root_path / lang / 'sub.txt'
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
