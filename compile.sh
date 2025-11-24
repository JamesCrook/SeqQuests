#!/bin/bash
# Build script for sw_search_metal, including its kernel
# Exit on error
set -e

# Get chip info
CHIP=$(sysctl -n machdep.cpu.brand_string)

if [[ $CHIP == *"M4 Pro"* ]]; then
    THREADS=$((4096*4))
    UNROLL=40
elif [[ $CHIP == *"M3"* ]]; then
    THREADS=$((4096*2))
    UNROLL=40
elif [[ $CHIP == *"M2 Pro"* ]]; then
    THREADS=$((4096*2))
    UNROLL=40
elif [[ $CHIP == *"M1"* ]]; then
    THREADS=$((4096))
    UNROLL=32
else
    THREADS=$((4096))
    UNROLL=32
fi

echo "--- Compiling for $CHIP with THREADS=$THREADS, UNROLL=$UNROLL ---"

echo "--- Compiling Metal Shader ---"
xcrun -sdk macosx metal -c c_src/sw.metal -o bin/sw.air \
    -D THREADS=$THREADS -D UNROLL=$UNROLL
xcrun -sdk macosx metallib bin/sw.air -o bin/sw.metallib

echo "--- Compiling C Code (sw_search_metal) ---"
# -g -fsanitize=address may be useful.
# -O2 for speed
clang++ -std=c++17 -O2 -o bin/sw_search_metal c_src/sw_search_metal.mm \
    -I$HOME/metal-cpp \
    -D THREADS=$THREADS -D UNROLL=$UNROLL \
    -framework Foundation -framework Metal -framework QuartzCore

echo "--- Compiling C++ Tree Builder ---"
clang++ -std=c++17 -O2 -o bin/tree_builder_cpp c_src/tree_builder.cpp

echo "--- Compilation Successful ---"
echo "To run: ./bin/sw_search_metal"
echo "To run: ./bin/tree_builder_cpp"
