# Follow-up

Follow-up to original lda-lemmas study.

## Resources & Dependencies:

### Polyglot Corpus

Download the polyglot corpora from [Rami Al-Rfou's Polyglot
page](https://sites.google.com/site/rmyeid/projects/polyglot).
As of the time of writing, you must request permission to access each
file; you may do this by clicking the respective link and then
requesting access through Google Drive.

### TreeTagger

[Download and install
TreeTagger](https://www.cis.uni-muenchen.de/~schmid/tools/TreeTagger/),
and download the following model
parameters, to a subdirectory `treetagger` of this directory:

* [english](https://www.cis.uni-muenchen.de/~schmid/tools/TreeTagger/data/english.par.gz)
* [persian](https://www.cis.uni-muenchen.de/~schmid/tools/TreeTagger/data/persian.par.gz)
* [korean](https://www.cis.uni-muenchen.de/~schmid/tools/TreeTagger/data/korean.par.gz)
* [russian](https://www.cis.uni-muenchen.de/~schmid/tools/TreeTagger/data/russian.par.gz)

### UDPipe

Download and unpack [UDPipe](https://ufal.mff.cuni.cz/udpipe/1) to a
subdirectory `udpipe` of this directory.  I downloaded the pre-compiled
binaries for [UDPipe
1.2.0](https://github.com/ufal/udpipe/releases/tag/v1.2.0).

Then, download models from [the UD 2.5 UDPipe models
page](https://lindat.mff.cuni.cz/repository/xmlui/handle/11234/1-3131)
to the `udpipe` subdirectory:

* [English](https://lindat.mff.cuni.cz/repository/xmlui/bitstream/handle/11234/1-3131/english-ewt-ud-2.5-191206.udpipe?sequence=17&isAllowed=y)
* [Persian](https://lindat.mff.cuni.cz/repository/xmlui/bitstream/handle/11234/1-3131/persian-seraji-ud-2.5-191206.udpipe?sequence=78&isAllowed=y)
* [Korean](https://lindat.mff.cuni.cz/repository/xmlui/bitstream/handle/11234/1-3131/korean-kaist-ud-2.5-191206.udpipe?sequence=61&isAllowed=y)
* [Russian](https://lindat.mff.cuni.cz/repository/xmlui/bitstream/handle/11234/1-3131/russian-syntagrus-ud-2.5-191206.udpipe?sequence=70&isAllowed=y)

### MALLET

Download and unpack [MALLET](http://mallet.cs.umass.edu/download.php)
to a subdirectory `mallet` of this directory.  I downloaded MALLET
version 2.0.8.
