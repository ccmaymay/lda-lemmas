#!/bin/bash

set -e

data_dir=/export/projects/cmay

for p in dl dll
do
    bin/mallet train-topics \
        --optimize-burn-in 50 \
        --optimize-interval 10 \
        --num-topics 100 \
        --output-model-interval 50 \
        --output-model $data_dir/wiki.ru.${p}.trunc50.mallet-model \
        --input $data_dir/wiki.ru.${p}.trunc50.mallet
done
