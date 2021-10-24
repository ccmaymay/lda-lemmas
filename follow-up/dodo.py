from pathlib import Path

import pycountry  # type: ignore

from follow_up.conversion import convert_polyglot_to_mallet

DATA_ROOT = 'polyglot'
TREETAGGER_ROOT = 'treetagger'
MAX_NUM_DOCS = 200000

LANGUAGE_NAMES = dict(
    (lang.alpha_2, lang.name.lower())
    for lang in pycountry.languages
    if hasattr(lang, 'alpha_2')
)


def get_languages():
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
            'actions': [f'treetagger/cmd/tree-tagger-{lang_name} < %(dependencies)s > %(targets)s'],
            'targets': [output_path],
        }
