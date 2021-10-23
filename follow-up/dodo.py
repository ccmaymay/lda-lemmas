from pathlib import Path

DATA_DIR = '/export/b01/cmay14/polyglot'


def task_untar():
    data_dir_path = Path(DATA_DIR)
    for tar_path in data_dir_path.glob('*.tar.lzma'):
        lang_id = tar_path.name[:2]
        output_text_path = data_dir_path / lang_id / 'full.txt'
        yield {
            'name': lang_id,
            'file_dep': [tar_path],
            'actions': [f'tar -C {DATA_DIR} -xvJf %(dependencies)s'],
            'targets': [output_text_path],
        }
