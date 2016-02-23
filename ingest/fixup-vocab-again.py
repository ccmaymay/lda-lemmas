#!/usr/bin/env python2.7

from redis import Redis
r = Redis('r7n19', 61244)
df_key = 'wiki.ru:dl/df'
vocab_key = 'wiki.ru:dl/vocab:10k-100:p'
for lemma in r.zrevrange(df_key, 0, 99):
    print lemma.decode('utf-8')
    r.lrem(vocab_key, lemma, num=1)
