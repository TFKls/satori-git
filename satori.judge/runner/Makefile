PROGRAM=runner
VERSION=0.9
.PHONY: all build clean prepare

all: build

build: ${PROGRAM}

clean:
	rm -f ${PROGRAM}

prepare:
	sudo apt-get install libpopt-dev libcap-dev libcurl4-openssl-dev libyaml-dev

runner : runner_main.cpp runner.cpp runner.h
	g++ -DVERSION=${VERSION} -g -Wall -O2 `curl-config --cflags` -o runner runner_main.cpp runner.cpp -lcap -lpthread -lpopt -lrt `curl-config --libs` -lyaml
