#!/bin/bash

# Part 2 of:
# Example preprocessing procedure for Wikipedia tokens with POS and
# lemma taggings in tab-delimited format.

set -e

input_host=${1:-`hostname`}
input_port=${2:-1118}
base_key=wiki.ru

input_addr=${input_host}:${input_port}

int_key=${base_key}:dl

tube flow $input_addr ${int_key}:df-seen:15 set
qsub -N clone -b y -cwd -j y -V -t 1-100 -tc 1 \
    -l h_rt=287:00:00,num_proc=1,mem_free=1G \
    tube clone \
        --block \
        $input_addr \
        ${int_key}:df-seen{:14,:15,:16}

tube flow $input_addr ${int_key}:trunc50 set
qsub -N truncate -b y -cwd -j y -V -t 1-100 -tc 1 \
    -l h_rt=287:00:00,num_proc=1,mem_free=1G \
    tube truncate \
        --block \
        $input_addr \
        ${int_key}:df-seen:15 \
        50 \
        ${int_key}:trunc50

tube flow $input_addr ${int_key}:trunc50:nz set
qsub -N filter-empty -b y -cwd -j y -V -t 1-100 -tc 1 \
    -l h_rt=287:00:00,num_proc=1,mem_free=1G \
    tube filter-empty \
        --block \
        --vocab-key ${int_key}/vocab \
        $input_addr \
        ${int_key}:trunc50{,:nz}

qsub -N extract-bow -b y -cwd -j y -V -t 1-100 -tc 1 \
    -l h_rt=287:00:00,num_proc=1,mem_free=1G \
    tube extract-bow \
        --block \
        $input_addr \
        ${int_key}:trunc50:nz \
        ${int_key}/vocab \
        ${int_key}:trunc50:nz/bow

int_key=${base_key}:dll

tube flow $input_addr ${int_key}:df-seen:7 set
qsub -N clone -b y -cwd -j y -V -t 1-100 -tc 1 \
    -l h_rt=287:00:00,num_proc=1,mem_free=1G \
    tube clone \
        --block \
        $input_addr \
        ${int_key}:df-seen{:6,:7,:8}

tube flow $input_addr ${int_key}:trunc50 set
qsub -N truncate -b y -cwd -j y -V -t 1-100 -tc 1 \
    -l h_rt=287:00:00,num_proc=1,mem_free=1G \
    tube truncate \
        --block \
        $input_addr \
        ${int_key}:df-seen:7 \
        50 \
        ${int_key}:trunc50

tube flow $input_addr ${int_key}:trunc50:nz set
qsub -N filter-empty -b y -cwd -j y -V -t 1-100 -tc 1 \
    -l h_rt=287:00:00,num_proc=1,mem_free=1G \
    tube filter-empty \
        --block \
        --vocab-key ${int_key}/vocab \
        $input_addr \
        ${int_key}:trunc50{,:nz}

qsub -N extract-bow -b y -cwd -j y -V -t 1-100 -tc 1 \
    -l h_rt=287:00:00,num_proc=1,mem_free=1G \
    tube extract-bow \
        --block \
        $input_addr \
        ${int_key}:trunc50:nz \
        ${int_key}/vocab \
        ${int_key}:trunc50:nz/bow
