#!/usr/bin/env python3
"""
ready_to_rock.py - Environment setup checker and fixer

Validates that all prerequisites are in place for running the web server
and long-running jobs. Offers to fix issues where possible.
"""

import os
import sys
import shutil
import subprocess
import platform
from pathlib import Path
from dataclasses import dataclass, field
from typing import Callable, Optional
from enum import Enum

# Try to load .env early so checks can use the values
def load_env_file(env_path: Path) -> dict[str, str]:
    """Parse .env file and return dict of values (also sets os.environ)."""
    values = {}
    if env_path.exists():
        with open(env_path) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, _, value = line.partition('=')
                    key = key.strip()
                    value = value.strip().strip('"').strip("'")
                    # Expand ~ and env vars
                    value = os.path.expanduser(os.path.expandvars(value))
                    values[key] = value
                    os.environ.setdefault(key, value)
    return values

# Script is in py/ready_to_rock.py, so repo root is parent
PROJECT_ROOT = Path(__file__).parent.parent.resolve()
os.chdir(PROJECT_ROOT)

ENV_FILE = PROJECT_ROOT / ".env"
ENV_VALUES = load_env_file(ENV_FILE)


def get_env(key: str, default: str = "") -> str:
    """Get an environment value, with ~ expansion."""
    return ENV_VALUES.get(key, os.environ.get(key, default))


class Status(Enum):
    OK = "ok"
    MISSING = "missing"
    ERROR = "error"
    SKIPPED = "skipped"


@dataclass
class CheckResult:
    status: Status
    message: str
    details: Optional[str] = None
    fixable: bool = False
    fix_action: Optional[Callable] = None


@dataclass
class Check:
    name: str
    description: str
    check_fn: Callable[[], CheckResult]
    category: str = "general"
    depends_on: Optional[str] = None  # Name of check this depends on
    critical: bool = False  # If True, stop all checks on failure


# ============================================================================
# Configuration - paths relative to PROJECT_ROOT
# ============================================================================

ENV_EXAMPLE = PROJECT_ROOT / ".env.example"
COMPILE_SCRIPT = PROJECT_ROOT / "compile.sh"
COMPILE_WASM_SCRIPT = PROJECT_ROOT / "compile_wasm.sh"
GET_UNIPROT_SCRIPT = PROJECT_ROOT / "get_uniprot.sh"


# ============================================================================
# Utility functions
# ============================================================================

def run_command(cmd: list[str], cwd: Path = PROJECT_ROOT) -> tuple[int, str, str]:
    """Run a command and return (returncode, stdout, stderr)."""
    try:
        result = subprocess.run(
            cmd,
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=300
        )
        return result.returncode, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        return -1, "", "Command timed out"
    except Exception as e:
        return -1, "", str(e)


def prompt_yes_no(question: str, default: bool = True) -> bool:
    """Prompt user for yes/no answer."""
    suffix = " [Y/n] " if default else " [y/N] "
    while True:
        response = input(question + suffix).strip().lower()
        if response == "":
            return default
        if response in ("y", "yes"):
            return True
        if response in ("n", "no"):
            return False
        print("Please answer 'y' or 'n'")


# ============================================================================
# Individual checks
# ============================================================================

def check_python_version() -> CheckResult:
    """Check Python version is 3.9+."""
    version = sys.version_info
    if version >= (3, 9):
        return CheckResult(
            Status.OK,
            f"Python {version.major}.{version.minor}.{version.micro}"
        )
    return CheckResult(
        Status.ERROR,
        f"Python {version.major}.{version.minor} found, need 3.9+",
        fixable=False
    )


def check_apple_silicon() -> CheckResult:
    """Check if running on Apple Silicon (for Metal support)."""
    if platform.system() != "Darwin":
        return CheckResult(
            Status.SKIPPED,
            "Not on macOS, Metal components not applicable"
        )
    
    # Check for Apple Silicon
    machine = platform.machine()
    if machine == "arm64":
        # Get chip name
        try:
            result = subprocess.run(
                ["sysctl", "-n", "machdep.cpu.brand_string"],
                capture_output=True, text=True
            )
            chip = result.stdout.strip() if result.returncode == 0 else "Apple Silicon"
        except Exception:
            chip = "Apple Silicon"
        return CheckResult(Status.OK, f"{chip}")
    
    return CheckResult(
        Status.MISSING,
        f"Intel Mac detected ({machine}), Metal acceleration unavailable",
        details="Metal components require Apple Silicon for optimal performance"
    )


def check_metal_cpp() -> CheckResult:
    """Check if metal-cpp is available."""
    if platform.system() != "Darwin":
        return CheckResult(Status.SKIPPED, "Not on macOS")
    
    # Check METAL_CPP_PATH from .env first, then fallback locations
    env_path = get_env("METAL_CPP_PATH")
    search_paths = []
    
    if env_path:
        search_paths.append(Path(env_path))
    
    search_paths.extend([
        Path("/usr/local/include/metal-cpp"),
        Path("/opt/homebrew/include/metal-cpp"),
        Path.home() / "metal-cpp",
        Path.home() / "metal",
        PROJECT_ROOT / "metal-cpp",
        PROJECT_ROOT / "vendor" / "metal-cpp",
    ])
    
    for path in search_paths:
        if path.exists() and (path / "Metal" / "Metal.hpp").exists():
            return CheckResult(Status.OK, f"Found at {path}")
    
    if env_path:
        return CheckResult(
            Status.MISSING,
            f"metal-cpp not found at METAL_CPP_PATH={env_path}",
            details="Download from https://developer.apple.com/metal/cpp/ and extract to that path",
            fixable=False
        )
    
    return CheckResult(
        Status.MISSING,
        "metal-cpp not found (METAL_CPP_PATH not set in .env)",
        details="Set METAL_CPP_PATH in .env and download from https://developer.apple.com/metal/cpp/",
        fixable=False
    )


def check_package_installed() -> CheckResult:
    """Check if the package is installed in editable mode."""
    # Check for .egg-info directory (created by pip install -e .)
    # Could be at root or in py/ depending on where pyproject.toml is
    egg_info = list(PROJECT_ROOT.glob("*.egg-info")) + list((PROJECT_ROOT / "py").glob("*.egg-info"))
    if egg_info:
        return CheckResult(Status.OK, f"Package installed ({egg_info[0].name})")
    
    # Also check site-packages for editable install marker
    code, stdout, stderr = run_command([sys.executable, "-m", "pip", "show", "-f", "."])
    if code == 0 and "Editable project location" in stdout:
        return CheckResult(Status.OK, "Package installed (editable)")
    
    def fix():
        print("  Running: pip install -e .")
        code, stdout, stderr = run_command([sys.executable, "-m", "pip", "install", "-e", "."])
        if code != 0:
            print(f"  Error: {stderr}")
            return False
        return True
    
    return CheckResult(
        Status.MISSING,
        "Package not installed",
        details="Run: pip install -e .",
        fixable=True,
        fix_action=fix
    )


def check_env_file() -> CheckResult:
    """Check if .env file exists and has required variables."""
    global ENV_VALUES
    
    if not ENV_FILE.exists():
        def fix():
            global ENV_VALUES
            if ENV_EXAMPLE.exists():
                print(f"  Copying {ENV_EXAMPLE} to {ENV_FILE}")
                shutil.copy(ENV_EXAMPLE, ENV_FILE)
                # Reload env values
                ENV_VALUES = load_env_file(ENV_FILE)
                print("  ⚠️  Please edit .env to customize paths for your environment")
                return True
            else:
                print(f"  Error: {ENV_EXAMPLE} not found")
                return False
        
        return CheckResult(
            Status.MISSING,
            ".env file not found",
            details=f"Copy from {ENV_EXAMPLE}",
            fixable=ENV_EXAMPLE.exists(),
            fix_action=fix
        )
    
    # Check for required variables
    required_vars = ["SEQQUESTS_DATA_DIR", "METAL_CPP_PATH"]
    missing = []
    
    with open(ENV_FILE) as f:
        content = f.read()
        for var in required_vars:
            # Check if variable is defined (not just commented out)
            if not any(
                line.strip().startswith(f"{var}=") 
                for line in content.splitlines() 
                if not line.strip().startswith('#')
            ):
                missing.append(var)
    
    if missing:
        return CheckResult(
            Status.ERROR,
            f".env missing variables: {', '.join(missing)}",
            details="Edit .env to add missing variables"
        )
    
    return CheckResult(Status.OK, ".env configured")


def check_compiled_metal() -> CheckResult:
    """Check if Metal components are compiled."""
    if platform.system() != "Darwin":
        return CheckResult(Status.SKIPPED, "Not on macOS")
    
    bin_dir = PROJECT_ROOT / "bin"
    required_files = [
        "sw.metallib",
        "sw_search_metal",
        "libsw_align.dylib",
        "tree_builder_cpp",
    ]
    
    missing = [f for f in required_files if not (bin_dir / f).exists()]
    
    if not missing:
        # Try to detect THREADS/UNROLL from the metallib or binary
        # We can check what values would be used based on chip
        try:
            result = subprocess.run(
                ["sysctl", "-n", "machdep.cpu.brand_string"],
                capture_output=True, text=True
            )
            chip = result.stdout.strip() if result.returncode == 0 else ""
            
            if "M4 Pro" in chip:
                threads, unroll = 4096*4*4, 40
            elif "M3" in chip:
                threads, unroll = 4096*2, 40
            elif "M2 Pro" in chip:
                threads, unroll = 4096*2, 40
            else:
                threads, unroll = 4096, 32
            
            return CheckResult(
                Status.OK, 
                f"Found all binaries (THREADS={threads}, UNROLL={unroll})"
            )
        except Exception:
            pass
        
        return CheckResult(Status.OK, f"Found all binaries in bin/")
    
    def fix():
        if not COMPILE_SCRIPT.exists():
            print(f"  Error: {COMPILE_SCRIPT} not found")
            return False
        print(f"  Running: {COMPILE_SCRIPT}")
        code, stdout, stderr = run_command(["bash", str(COMPILE_SCRIPT)])
        print(stdout)
        if code != 0:
            print(f"  Error: {stderr}")
            return False
        return True
    
    return CheckResult(
        Status.MISSING,
        f"Missing: {', '.join(missing)}",
        details="Run: ./compile.sh",
        fixable=COMPILE_SCRIPT.exists(),
        fix_action=fix
    )


def check_compiled_wasm() -> CheckResult:
    """Check if WASM components are compiled."""
    # Check for compiled output from compile_wasm.sh
    wasm_js = PROJECT_ROOT / "static" / "sw_align_module.js"
    wasm_file = PROJECT_ROOT / "static" / "sw_align_module.wasm"
    
    if wasm_js.exists():
        size_kb = wasm_js.stat().st_size / 1024
        return CheckResult(Status.OK, f"Found sw_align_module.js ({size_kb:.1f} KB)")
    
    # Check if emscripten is available
    emcc = shutil.which("emcc")
    
    def fix():
        if not COMPILE_WASM_SCRIPT.exists():
            print(f"  Error: {COMPILE_WASM_SCRIPT} not found")
            return False
        print(f"  Running: {COMPILE_WASM_SCRIPT}")
        code, stdout, stderr = run_command(["bash", str(COMPILE_WASM_SCRIPT)])
        print(stdout)
        if code != 0:
            print(f"  Error: {stderr}")
            return False
        return True
    
    if not emcc:
        return CheckResult(
            Status.MISSING,
            "WASM not compiled, Emscripten (emcc) not found",
            details="Install Emscripten or use Docker (see compile_wasm.sh)",
            fixable=False
        )
    
    return CheckResult(
        Status.MISSING,
        "WASM components not compiled",
        details="Run: ./compile_wasm.sh",
        fixable=COMPILE_WASM_SCRIPT.exists(),
        fix_action=fix
    )


def check_uniprot_data() -> CheckResult:
    """Check if Uniprot data files are installed."""
    data_dir = get_env("SEQQUESTS_DATA_DIR")
    
    # Check locations for Uniprot data
    data_paths = []
    if data_dir:
        data_paths.append(Path(data_dir))
        data_paths.append(Path(data_dir) / "uniprot")
    
    data_paths.extend([
        PROJECT_ROOT / "data" / "uniprot",
        Path.home() / "data" / "seqquests",
    ])
    
    required_files = [
        "uniprot_sprot.fasta",
        # Add other required files
    ]
    
    for search_dir in data_paths:
        if search_dir.exists():
            found_all = all((search_dir / f).exists() for f in required_files)
            if found_all:
                return CheckResult(Status.OK, f"Found at {search_dir}")
    
    def fix():
        if not GET_UNIPROT_SCRIPT.exists():
            print(f"  Error: {GET_UNIPROT_SCRIPT} not found")
            return False
        print(f"  Running: {GET_UNIPROT_SCRIPT}")
        print("  (This may take a while, downloading large files...)")
        code, stdout, stderr = run_command(["bash", str(GET_UNIPROT_SCRIPT)])
        if code != 0:
            print(f"  Error: {stderr}")
            return False
        return True
    
    if data_dir:
        msg = f"Uniprot data not found in SEQQUESTS_DATA_DIR={data_dir}"
    else:
        msg = "Uniprot data not found (SEQQUESTS_DATA_DIR not set)"
    
    return CheckResult(
        Status.MISSING,
        msg,
        details="Run: ./get_uniprot.sh",
        fixable=GET_UNIPROT_SCRIPT.exists(),
        fix_action=fix
    )


def check_binary_data() -> CheckResult:
    """Check if prepared binary data files exist."""
    data_dir = PROJECT_ROOT / "data"
    pam_file = data_dir / "pam250.bin"
    fasta_file = data_dir / "fasta.bin"
    prepare_script = PROJECT_ROOT / "py" / "prepare_binary_data.py"
    
    missing = []
    if not pam_file.exists():
        missing.append("pam250.bin")
    if not fasta_file.exists():
        missing.append("fasta.bin")
    
    if not missing:
        pam_size = pam_file.stat().st_size / 1024
        fasta_size = fasta_file.stat().st_size / (1024 * 1024)
        return CheckResult(
            Status.OK, 
            f"Found pam250.bin ({pam_size:.1f} KB), fasta.bin ({fasta_size:.1f} MB)"
        )
    
    def fix():
        if not prepare_script.exists():
            print(f"  Error: {prepare_script} not found")
            return False
        print(f"  Running: python {prepare_script}")
        code, stdout, stderr = run_command([sys.executable, str(prepare_script)])
        print(stdout)
        if code != 0:
            print(f"  Error: {stderr}")
            return False
        return True
    
    return CheckResult(
        Status.MISSING,
        f"Missing: {', '.join(missing)}",
        details="Run: python py/prepare_binary_data.py",
        fixable=prepare_script.exists(),
        fix_action=fix
    )


def check_database() -> CheckResult:
    """Check if database is set up and migrated."""
    # Example: check for SQLite database file or connection
    db_path = PROJECT_ROOT / "data" / "app.db"
    
    if db_path.exists():
        # Could add schema version check here
        return CheckResult(Status.OK, f"Database found ({db_path.stat().st_size / 1024:.1f} KB)")
    
    def fix():
        print("  Initializing database...")
        # Customize this for your migration tool (alembic, etc.)
        code, stdout, stderr = run_command([sys.executable, "-m", "your_package.db", "init"])
        return code == 0
    
    return CheckResult(
        Status.MISSING,
        "Database not found",
        details="Run database initialization",
        fixable=True,
        fix_action=fix
    )


# ============================================================================
# Post-processing checks (after long-running job completes)
# ============================================================================

def check_sw_results() -> CheckResult:
    """Check if the main SW results file exists (from long-running job)."""
    results_file = PROJECT_ROOT / "sw_results" / "sw_results.csv"
    
    if results_file.exists():
        size_mb = results_file.stat().st_size / (1024 * 1024)
        return CheckResult(Status.OK, f"Found ({size_mb:.1f} MB)")
    
    return CheckResult(
        Status.MISSING,
        "Not found (long-running job not complete)",
        details="Run the web server and start the search job"
    )


def check_tree_files() -> CheckResult:
    """Check if tree builder outputs exist."""
    results_dir = PROJECT_ROOT / "sw_results"
    tree_file = results_dir / "sw_tree.txt"
    finds_raw = results_dir / "sw_finds_raw.txt"
    tree_script = PROJECT_ROOT / "py" / "tree_builder.py"
    
    missing = []
    if not tree_file.exists():
        missing.append("sw_tree.txt")
    if not finds_raw.exists():
        missing.append("sw_finds_raw.txt")
    
    if not missing:
        return CheckResult(Status.OK, "Found sw_tree.txt and sw_finds_raw.txt")
    
    def fix():
        if not tree_script.exists():
            print(f"  Error: {tree_script} not found")
            return False
        print(f"  Running: python {tree_script}")
        code, stdout, stderr = run_command([sys.executable, str(tree_script)])
        print(stdout)
        if code != 0:
            print(f"  Error: {stderr}")
            return False
        return True
    
    return CheckResult(
        Status.MISSING,
        f"Missing: {', '.join(missing)}",
        details="Run: python py/tree_builder.py",
        fixable=tree_script.exists(),
        fix_action=fix
    )


def check_filtered_finds() -> CheckResult:
    """Check if filtered finds exist."""
    results_dir = PROJECT_ROOT / "sw_results"
    standard = results_dir / "sw_finds_standard.txt"
    biased = results_dir / "sw_finds_biased.txt"
    filter_script = PROJECT_ROOT / "py" / "filter_twilight.py"
    
    missing = []
    if not standard.exists():
        missing.append("sw_finds_standard.txt")
    if not biased.exists():
        missing.append("sw_finds_biased.txt")
    
    if not missing:
        return CheckResult(Status.OK, "Found sw_finds_standard.txt and sw_finds_biased.txt")
    
    def fix():
        if not filter_script.exists():
            print(f"  Error: {filter_script} not found")
            return False
        print(f"  Running: python {filter_script}")
        code, stdout, stderr = run_command([sys.executable, str(filter_script)])
        print(stdout)
        if code != 0:
            print(f"  Error: {stderr}")
            return False
        return True
    
    return CheckResult(
        Status.MISSING,
        f"Missing: {', '.join(missing)}",
        details="Run: python py/filter_twilight.py",
        fixable=filter_script.exists(),
        fix_action=fix
    )


# ============================================================================
# Post-processing check registry
# ============================================================================

POST_PROCESSING_CHECKS = [
    Check("SW Results", "Main search results (sw_results.csv)", check_sw_results, "results"),
    Check("Tree Builder", "sw_tree.txt and sw_finds_raw.txt", check_tree_files, "results", depends_on="SW Results"),
    Check("Filtered Finds", "sw_finds_standard.txt and sw_finds_biased.txt", check_filtered_finds, "results", depends_on="Tree Builder"),
]


# ============================================================================
# Setup check registry
# ============================================================================

ALL_CHECKS = [
    Check("Python Version", "Python 3.9+ required", check_python_version, "environment"),
    Check("Apple Silicon", "Metal acceleration support", check_apple_silicon, "environment"),
    Check(".env File", "Environment configuration", check_env_file, "configuration", critical=True),
    Check("metal-cpp", "Metal C++ headers", check_metal_cpp, "dependencies"),
    Check("Package Installed", "pip install -e .", check_package_installed, "dependencies"),
    Check("Metal Components", "Compiled C++/Metal code", check_compiled_metal, "compilation", depends_on="metal-cpp"),
    Check("WASM Components", "In-browser alignment", check_compiled_wasm, "compilation"),
    Check("Uniprot Data", "Protein data files", check_uniprot_data, "data"),
    Check("Binary Data", "Prepared pam250.bin and fasta.bin", check_binary_data, "data", depends_on="Uniprot Data"),
    # Check("Database", "Application database", check_database, "data"),
]


# ============================================================================
# Main runner
# ============================================================================

def print_header():
    print()
    print("=" * 60)
    print("  🎸 Ready to Rock? - Environment Checker")
    print("=" * 60)
    print()


def print_result(check: Check, result: CheckResult):
    icons = {
        Status.OK: "✅",
        Status.MISSING: "❌",
        Status.ERROR: "⚠️ ",
        Status.SKIPPED: "⏭️ ",
    }
    icon = icons[result.status]
    print(f"  {icon} {check.name}: {result.message}")
    if result.details and result.status != Status.OK:
        print(f"      └─ {result.details}")


def run_checks(auto_fix: bool = False, interactive_fix: bool = False) -> dict[str, list[tuple[Check, CheckResult]]]:
    """Run all checks and return results grouped by category."""
    results: dict[str, list[tuple[Check, CheckResult]]] = {}
    passed_checks: set[str] = set()  # Track which checks passed (OK or SKIPPED)
    current_category = None
    
    for check in ALL_CHECKS:
        # Print category header when it changes
        if check.category != current_category:
            current_category = check.category
            print(f"\n  [{current_category.upper()}]")
        
        if check.category not in results:
            results[check.category] = []
        
        # Check if dependency failed
        if check.depends_on and check.depends_on not in passed_checks:
            result = CheckResult(
                Status.SKIPPED,
                f"Skipped (needs {check.depends_on})"
            )
            results[check.category].append((check, result))
            print_result(check, result)
            continue
        
        # Run the check
        result = check.check_fn()
        results[check.category].append((check, result))
        
        # Show result immediately
        print_result(check, result)
        
        # Track if check passed (OK or SKIPPED count as "not failed")
        if result.status in (Status.OK, Status.SKIPPED):
            passed_checks.add(check.name)
        
        # Offer to fix if applicable
        if result.status in (Status.MISSING, Status.ERROR) and result.fixable and result.fix_action:
            should_fix = auto_fix or (interactive_fix and prompt_yes_no(f"      Fix '{check.name}'?"))
            if should_fix:
                print()
                success = result.fix_action()
                if success:
                    # Re-check
                    result = check.check_fn()
                    results[check.category][-1] = (check, result)
                    icon = "✅" if result.status == Status.OK else "❌"
                    print(f"      {icon} {'Fixed!' if result.status == Status.OK else 'Still failing'}")
                    if result.status in (Status.OK, Status.SKIPPED):
                        passed_checks.add(check.name)
                else:
                    print("      ❌ Fix failed")
                print()
        
        # Stop if critical check failed
        if check.critical and result.status not in (Status.OK, Status.SKIPPED):
            print()
            print("  ⛔ Critical check failed. Please fix before continuing.")
            break
    
    return results


def print_summary(results: dict[str, list[tuple[Check, CheckResult]]]):
    total_ok = 0
    total_issues = 0
    total_skipped = 0
    
    for category, checks in results.items():
        for check, result in checks:
            if result.status == Status.OK:
                total_ok += 1
            elif result.status == Status.SKIPPED:
                total_skipped += 1
            else:
                total_issues += 1
    
    print()
    print("-" * 60)
    
    if total_issues == 0:
        print("  🎸 You're ready to rock! All checks passed.")
    else:
        print(f"  📊 Results: {total_ok} passed, {total_issues} issues, {total_skipped} skipped")
        print()
        print("  Run with --interactive to ask and attempt to fix")
        print("  Run with --yes to YOLO and agree to all prompts for fixes")
    
    print("-" * 60)
    print()
    
    return total_issues == 0


def run_post_processing_checks(auto_fix: bool = False, interactive_fix: bool = False) -> Optional[dict[str, list[tuple[Check, CheckResult]]]]:
    """Run post-processing checks if the long-running job has completed."""
    results_file = PROJECT_ROOT / "sw_results" / "sw_results.csv"
    
    if not results_file.exists():
        return None
    
    print("\n" + "=" * 60)
    print("  📊 Post-Processing Checks (search job completed)")
    print("=" * 60)
    
    results: dict[str, list[tuple[Check, CheckResult]]] = {}
    passed_checks: set[str] = set()
    current_category = None
    
    for check in POST_PROCESSING_CHECKS:
        if check.category != current_category:
            current_category = check.category
            print(f"\n  [{current_category.upper()}]")
        
        if check.category not in results:
            results[check.category] = []
        
        # Check if dependency failed
        if check.depends_on and check.depends_on not in passed_checks:
            result = CheckResult(
                Status.SKIPPED,
                f"Skipped (needs {check.depends_on})"
            )
            results[check.category].append((check, result))
            print_result(check, result)
            continue
        
        result = check.check_fn()
        results[check.category].append((check, result))
        print_result(check, result)
        
        if result.status in (Status.OK, Status.SKIPPED):
            passed_checks.add(check.name)
        
        # Offer to fix if applicable
        if result.status in (Status.MISSING, Status.ERROR) and result.fixable and result.fix_action:
            should_fix = auto_fix or (interactive_fix and prompt_yes_no(f"      Fix '{check.name}'?"))
            if should_fix:
                print()
                success = result.fix_action()
                if success:
                    result = check.check_fn()
                    results[check.category][-1] = (check, result)
                    icon = "✅" if result.status == Status.OK else "❌"
                    print(f"      {icon} {'Fixed!' if result.status == Status.OK else 'Still failing'}")
                    if result.status in (Status.OK, Status.SKIPPED):
                        passed_checks.add(check.name)
                else:
                    print("      ❌ Fix failed")
                print()
    
    return results


def print_post_summary(results: dict[str, list[tuple[Check, CheckResult]]]) -> bool:
    total_ok = 0
    total_issues = 0
    
    for category, checks in results.items():
        for check, result in checks:
            if result.status == Status.OK:
                total_ok += 1
            elif result.status != Status.SKIPPED:
                total_issues += 1
    
    print()
    print("-" * 60)
    
    if total_issues == 0:
        print("  🔬 Analysis complete! Results ready for review in the web UI.")
    else:
        print(f"  📊 Post-processing: {total_ok} passed, {total_issues} need attention")
        print()
        print("  Run with --fix to attempt automatic fixes")
    
    print("-" * 60)
    print()
    
    return total_issues == 0


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Check if environment is ready to rock")
    parser.add_argument("--interactive", action="store_true", help="Prompt to fix issues")
    parser.add_argument("--yes", action="store_true", help="Agree to all proposed fixes")
    parser.add_argument("--quiet", "-q", action="store_true", help="Only show issues")
    args = parser.parse_args()
    
    print_header()
    
    if args.yes:
        print("  Running in auto-fix (--yes) mode...")
    elif args.interactive:
        print("  Running in interactive fix mode...")
    
    results = run_checks(auto_fix=args.yes, interactive_fix=args.interactive)
    ready = print_summary(results)
    
    if not ready:
        sys.exit(1)
    
    # If setup is ready, check for post-processing
    post_results = run_post_processing_checks(auto_fix=args.yes, interactive_fix=args.interactive)
    
    if post_results is not None:
        post_ready = print_post_summary(post_results)
        sys.exit(0 if post_ready else 1)
    
    sys.exit(0)


if __name__ == "__main__":
    main()