from functools import partial
from pathlib import Path

import pycountry  # type: ignore

from follow_up.util import subsample_parallel
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
        input_tar_path = data_root_path / f'{lang}_wiki_text.tar.lzma'
        output_text_path = data_root_path / lang / 'full.txt'
        yield {
            'name': lang,
            'file_dep': [input_tar_path],
            'actions': [f'tar -C {DATA_ROOT} -xvJf %(dependencies)s'],
            'targets': [output_text_path],
        }


def task_to_mallet():
    data_root_path = Path(DATA_ROOT)
    for lang in LANGUAGES:
        input_paths = [
            data_root_path / lang / 'full.txt',
            data_root_path / lang / 'lem-polyglot.txt',
            data_root_path / lang / 'lem-treetagger.txt',
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


def task_subsample_mallet():
    data_root_path = Path(DATA_ROOT)
    for lang in LANGUAGES:
        input_paths = [
            data_root_path / lang / 'full.mallet.txt',
            data_root_path / lang / 'lem-polyglot.mallet.txt',
            data_root_path / lang / 'lem-treetagger.mallet.txt',
        ]
        output_paths = [input_path.with_suffix('.sub.txt') for input_path in input_paths]
        yield {
            'name': lang,
            'file_dep': input_paths,
            'actions': partial(subsample_parallel, max_num_lines=MAX_NUM_DOCS),
            'targets': output_paths,
        }


def task_lemmatize_treetagger():
    data_root_path = Path(DATA_ROOT)
    for lang in LANGUAGES:
        lang_name = LANGUAGE_NAMES[lang]
        input_path = data_root_path / lang / 'full.txt'
        output_path = data_root_path / lang / 'lem-treetagger-unparsed.txt'
        yield {
            'name': lang,
            'file_dep': [input_path],
            'actions': [
                f'treetagger/cmd/tree-tagger-{lang_name} < %(dependencies)s > %(targets)s'
            ],
            'targets': [output_path],
        }


def task_parse_treetagger():
    data_root_path = Path(DATA_ROOT)
    for lang in LANGUAGES:
        input_path = data_root_path / lang / 'lem-treetagger-unparsed.txt'
        output_path = data_root_path / lang / 'lem-treetagger.txt'
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


def task_lemmatize_polyglot():
    data_root_path = Path(DATA_ROOT)
    for lang in LANGUAGES:
        input_path = data_root_path / lang / 'full.txt'
        output_path = data_root_path / lang / 'lem-polyglot.txt'
        yield {
            'name': lang,
            # consider up-to-date as long as target files exist
            'uptodate': [True],
            # ensure untar happens first without affecting uptodateness
            'task_dep': [f'untar:{lang}'],
            'actions': [(lemmatize_polyglot, (), dict(
                lang=lang,
                input_path=input_path,
                output_path=output_path
            ))],
            'targets': [output_path],
        }
