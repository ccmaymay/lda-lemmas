#!/usr/bin/env python2.7
import sys
import codecs
with codecs.open(sys.argv[1], encoding='utf-8') as f:
    for line in f:
        words = line.strip().split()
        lengths = tuple(len(w) for w in words)
        length_min = min(lengths)
        length_mean = sum(lengths) / float(len(lengths))
        length_median = sorted(lengths)[len(lengths)/2 + 1]
        length_max = max(lengths)
        print '%d\t%d\t%d\t%d' % (length_min, length_mean, length_median,
                                  length_max)
