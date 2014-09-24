PROGRAM=satori_run
DAEMONS=satori_rund satori_testd
TOOLS=satori_test
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
	$(INSTALL) -m 755 $(DAEMONS) $(DESTSBIN)/
	$(INSTALL) -m 755 $(TOOLS) $(DESTBIN)/

satori_run : satori_run.cpp runner.cpp runner.h
	g++ -Wall -Wno-write-strings -DVERSION=$(VERSION) -std=c++0x -g `curl-config --cflags` -o $@ satori_run.cpp runner.cpp -lcap -lpthread -lpopt -lrt `curl-config --libs`

ppa:
	dpkg-buildpackage -S
	dput ppa:satoriproject/satori ../satori-testing_*.changes
