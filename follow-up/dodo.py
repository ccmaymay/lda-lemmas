from pathlib import Path
from typing import Iterable

import pycountry  # type: ignore

from follow_up.conversion import convert_polyglot_to_mallet
from follow_up.lemmatization import parse_treetagger, lemmatize_polyglot

DATA_ROOT = 'polyglot'
TREETAGGER_ROOT = 'treetagger'
MAX_NUM_DOCS = 200000

LANGUAGE_NAMES = dict(
    (lang.alpha_2, lang.name.lower())
    for lang in pycountry.languages
    if hasattr(lang, 'alpha_2')
)


def get_languages() -> Iterable[str]:
    data_dir_path = Path(DATA_ROOT)
    for input_tar_path in data_dir_path.glob('??_wiki_text.tar.lzma'):
        lang = input_tar_path.name[:2]
        yield lang


def task_untar():
    data_dir_path = Path(DATA_ROOT)
    for lang in get_languages():
        input_tar_path = data_dir_path / f'{lang}_wiki_text.tar.lzma'
        output_text_path = data_dir_path / lang / 'full.txt'
        yield {
            'name': lang,
            'file_dep': [input_tar_path],
            'actions': [f'tar -C {DATA_ROOT} -xvJf %(dependencies)s'],
            'targets': [output_text_path],
        }


def task_convert_polyglot_to_mallet():
    data_dir_path = Path(DATA_ROOT)
    for lang in get_languages():
        input_path = data_dir_path / lang / 'full.txt'
        output_path = data_dir_path / lang / 'mallet.txt'
        yield {
            'name': lang,
            'file_dep': [input_path],
            'actions': [(convert_polyglot_to_mallet, (), dict(
                lang=lang,
                input_path=input_path,
                output_path=output_path
            ))],
            'targets': [output_path],
        }


def task_subsample():
    data_dir_path = Path(DATA_ROOT)
    for lang in get_languages():
        input_path = data_dir_path / lang / 'mallet.txt'
        output_path = data_dir_path / lang / 'mallet-sub.txt'
        yield {
            'name': lang,
            'file_dep': [input_path],
            'actions': [f'shuf -n {MAX_NUM_DOCS} %(dependencies)s > %(targets)s'],
            'targets': [output_path],
        }


def task_lemmatize_treetagger():
    data_dir_path = Path(DATA_ROOT)
    for lang in get_languages():
        lang_name = LANGUAGE_NAMES[lang]
        input_path = data_dir_path / lang / 'full.txt'
        output_path = data_dir_path / lang / 'lem-treetagger.txt'
        yield {
            'name': lang,
            'file_dep': [input_path],
            'actions': [
                f'treetagger/cmd/tree-tagger-{lang_name} < %(dependencies)s > %(targets)s'
            ],
            'targets': [output_path],
        }


def task_parse_treetagger():
    data_dir_path = Path(DATA_ROOT)
    for lang in get_languages():
        input_path = data_dir_path / lang / 'lem-treetagger.txt'
        output_path = data_dir_path / lang / 'lem-treetagger-parsed.txt'
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
    data_dir_path = Path(DATA_ROOT)
    for lang in get_languages():
        input_path = data_dir_path / lang / 'full.txt'
        output_path = data_dir_path / lang / 'lem-polyglot.txt'
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
