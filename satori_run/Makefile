PROGRAM=satori_run
DAEMON=satori_rund
VERSION=1.0
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

satori_run : satori_run.cpp runner.cpp runner.h
	g++ -Wall -Wno-write-strings -DVERSION=$(VERSION) -std=c++0x -g `curl-config --cflags` -o $@ satori_run.cpp runner.cpp -lcap -lpthread -lpopt -lrt `curl-config --libs`
