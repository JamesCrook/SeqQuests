#!/bin/bash
# Script to compile the C++ Smith-Waterman implementation to WebAssembly
# Requires Emscripten (emcc)

# Output directory
mkdir -p static

# Source file
SRC="c_src/sw_align_core.cpp"
OUT="static/sw_align.wasm"

echo "Compiling $SRC to $OUT..."

if command -v emcc &> /dev/null; then
    # Compile with Emscripten
    # -O3: Optimize for speed
    # --no-entry: No main() function, just a library
    # -s EXPORTED_FUNCTIONS: Export our function and memory management
    # -s ERROR_ON_UNDEFINED_SYMBOLS=0: Allow missing symbols if any (usually not needed for this)
    # -s IMPORTED_MEMORY=1: Allow importing memory from JS (optional, but good for control)
    # Actually, for the simplified loader in HTML, we let WASM manage its own memory but export malloc/free.

    OUT_JS="static/sw_align_module.js"

    emcc "$SRC" \
        -O3 \
        -s WASM=1 \
        -s EXPORTED_FUNCTIONS="['_align_local_core', '_malloc', '_free']" \
        -s EXPORTED_RUNTIME_METHODS="['wasmMemory', 'HEAPU8', 'HEAP32', 'HEAPF32']" \
        -s ALLOW_MEMORY_GROWTH=1 \
        -s MODULARIZE=1 \
        -s EXPORT_NAME="createWasmModule" \
        -o "$OUT_JS"

    echo "Compilation complete. File created at $OUT"
    echo "You can now open static/fast-align.html to test the WASM implementation."

else
    echo "Error: 'emcc' (Emscripten) not found in PATH."
    echo "Please install Emscripten or use the Docker command below:"
    echo ""
    echo "docker run --rm -v \$(pwd):/src -u \$(id -u):\$(id -g) emscripten/emsdk emcc c_src/sw_align_core.cpp -O3 -s WASM=1 --no-entry -s EXPORTED_FUNCTIONS=\"['_align_local_core', '_malloc', '_free']\" -s ALLOW_MEMORY_GROWTH=1 -o static/sw_align.wasm"
fi
