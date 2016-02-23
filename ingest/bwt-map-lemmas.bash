#!/bin/bash

# Part 1 of:
# Example preprocessing procedure for Wikipedia tokens with POS and
# lemma taggings in tab-delimited format.

set -e

input_host=${1:-`hostname`}
input_port=${2:-1118}
input_dir=~rcotterell/wikipedia/data/formatted/ru
base_key=wiki.ru

input_addr=${input_host}:${input_port}

tube flow --count 10000 $input_addr '*' set

find $input_dir -type f -not -name '.*' -print0 \
    | xargs -0 redis-cli -h $input_host -p $input_port rpush ${base_key}/paths
qsub -N load-tab-tags -b y -cwd -j y -V -t 1-100 -tc 1 \
    -l h_rt=287:00:00,num_proc=1,mem_free=1G \
    tube load tab-tags \
        --backoff-unknown-lemma \
        $input_addr ${base_key}/paths ${base_key} POS LEMMA
int_key=${base_key}

qsub -N dedupe -b y -cwd -j y -V -t 1-100 -tc 1 \
    -l h_rt=287:00:00,num_proc=1,mem_free=1G \
    tube dedupe \
        --block \
        $input_addr ${int_key} ${int_key}:deduped ${int_key}/ids-seen
int_key=${int_key}:deduped

qsub -N extract-lemma-map -b y -cwd -j y -V -t 1-100 -tc 1 \
    -l h_rt=287:00:00,num_proc=1,mem_free=1G \
    tube extract-lemma-map \
        --block \
        --lowercase \
        $input_addr ${int_key} ${int_key}:lemmas-seen \
        ${base_key}:d/lemma-map
int_key=${int_key}:lemmas-seen

qsub -N dump -b y -cwd -j y -V -t 1-100 -tc 1 \
    -l h_rt=287:00:00,num_proc=1,mem_free=1G \
    tube dump \
        --block \
        --concrete \
        $input_addr ${int_key} /dev/null
