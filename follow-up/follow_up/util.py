import re
from dataclasses import dataclass
from os import PathLike
from typing import Generator, List

DOC_ID_RE = re.compile(r'^\[\[(\d+)\]\]$')


@dataclass
class Doc(object):
    name: str
    sections: List[List[str]]

    @property
    def tokens(self) -> List[str]:
        return [
            token
            for section in self.sections
            for token in section
        ]

    @property
    def text(self) -> str:
        return ''.join(
            ' '.join(section) + '\n'
            for section in self.sections
        )

    @property
    def flat_text(self) -> str:
        return ' '.join(self.tokens)

    def to_mallet(self, cls: str) -> str:
        return f'{self.name} {cls} {self.flat_text}'

    def to_polyglot(self) -> str:
        return f'[[{self.name}]]\n{self.text}'


def load_polyglot(input_path: PathLike) -> Generator[Doc, None, None]:
    with open(input_path, encoding='utf-8') as f:
        prev_line = None
        doc = None
        for line in f:
            line = line.strip()
            doc_id_match = DOC_ID_RE.match(line)
            if not prev_line and doc_id_match is not None:
                if doc is not None and doc.tokens:
                    yield doc
                doc = Doc(doc_id_match.group(1), [])
            elif doc is not None and line:
                doc.sections.append(line.split())

            prev_line = line

        if doc is not None and doc.tokens:
            yield doc
