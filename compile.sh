#!/bin/bash
# Compiles the metal_nws project.

# Exit on error
set -e

echo "--- Compiling Metal Shader ---"
xcrun -sdk macosx metal -c c_src/nws.metal -o c_src/nws.air
xcrun -sdk macosx metallib c_src/nws.air -o c_src/nws.metallib

echo "--- Compiling C Code ---"
clang -ObjC -o c_src/metal_nws c_src/metal_nws.c -fmodules -framework Foundation -framework Metal -framework QuartzCore

echo "--- Compilation Successful ---"
echo "To run: ./c_src/metal_nws"
