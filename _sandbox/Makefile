CFLAGS=$(shell python-config --cflags) -Wall -Werror
LIBS=$(shell python-config --libs)
DYNLIB=_sandboxmodule.so

all: $(DYNLIB)

install: $(DYNLIB)
	install -o root -g root -m 644 $(DYNLIB) /usr/lib/python2.6/site-packages/

module.o: module.c
	$(CC) -c -o $@ $< $(CFLAGS)

$(DYNLIB): module.o
	$(CC) -o $@ $< $(CFLAGS) $(LIBS) -shared

clean:
	rm -f module.o _sandboxmodule.so

