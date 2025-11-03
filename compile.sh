#!/bin/bash
# Exit on error
set -e

COLS=4096
UNROLL=8

echo "--- Compiling with COLS=$COLS, UNROLL=$UNROLL ---"

echo "--- Compiling Metal Shader ---"
xcrun -sdk macosx metal -c c_src/nws.metal -o bin/nws.air \
    -D COLS=$COLS -D UNROLL=$UNROLL
xcrun -sdk macosx metallib bin/nws.air -o bin/nws.metallib

echo "--- Compiling C Code ---"
# -g -fsanitize=address may be useful.
# -O2 for speed
clang++ -std=c++17 -O2 -o bin/metal_nws c_src/metal_nws.mm \
    -I$HOME/metal-cpp \
    -D COLS=$COLS -D UNROLL=$UNROLL \
    -framework Foundation -framework Metal -framework QuartzCore

echo "--- Compilation Successful ---"
echo "To run: ./bin/metal_nws"