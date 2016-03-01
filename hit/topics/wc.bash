#!/bin/bash
echo -e "                                         filename\tmin\tmean\tmedian\tmax";for f in *big.txt ; do l=`echo $f | wc | awk '{ print $3 }'` ; for i in {1..50} ; do if [ $(($i - $l)) -gt 0 ] ; then echo -n ' ' ; fi ; done ; echo -n $f ; for i in 1 2 3 4 ; do x=`./wc.py $f | cut -f $i | paste -s -d + - | bc` ; echo -en "\t$x" ; done ; echo ; done
