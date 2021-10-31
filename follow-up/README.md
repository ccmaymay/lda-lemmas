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

### Polyglot Lemmatizer

I was unable to successfully install polyglot on a managed system, or
at all when using poetry, but your results may vary.  The main issue 
I had was installing the `PyICU` package, one of polyglot's effective
dependencies; pip did not automatically install it for me when I
installed the `polyglot` package.  Specifically, I found that the
following additional Python packages were necessary:

* `six`
* `numpy`
* `Morfessor`
* `PyICU`
* `pycld2`

To install polyglot sufficiently for lemmatization to work, I did the
following on my Ubuntu 20.04 system (note, these commands seem to be
sufficient, but they might not all be necessary):

```
sudo apt-get update -y
sudo apt-get upgrade -y
sudo apt-get install -y \
    build-essential \
    python3{,-dev,-icu,-numpy,-pip,-six}
pip3 install --user morfessor pycld2 polyglot
export PATH=$HOME/.local/bin:$PATH
```

After installing polyglot and its dependencies, download the required
models with the following commands:

```
polyglot download morph2.en
polyglot download morph2.fa
polyglot download morph2.ko
polyglot download morph2.ru
```

Run the following command to test that polyglot's lemmatizer works:

```
python3 -c 'from polyglot.text import Text; print(Text("Hello, world!").morphemes)'
```

Since I did not install polyglot in poetry, it was also necessary in
my case to manually install the remaining dependencies for my
experiments; it sufficed to use `pip` to install the packages listed in
`pyproject.toml` under `tool.poetry.dependencies`.

### UDPipe

Download and install UDPipe from [the UDPipe home
page](https://ufal.mff.cuni.cz/udpipe/1) to a subdirectory `udpipe` of
this directory.  I downloaded the pre-compiled binaries for [UDPipe
1.2.0](https://github.com/ufal/udpipe/releases/tag/v1.2.0), so all that
was necessary to install UDPipe was unzipping the archive and renaming
the unzipped `udpipe-1.2.0-bin` directory to `udpipe`.

Then, download models from [the UD 2.5 UDPipe models
page](https://lindat.mff.cuni.cz/repository/xmlui/handle/11234/1-3131)
to the `udpipe` subdirectory:

* [English](https://lindat.mff.cuni.cz/repository/xmlui/bitstream/handle/11234/1-3131/english-ewt-ud-2.5-191206.udpipe?sequence=17&isAllowed=y)
* [Persian](https://lindat.mff.cuni.cz/repository/xmlui/bitstream/handle/11234/1-3131/persian-seraji-ud-2.5-191206.udpipe?sequence=78&isAllowed=y)
* [Korean](https://lindat.mff.cuni.cz/repository/xmlui/bitstream/handle/11234/1-3131/korean-kaist-ud-2.5-191206.udpipe?sequence=61&isAllowed=y)
* [Russian](https://lindat.mff.cuni.cz/repository/xmlui/bitstream/handle/11234/1-3131/russian-syntagrus-ud-2.5-191206.udpipe?sequence=70&isAllowed=y)
