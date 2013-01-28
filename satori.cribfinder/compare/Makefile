.PHONY: all

all: parseClang compare03

parseClang: parseClang.cpp
	g++ -O3 parseClang.cpp -lclang -o $@

compare03: compare03.cpp hun.cpp
	g++ -O3 compare03.cpp -o $@
