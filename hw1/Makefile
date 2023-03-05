CC := g++
CFLAGS := -I include -lpcap

.PHONY: all clean

all: main

clean:
	rm -rf main

main: main.cpp
	$(CC) -o $@ $< $(CFLAGS)