from .util import load_polyglot


def convert_polyglot_to_mallet(lang, input_path, output_path):
    with open(output_path, encoding='utf-8', mode='w') as f:
        for doc in load_polyglot(input_path):
            f.write(doc.to_mallet(lang) + '\n')
