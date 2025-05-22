#!/bin/bash

SRC="bot.c"
OUTPUT_DIR="binarios"
COMPILERS_DIR="compilers_extracted"

mkdir -p "$OUTPUT_DIR"

# Verifica se bot.c usa pthreads
USES_PTHREAD=$(grep -q "pthread_" "$SRC" && echo "yes" || echo "no")

for dir in "$COMPILERS_DIR"/*; do
    if [[ -d "$dir" ]]; then
        BIN_PATH=$(find "$dir" -type f -executable -name "*-gcc" | head -n 1)

        if [[ -n "$BIN_PATH" ]]; then
            ARCH=$(basename "$dir" | sed 's/cross-compiler-//')
            OUTFILE="$OUTPUT_DIR/bot.$ARCH"

            echo "[+] Compilando para $ARCH..."

            if [[ "$USES_PTHREAD" == "yes" ]]; then
                "$BIN_PATH" -std=c99 -static -w "$SRC" -o "$OUTFILE" -lpthread
            else
                "$BIN_PATH" -std=c99 -static -w "$SRC" -o "$OUTFILE"
            fi

            if [[ $? -eq 0 ]]; then
                echo "[✔] Sucesso: $OUTFILE"
            else
                echo "[✘] Falha ao compilar para $ARCH"
            fi
        else
            echo "[!] GCC não encontrado em: $dir"
        fi
    fi
done