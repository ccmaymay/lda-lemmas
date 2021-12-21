#!/bin/bash

set -e

sed=gsed
shuf=gshuf

for f in polyglot/en/*-100-0.keys.filtered.txt polyglot/??/*-100-0.keys.translated.filtered.txt
do
    echo '***'
    echo $f | $sed 's@^polyglot/@@;s@.lower.mallet.*$@@'
    $shuf -n 4 $f | \
        cut -d '	' -f 3 | \
        cut -d ' ' -f 1-5
done | column
