#!/bin/bash

set -e

input_host=${1:-`hostname`}
input_port=${2:-1118}
base_key=wiki.ru

input_addr=${input_host}:${input_port}

for int_key in ${base_key}:dll ${base_key}:dl
do
    tube extract-vocab \
        --remove-non-alpha \
        --rank-lb 100 \
        --rank-ub 10100 \
        $input_addr \
        ${int_key}/df \
        ${int_key}/num-docs \
        ${int_key}/vocab:10k-100
done
