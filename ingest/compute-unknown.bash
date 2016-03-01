#!/bin/bash

set -e

o=~/lda-lemmas/ingest/unknown.tsv
echo -e "filename\tunknown\ttokens\tlines" | tee $o
for f in *
do
    n=`cut -f 3 $f | sed '/^$/d' | wc -l`
    u=`cut -f 3 $f | grep '^<unknown>$' | wc -l`
    b=`wc -l < $f`
    echo -e "$f\t$u\t$n\t$b"
done | tee -a $o
