import re

DOC_ID_RE = re.compile(r'^\[\[(\d+)\]\]$')


def write_doc(f, lang, doc_id, tokens):
    joined_tokens = ' '.join(tokens)
    f.write(f'{doc_id} {lang} {joined_tokens}\n')


def convert_polyglot_to_mallet(lang, input_path, output_path):
    with open(input_path, encoding='utf-8') as in_f, \
            open(output_path, encoding='utf-8', mode='w') as out_f:
        prev_line = None
        doc_id = None
        doc_tokens = []
        for line in in_f:
            line = line.strip()
            m = DOC_ID_RE.match(line)
            if not prev_line and m is not None:
                if doc_id and doc_tokens:
                    write_doc(out_f, lang, doc_id, doc_tokens)
                doc_id = m.group(1)
                doc_tokens = []
            else:
                for token in line.split():
                    doc_tokens.append(token)

            prev_line = line

        if doc_id and doc_tokens:
            write_doc(out_f, lang, doc_id, doc_tokens)
