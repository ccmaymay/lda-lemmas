#!/bin/bash

set -e

k="$1"
f="$2"

bash recover-tsv-topics.bash $f > a

dc=4000
while true
do
    echo "trying doc count $dc ..."
    bash format-bs-topics-for-recovery.bash $k $dc > b
    if diff a b
    then
        echo "$k doc count matching $f: $dc"
        break
    fi
    dc=$((2*$dc))
done
