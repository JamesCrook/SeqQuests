#!/bin/bash
# Build script for sw_search_metal, including its kernel
# Exit on error
set -e

# Configuration: Allow overrides from environment, else auto-detect or default
METAL_CPP_PATH=${METAL_CPP_PATH:-"$HOME/metal-cpp"}

# Auto-detect chip logic if not provided
if [ -z "$THREADS" ] || [ -z "$UNROLL" ]; then
    # Get chip info
    CHIP=$(sysctl -n machdep.cpu.brand_string || echo "Unknown")

    if [[ $CHIP == *"M4 Pro"* ]]; then
        DEFAULT_THREADS=$((4096*4*4))
        DEFAULT_UNROLL=40
    elif [[ $CHIP == *"M3"* ]]; then
        DEFAULT_THREADS=$((4096*2))
        DEFAULT_UNROLL=40
    elif [[ $CHIP == *"M2 Pro"* ]]; then
        DEFAULT_THREADS=$((4096*2))
        DEFAULT_UNROLL=40
    elif [[ $CHIP == *"M1"* ]]; then
        DEFAULT_THREADS=$((4096))
        DEFAULT_UNROLL=32
    else
        DEFAULT_THREADS=$((4096))
        DEFAULT_UNROLL=32
    fi

    THREADS=${THREADS:-$DEFAULT_THREADS}
    UNROLL=${UNROLL:-$DEFAULT_UNROLL}

    if [ "$CHIP" == "Unknown" ]; then
        echo "Could not detect chip. Using default: THREADS=$THREADS, UNROLL=$UNROLL"
    else
         echo "Detected $CHIP. Using default: THREADS=$THREADS, UNROLL=$UNROLL"
    fi
else
    echo "Using user overrides: THREADS=$THREADS, UNROLL=$UNROLL"
fi


echo "--- Compiling with METAL_CPP_PATH=$METAL_CPP_PATH ---"
echo "--- Compiling Metal Shader ---"
xcrun -sdk macosx metal -c c_src/sw.metal -o bin/sw.air \
    -D THREADS=$THREADS -D UNROLL=$UNROLL
xcrun -sdk macosx metallib bin/sw.air -o bin/sw.metallib

echo "--- Compiling C Code (sw_search_metal) ---"
# -g -fsanitize=address may be useful.
# -O2 for speed
clang++ -std=c++17 -O2 -o bin/sw_search_metal c_src/sw_search_metal.mm \
    -I"$METAL_CPP_PATH" \
    -D THREADS=$THREADS -D UNROLL=$UNROLL \
    -framework Foundation -framework Metal -framework QuartzCore

echo "--- Compiling C Core Shared Library (sw_align) ---"
# Create shared library for Python ctypes
clang++ -std=c++17 -O3 -shared -undefined dynamic_lookup -o bin/libsw_align.dylib c_src/sw_align_core.cpp

echo "--- Compiling C++ Tree Builder ---"
clang++ -std=c++17 -O2 -o bin/tree_builder_cpp c_src/tree_builder.cpp

echo "--- Compilation Successful ---"
echo "To run: ./bin/sw_search_metal"
echo "To run: ./bin/tree_builder_cpp"
