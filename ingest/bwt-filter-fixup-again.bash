#!/bin/bash

# Part 2 of:
# Example preprocessing procedure for Wikipedia tokens with POS and
# lemma taggings in tab-delimited format.

set -e

input_host=${1:-`hostname`}
input_port=${2:-1118}
base_key=wiki.ru

input_addr=${input_host}:${input_port}
filter_leaf=:10k-100:p

python << EOF
from redis import Redis
r = Redis('$input_host', $input_port)
seen = set()
for w in r.zrevrange('${base_key}:dl/df', 0, 99):
    seen.add(w)
for w in r.zrevrange('${base_key}:dll/df', 0, 99):
    seen.add(w)
vocab_key = '${base_key}:dl/vocab:10k-100:p'
vocab = r.lrange(vocab_key, 0, -1)
new_vocab = []
for w in vocab:
    if w not in seen:
        new_vocab.append(w)
        seen.add(w)
r.rename(vocab_key, vocab_key + ':orig')
r.lpush(vocab_key, *new_vocab)
EOF

for int_key in ${base_key}:dl
do
    tube flow $input_addr ${int_key}:df-seen:21 set
    tube flow $input_addr ${int_key}:df-seen:22 set
    qsub -N clone -b y -cwd -j y -V -t 1-100 -tc 1 \
        -l h_rt=287:00:00,num_proc=1,mem_free=1G \
        tube clone \
            --block \
            $input_addr \
            ${int_key}:df-seen:2{0,1,2}

    tube flow $input_addr ${int_key}:df-seen:23 set
    qsub -N clone -b y -cwd -j y -V -t 1-100 -tc 1 \
        -l h_rt=287:00:00,num_proc=1,mem_free=1G \
        tube clone \
            --block \
            $input_addr \
            ${int_key}:df-seen:2{1,3,4}

    tube flow $input_addr ${int_key}:trunc50 set
    qsub -N truncate -b y -cwd -j y -V -t 1-100 -tc 1 \
        -l h_rt=287:00:00,num_proc=1,mem_free=1G \
        tube truncate \
            --block \
            $input_addr \
            ${int_key}:df-seen:22 \
            50 \
            ${int_key}:trunc50

    tube flow $input_addr ${int_key}:trunc50:nz set
    qsub -N filter-empty -b y -cwd -j y -V -t 1-100 -tc 1 \
        -l h_rt=287:00:00,num_proc=1,mem_free=1G \
        tube filter-empty \
            --block \
            --vocab-key ${int_key}/vocab${filter_leaf} \
            $input_addr \
            ${int_key}:trunc50{,:nz}

    qsub -N extract-bow -b y -cwd -j y -V -t 1-100 -tc 1 \
        -l h_rt=287:00:00,num_proc=1,mem_free=1G \
        tube extract-bow \
            --block \
            $input_addr \
            ${int_key}:trunc50:nz \
            ${int_key}/vocab${filter_leaf} \
            ${int_key}:trunc50:nz/bow${filter_leaf}

    tube flow $input_addr ${int_key}:nz set
    qsub -N filter-empty -b y -cwd -j y -V -t 1-100 -tc 1 \
        -l h_rt=287:00:00,num_proc=1,mem_free=1G \
        tube filter-empty \
            --block \
            --vocab-key ${int_key}/vocab${filter_leaf} \
            $input_addr \
            ${int_key}:df-seen:23 \
            ${int_key}:nz

    qsub -N extract-bow -b y -cwd -j y -V -t 1-100 -tc 1 \
        -l h_rt=287:00:00,num_proc=1,mem_free=1G \
        tube extract-bow \
            --block \
            $input_addr \
            ${int_key}:nz \
            ${int_key}/vocab${filter_leaf} \
            ${int_key}:nz/bow${filter_leaf}
done
