#!/usr/bin/env python3
"""
Simple test to check if PyObjC and Metal are available
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
