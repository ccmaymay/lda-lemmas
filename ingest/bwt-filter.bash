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

tube flow --count 2000 $input_addr '*' set

for int_key in ${base_key}:dll ${base_key}:dl
do
    qsub -N clone -b y -cwd -j y -V -t 1-100 -tc 1 \
        -l h_rt=287:00:00,num_proc=1,mem_free=1G \
        tube clone \
            --block \
            $input_addr \
            ${int_key}:df-seen{:2,:3,:4}

    qsub -N clone -b y -cwd -j y -V -t 1-100 -tc 1 \
        -l h_rt=287:00:00,num_proc=1,mem_free=1G \
        tube clone \
            --block \
            $input_addr \
            ${int_key}:df-seen{:3,:5,:6}

    qsub -N truncate -b y -cwd -j y -V -t 1-100 -tc 1 \
        -l h_rt=287:00:00,num_proc=1,mem_free=1G \
        tube truncate \
            --block \
            $input_addr \
            ${int_key}:df-seen:4 \
            50 \
            ${int_key}:trunc50

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

    qsub -N filter-empty -b y -cwd -j y -V -t 1-100 -tc 1 \
        -l h_rt=287:00:00,num_proc=1,mem_free=1G \
        tube filter-empty \
            --block \
            --vocab-key ${int_key}/vocab${filter_leaf} \
            $input_addr \
            ${int_key}:df-seen:5 \
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
