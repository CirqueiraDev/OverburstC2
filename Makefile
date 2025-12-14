CC = gcc
CFLAGS = -Wall -O2 -pthread
TARGET = payload/bot/bot
SRCDIR = payload/bot
SOURCES = $(SRCDIR)/bot.c $(SRCDIR)/attacks.c
OBJECTS = $(SRCDIR)/bot.o $(SRCDIR)/attacks.o
HEADERS = $(SRCDIR)/config.h $(SRCDIR)/attacks.h

all: $(TARGET)

$(TARGET): $(OBJECTS)
	$(CC) $(CFLAGS) -o $(TARGET) $(OBJECTS)

$(SRCDIR)/%.o: $(SRCDIR)/%.c $(HEADERS)
	$(CC) $(CFLAGS) -c $< -o $@

clean:
	rm -f $(OBJECTS) $(TARGET)

run: $(TARGET)
	cd $(SRCDIR) && ./bot

.PHONY: all clean run