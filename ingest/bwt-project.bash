#!/bin/bash

set -e

input_host=${1:-`hostname`}
input_port=${2:-1118}
base_key=wiki.ru

input_addr=${input_host}:${input_port}

input_vocab_key=${base_key}:dll/vocab:10k-100
lemma_map_key_stem=${base_key}:d/lemma-map
output_vocab_key=${base_key}:dl/vocab:10k-100:p

tube project-lemma-vocab \
    $input_addr \
    $input_vocab_key \
    $lemma_map_key_stem \
    $output_vocab_key
