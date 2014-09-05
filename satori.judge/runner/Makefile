PROGRAM=runner
DAEMON=runnerd
VERSION=0.9
.PHONY: build clean install
DESTROOT=$(DESTDIR)/usr
DESTBIN=$(DESTROOT)/bin
DESTSBIN=$(DESTROOT)/sbin
INSTALL=install

build: $(PROGRAM) $(DAEMON)

clean:
	rm -f $(PROGRAM)

install: build
	$(INSTALL) -s -m 755 $(PROGRAM) $(DESTBIN)/
	$(INSTALL) -m 755 $(DAEMON) $(DESTSBIN)/

runner : runner_main.cpp runner.cpp runner.h
	g++ -DVERSION=$(VERSION) -std=c++0x -g -Wall -O2 `curl-config --cflags` -o runner runner_main.cpp runner.cpp -lcap -lpthread -lpopt -lrt `curl-config --libs`
