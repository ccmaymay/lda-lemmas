#!/bin/bash

set -e

while read line
do
    k=`echo "$line" | cut -f 3` ;
    t=`echo "$line" | cut -f 4` ;
    i=`echo "$line" | cut -f 5` ;
    w=`echo "$line" | cut -f 6- | awk -F '\t' -v f=$(($i+1)) '{for(i=1;i<=NF;i++)if(i==f)continue;else printf("%s%s",$i,(i!=NF)?" ":ORS)}' | tr ' ' '\n' | sort | tr '\n' ' ' | sed 's/ $/\n/'`
    echo "$k	$t	$w"
done < "$1" | sort
