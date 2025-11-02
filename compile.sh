#!/bin/bash
# Compiles the metal_nws project.

# Exit on error
set -e

echo "--- Compiling Metal Shader ---"
xcrun -sdk macosx metal -c c_src/nws.metal -o bin/nws.air
xcrun -sdk macosx metallib bin/nws.air -o bin/nws.metallib

echo "--- Compiling C Code ---"
#clang++ -std=c++17 -g -fsanitize=address -o bin/metal_nws c_src/metal_nws.mm -I$HOME/metal-cpp -framework Foundation -framework Metal -framework QuartzCore
clang++ -std=c++17 -O2 -o bin/metal_nws c_src/metal_nws.mm -I$HOME/metal-cpp -framework Foundation -framework Metal -framework QuartzCore

echo "--- Compilation Successful ---"
echo "To run: ./c_src/metal_nws"
