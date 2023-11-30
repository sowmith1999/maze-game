FROM ubuntu:latest

RUN apt-get update && apt-get install -y \
    git \
    llvm \
    clang \
    make \
    ffmpeg \
    graphicsmagick \
    libgraphicsmagick++1-dev \
    libboost-all-dev 

RUN mkdir /root/videos

RUN apt-get update

WORKDIR /root

# RUN git clone https://github.com/sowmith1999/maze-game
COPY . /root/maze-game

WORKDIR /root/maze-game

RUN make

# ENTRYPOINT ["tail", "-f", "/dev/null"]
