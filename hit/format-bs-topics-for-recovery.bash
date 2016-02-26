#!/bin/bash

dllk="$1"
dlk=`echo "$1" | sed 's/dll/dl/'`
dc="$2"

echo_experiment() {
    bs postproc list-global \
            --words-per-topic 5 --topic-ss-leaf beta-ss \
            --doc-count "$dc" \
            "$1" | \
        sed '/^$/d' | \
        while read line
            do
                echo "$line" | \
                    tr ' ' '\n' | \
                    sort | \
                    tr '\n' ' ' | \
                    sed 's/ $/\n/'
            done | \
        awk '{ print NR-1, $0 }' | \
        sed "s@^@$1 @" | \
        sed 's/ /\t/' | \
        sed 's/ /\t/'
}

(
    echo -e 'experiment\ttopic\tword-1 word-2 word-3 word-4 word-5'
    echo_experiment "$dllk"
    echo_experiment "$dlk"
) | sort
