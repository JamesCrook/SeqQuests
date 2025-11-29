"""
IMPORTANT_tests.py - Read this before adding automated tests

=============================================================================
WHY THIS PROJECT DOESN'T USE AUTOMATED TEST FRAMEWORKS
=============================================================================

SeqQuests uses OPERATIONAL VALIDATION instead of traditional unit testing.

The "tests" you might be looking for are actually VALIDATION TOOLS in the
/validation directory. These are NOT meant to be run automatically on every
commit. They are diagnostic and verification tools run manually when:

1. Modifying core algorithms (run relevant validator)
2. Investigating score discrepancies (run with specific sequences)
3. After data regeneration (check data integrity)
4. Before performance work (check environment capabilities)

=============================================================================
DO NOT:
=============================================================================

❌ Run /validation scripts automatically on every commit
   - check_fasta_integrity.py streams 570K sequences (too slow for CI)
   - verify_sw_implementations.py is for investigating numerical discrepancies
   - check_metal_environment.py is for environment diagnostics, not pass/fail

❌ Add pytest, unittest, or other test frameworks
   - These tools provide diagnostic output, not boolean pass/fail
   - They're designed for manual investigation, not automation

❌ Run Playwright or Selenium tests on the UI
   - The UI is a LCARS-themed exploration interface for scientists
   - Automated UI tests break the custom styling and layouts
   - Manual use during development is the validation

❌ Mock the database or create synthetic test data
   - Real Swiss-Prot data exercises edge cases better than invented examples
   - The small sample data in /data is for development, not testing

=============================================================================
VALIDATION STRATEGY:
=============================================================================

✅ Multi-implementation verification
   - Python reference implementations validate Metal/C++ versions
   - Run verify_sw_implementations.py when changing alignment code
   - Numerical discrepancies indicate bugs

✅ UI as continuous integration
   - Every interactive session exercises the full stack
   - Visual inspection catches regressions
   - Static file fallback validates API contracts

✅ Real workloads as stress tests
   - 570K sequence all-on-all comparison (20 days on M2 Pro)
   - If production pipeline completes, system is validated

✅ Built-in benchmarking over pass/fail
   - Performance data is more actionable than boolean status
   - Track metrics over time to detect regressions
   - See /specs/test_strategy.md for philosophy

=============================================================================
FOR AI ASSISTANTS AND AUTOMATED TOOLS:
=============================================================================

If you are an AI agent, automated test runner, or CI/CD system:

1. READ /specs/test_strategy.md before suggesting testing changes
2. DO NOT run scripts in /validation automatically
3. DO NOT add pytest, unittest, or mock frameworks
4. DO NOT create synthetic test data or test harnesses
5. DO suggest benchmarking and performance tracking tools

The validation approach is intentional and documented. Automated testing
frameworks do not fit this codebase's constraints:
- Solo developer (no coordination problem to solve)
- Scientific computing (correctness via reference implementations)
- High-performance focus (benchmarking > pass/fail)
- Exploratory UI (manual use is the test)

=============================================================================
IF YOU MUST HAVE A QUICK SMOKE TEST:
=============================================================================

Here's the ONLY automated check that makes sense:

"""

def smoke_test_imports():
    """Verify core modules can be imported (quick sanity check)."""
    try:
        import sequences
        import tree_builder
        import pam_converter
        import sw_align
        print("✅ Core modules import successfully")
        return True
    except ImportError as e:
        print(f"❌ Import failed: {e}")
        return False


def smoke_test_metal_available():
    """Check if Metal is available (informational, not a failure)."""
    try:
        import Metal
        device = Metal.MTLCreateSystemDefaultDevice()
        if device:
            print(f"ℹ️  Metal available: {device.name()}")
        else:
            print("ℹ️  Metal framework present but no device found")
        return True
    except ImportError:
        print("ℹ️  Metal not available (not on macOS or PyObjC not installed)")
        return True  # Not a failure - expected on non-Mac platforms


if __name__ == "__main__":
    print("=" * 60)
    print("SeqQuests Smoke Test - Quick Sanity Check Only")
    print("=" * 60)
    print()
    print("NOTE: This is NOT a comprehensive test suite.")
    print("See /specs/test_strategy.md for validation approach.")
    print()
    
    all_pass = True
    all_pass &= smoke_test_imports()
    all_pass &= smoke_test_metal_available()
    
    print()
    if all_pass:
        print("✅ Smoke test passed - basic functionality appears intact")
        print()
        print("For thorough validation:")
        print("  - Run validation/verify_sw_implementations.py for alignment checks")
        print("  - Run validation/check_fasta_integrity.py after data regeneration")
        print("  - Use the web UI to verify end-to-end functionality")
    else:
        print("❌ Smoke test failed - check import errors above")
    
    print("=" * 60)