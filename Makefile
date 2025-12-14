CC = gcc
CFLAGS = -Wall -O2 -pthread
LIBS = -lssl -lcrypto
TARGET = payload/bot/bot
SRCDIR = payload/bot
SOURCES = $(SRCDIR)/bot.c $(SRCDIR)/attacks.c
OBJECTS = $(SRCDIR)/bot.o $(SRCDIR)/attacks.o
HEADERS = $(SRCDIR)/config.h $(SRCDIR)/attacks.h

all: update_config $(TARGET)

update_config:
	python3 payload/update_bot_config.py

$(TARGET): $(OBJECTS)
	$(CC) $(CFLAGS) -o $(TARGET) $(OBJECTS) $(LIBS)

$(SRCDIR)/%.o: $(SRCDIR)/%.c $(HEADERS)
	$(CC) $(CFLAGS) -c $< -o $@

clean:
	rm -f $(OBJECTS) $(TARGET)

run: $(TARGET)
	cd $(SRCDIR) && ./bot

.PHONY: all clean run