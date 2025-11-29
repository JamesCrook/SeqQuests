#!/usr/bin/env python3

"""
Metal Environment Diagnostic - Reports GPU capabilities and configuration.

This tool verifies that the Metal framework and PyObjC bindings are correctly
installed, and reports the capabilities of your GPU. It provides information
needed for performance optimization work.

Reports:
- Whether Metal module can be imported
- Available Metal device name
- Max threads per threadgroup (critical for kernel tuning)
- NumPy availability

Usage:
    python validation/check_metal_environment.py

When to run:
- On new development machines (verify environment setup)
- Before performance optimization work (know your hardware limits)
- When debugging "Metal not found" errors
- Before implementing the auto-tuning benchmark tool (need baseline capabilities)

The max threads per threadgroup is particularly important - it's one of the
parameters we currently tune manually in compile.sh (THREADS, UNROLL).
"""

try:
    import Metal
    print("✅ Metal module imported successfully")
    
    device = Metal.MTLCreateSystemDefaultDevice()
    if device:
        print(f"✅ Metal device found: {device.name()}")
        print(f"   Max threads per threadgroup: {device.maxThreadsPerThreadgroup()}")
    else:
        print("❌ No Metal device found")
        
except ImportError as e:
    print("❌ Failed to import Metal. You need to install PyObjC:")
    print("   pip install pyobjc-framework-Metal pyobjc-framework-Cocoa")
    print(f"   Error: {e}")

try:
    import numpy as np
    print("✅ NumPy imported successfully")
except ImportError:
    print("❌ NumPy not found. Install with: pip install numpy")
