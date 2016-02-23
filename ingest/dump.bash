#!/bin/bash

# Example of dumping a BOW dataset in redis (from tube) to
# the MALLET text format and then importing to the MALLET
# binary format on disk.

set -e

input_host=${1:-`hostname`}
input_port=${2:-1118}
output_dir=/export/projects/cmay

input_addr=${input_host}:${input_port}

for p in dl dll
do
    tube dump-bow-mallet \
        $input_addr \
        wiki.ru:${p}:trunc50:nz/bow \
        wiki.ru:${p}/vocab \
        $output_dir/wiki.ru.${p}.trunc50.mallet-txt
    bin/mallet import-file \
        --token-regex '\S+' \
        --preserve-case TRUE \
        --keep-sequence \
        --input $outpur_dir/wiki.ru.${p}.trunc50.mallet-txt \
        --output $output_dir/wiki.ru.${p}.trunc50.mallet
done
