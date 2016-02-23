#!/usr/bin/env python

from redis import Redis
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)-15s %(levelname)s %(process)d %(funcName)s: %(message)s'
)

def process(d, x):
    (lemma, word) = x.split(u'::lemma::')
    if lemma in d:
        d[lemma].add(word)
    else:
        d[lemma] = set([word])

def main():
    m = 'wiki.ru:d/lemma-map/*::lemma::*'
    nk = 'wiki.ru:d/lm'
    bs = 1000

    s = Redis('r8n40', 61243)
    if s.ping():
        logging.info('PONG')
    else:
        raise Exception('no pong')

    d = dict()

    logging.info('reading...')
    (c, b) = s.scan(0, match=m, count=bs)
    while c != 0:
        logging.info('read %d' % len(d))
        for x in b:
            process(d, x.decode('utf-8'))
        (c, b) = s.scan(c, match=m, count=bs)

    logging.info('writing...')
    d_items = d.items()
    i = 0
    while i < len(d_items):
        logging.info('wrote %d' % i)
        s.hmset(
            nk,
            dict(
                (f.encode('utf-8'), (u'\n'.join(v)).encode('utf-8'))
                for (f, v) in d_items[i:i+bs]
            )
        )
        i += bs

if __name__ == '__main__':
    main()
