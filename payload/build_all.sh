#!/bin/bash

SRC_DIR="./bot"
OUTPUT_DIR="binaries"
COMPILERS_DIR="compilers_extracted"

SUCCESS_COUNT=0
FAILED_COUNT=0

mkdir -p "$OUTPUT_DIR"

if [[ ! -d "$SRC_DIR" ]]; then
    echo "[!] Folder '$SRC_DIR' not found!"
    exit 1
fi

C_FILES=$(find "$SRC_DIR" -name "*.c")
if [[ -z "$C_FILES" ]]; then
    echo "[!] No .c files found in '$SRC_DIR'"
    exit 1
fi

USES_PTHREAD="no"
for file in $C_FILES; do
    if grep -q "pthread_" "$file"; then
        USES_PTHREAD="yes"
        break
    fi
done

echo "[i] Files found:"
echo "$C_FILES" | while read file; do echo "    - $file"; done
echo ""

for dir in "$COMPILERS_DIR"/*; do
    if [[ -d "$dir" ]]; then
        BIN_PATH=$(find "$dir" -type f -executable -name "*-gcc" | head -n 1)

        if [[ -n "$BIN_PATH" ]]; then
            ARCH=$(basename "$dir" | sed 's/cross-compiler-//')
            OUTFILE="$OUTPUT_DIR/bot.$ARCH"

            echo "[+] Compiling for $ARCH..."

            if [[ "$USES_PTHREAD" == "yes" ]]; then
                "$BIN_PATH" -std=c99 -static -w $C_FILES -o "$OUTFILE" -lpthread
            else
                "$BIN_PATH" -std=c99 -static -w $C_FILES -o "$OUTFILE"
            fi

            if [[ $? -eq 0 ]]; then
                SIZE=$(du -h "$OUTFILE" | cut -f1)
                echo "[✓] Success: $OUTFILE ($SIZE)"
                ((SUCCESS_COUNT++))
            else
                echo "[✗] Failed to compile for $ARCH"
                ((FAILED_COUNT++))
                
                ERROR_LOG=$("$BIN_PATH" -std=c99 -static -w $C_FILES -o "$OUTFILE" -lpthread 2>&1)
                
                if echo "$ERROR_LOG" | grep -q "relocation truncated to fit"; then
                    echo "    (Known toolchain limitation, not a code issue)"
                elif echo "$ERROR_LOG" | grep -q "\.h.*No such file or directory"; then
                    MISSING_HEADER=$(echo "$ERROR_LOG" | grep -o "[^/]*\.h" | head -n1)
                    echo ""
                    echo "════════════════════════════════════════════════════════════"
                    echo "  [!] ERROR: Missing header file: $MISSING_HEADER"
                    echo ""
                    echo "  Make sure all required .h files are in $SRC_DIR/"
                    echo "════════════════════════════════════════════════════════════"
                    echo ""
                fi
            fi
        else
            echo "[!] GCC not found in: $dir"
        fi
    fi
done

echo ""
echo "════════════════════════════════════════════════════════════"
echo "[✓] Compilation finished!"
echo ""
echo "Results: $SUCCESS_COUNT successful, $FAILED_COUNT failed"
echo ""
echo "Binaries location: $OUTPUT_DIR/"
ls -lh "$OUTPUT_DIR" 2>/dev/null | tail -n +2 | awk '{print "  • " $9 " (" $5 ")"}'
echo "════════════════════════════════════════════════════════════"