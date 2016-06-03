FROM ubuntu:latest
RUN apt-get update -y && \
    apt-get install -y \
        make \
        texlive \
        texlive-lang-cyrillic \
        texlive-latex-extra \
        texlive-science
RUN apt-get install -y make
ENV uid 500
RUN useradd -m -u $uid -s /bin/bash russian && \
    passwd -l russian
USER russian
VOLUME /home/russian/paper
WORKDIR /home/russian/paper
CMD ["bash", "-lc", "make"]
