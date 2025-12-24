CC = gcc
CFLAGS = -Wall -O2 -pthread
SRCDIR = payload/bot
TARGET = $(SRCDIR)/bot
SOURCES = $(SRCDIR)/bot.c $(SRCDIR)/attacks.c $(SRCDIR)/hmac.c
OBJECTS = $(SRCDIR)/bot.o $(SRCDIR)/attacks.o $(SRCDIR)/hmac.o
HEADERS = $(SRCDIR)/config.h $(SRCDIR)/attacks.h $(SRCDIR)/hmac.h

all: update_config $(TARGET)

update_config:
	python3 payload/update_bot_config.py

$(TARGET): $(OBJECTS)
	$(CC) $(CFLAGS) -o $(TARGET) $(OBJECTS)

$(SRCDIR)/bot.o: $(SRCDIR)/bot.c $(SRCDIR)/config.h $(SRCDIR)/attacks.h $(SRCDIR)/hmac.h
	$(CC) $(CFLAGS) -c $(SRCDIR)/bot.c -o $(SRCDIR)/bot.o

$(SRCDIR)/attacks.o: $(SRCDIR)/attacks.c $(SRCDIR)/attacks.h $(SRCDIR)/config.h
	$(CC) $(CFLAGS) -c $(SRCDIR)/attacks.c -o $(SRCDIR)/attacks.o

$(SRCDIR)/hmac.o: $(SRCDIR)/hmac.c $(SRCDIR)/hmac.h
	$(CC) $(CFLAGS) -c $(SRCDIR)/hmac.c -o $(SRCDIR)/hmac.o

clean:
	rm -f $(OBJECTS) $(TARGET)

run: $(TARGET)
	cd $(SRCDIR) && ./bot

# Cross-compile targets
arm:
	$(MAKE) CC=arm-linux-gnueabi-gcc

mips:
	$(MAKE) CC=mips-linux-gnu-gcc

x86_64:
	$(MAKE) CC=x86_64-linux-gnu-gcc

aarch64:
	$(MAKE) CC=aarch64-linux-gnu-gcc

.PHONY: all clean run update_config arm mips x86_64 aarch64