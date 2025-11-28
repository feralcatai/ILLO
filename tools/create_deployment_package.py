"""
CircuitPython Deployment Package Builder

Creates a ZIP file containing only the files needed to deploy ILLO to a Circuit Playground Bluefruit.
This package includes all Python files, libraries, configuration, and college data.

Usage:
    python tools/create_deployment_package.py
    python tools/create_deployment_package.py --output dist/illo-deploy.zip
    python tools/create_deployment_package.py --version 2.0.1
"""

import os
import sys
import zipfile
import shutil
import argparse
import re
from pathlib import Path


def get_version_from_project():
    """Extract version from project.toml or code.py"""
    project_root = Path(__file__).parent.parent

    # Try to read from project.toml first (simple regex parsing)
    toml_path = project_root / "project.toml"
    if toml_path.exists():
        try:
            with open(toml_path, 'r') as f:
                content = f.read()
                match = re.search(r'version\s*=\s*"([^"]+)"', content)
                if match:
                    return match.group(1)
        except Exception as e:
            print(f"Warning: Could not read version from project.toml: {e}")

    # Fallback to code.py
    code_path = project_root / "code.py"
    if code_path.exists():
        try:
            with open(code_path, 'r') as f:
                content = f.read()
                match = re.search(r'VERSION\s*=\s*["\']([^"\']+)["\']', content)
                if match:
                    return match.group(1)
        except Exception as e:
            print(f"Warning: Could not read version from code.py: {e}")

    return "0.0.0"


def create_deployment_package(output_path=None, version=None):
    """
    Create a deployment ZIP file with all necessary CircuitPython files.

    Args:
        output_path: Optional custom output path for the ZIP file
        version: Optional version string (defaults to reading from project.toml)
    """
    # Get project root (parent of tools directory)
    script_dir = Path(__file__).parent
    project_root = script_dir.parent

    # Get version
    if version is None:
        version = get_version_from_project()

    # Default output path
    if output_path is None:
        output_dir = project_root / "dist"
        output_dir.mkdir(exist_ok=True)
        output_path = output_dir / f"ILLO-CircuitPython-v{version}.zip"
    else:
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

    print(f"Creating ILLO deployment package v{version}...")
    print(f"Output: {output_path}")

    # Files to include (relative to project root)
    files_to_include = [
        # Main entry points
        "code.py",
        "boot.py",
        "config.json",

        # Core system files
        "base_routine.py",
        "config_manager.py",
        "memory_manager.py",
        "interaction_manager.py",
        "light_manager.py",
        "hardware_manager.py",
        "color_utils.py",

        # Routine files
        "ufo_intelligence.py",
        "intergalactic_cruising.py",
        "meditate.py",
        "dance_party.py",

        # UFO AI subsystems
        "ufo_ai_core.py",
        "ufo_ai_behaviors.py",
        "ufo_learning.py",
        "ufo_memory_manager.py",
        "ufo_college_system.py",

        # Audio and BLE
        "audio_processor.py",
        "music_player.py",
        "bluetooth_controller.py",
        "sync_manager.py",
        "chant_detector.py",

        # Utilities
        "physical_actions.py",
        "college_manager.py",
    ]

    # Directories to include recursively
    dirs_to_include = [
        "lib",        # CircuitPython libraries
        "colleges",   # College configuration files
    ]

    # Create the ZIP file
    with zipfile.ZipFile(output_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        # Add individual files
        for file_path in files_to_include:
            full_path = project_root / file_path
            if full_path.exists():
                zipf.write(full_path, file_path)
                print(f"  Added: {file_path}")
            else:
                print(f"  Warning: {file_path} not found, skipping")

        # Add directories recursively
        for dir_name in dirs_to_include:
            dir_path = project_root / dir_name
            if dir_path.exists() and dir_path.is_dir():
                for root, dirs, files in os.walk(dir_path):
                    # Skip __pycache__ and other unwanted directories
                    dirs[:] = [d for d in dirs if d not in ['__pycache__', '.git', '.idea']]

                    for file in files:
                        # Skip .pyc files and other build artifacts
                        if file.endswith(('.pyc', '.pyo', '.DS_Store')):
                            continue

                        file_full_path = Path(root) / file
                        arcname = file_full_path.relative_to(project_root)
                        zipf.write(file_full_path, arcname)
                        print(f"  Added: {arcname}")
            else:
                print(f"  Warning: {dir_name}/ not found, skipping")

        # Add README for deployment
        readme_content = f"""ILLO CircuitPython Deployment Package v{version}
===============================================

This package contains all files needed to deploy ILLO to your Circuit Playground Bluefruit.

INSTALLATION INSTRUCTIONS:
--------------------------

1. Connect your Circuit Playground Bluefruit to your computer via USB
2. It should appear as a drive named "CIRCUITPY"
3. Extract all files from this ZIP to the root of the CIRCUITPY drive
   - On Windows: Right-click the ZIP, select "Extract All", choose CIRCUITPY drive
   - On Mac: Double-click ZIP, drag all files to CIRCUITPY drive
   - On Linux: Extract and copy all files to the mount point

4. The device will automatically restart and run the new code

WHAT'S INCLUDED:
----------------
- code.py & boot.py (main entry points)
- config.json (default configuration)
- All routine Python files (UFO Intelligence, Cruising, Meditate, Dance Party)
- lib/ directory (CircuitPython libraries)
- colleges/ directory (college spirit configurations)

CONFIGURATION:
--------------
Edit config.json to customize:
- routine: 1=UFO Intelligence, 2=Cruising, 3=Meditate, 4=Dance Party
- mode: 1-4 (varies by routine)
- college: "penn_state" or other supported colleges
- bluetooth_enabled: true/false
- And more...

For complete documentation, visit:
https://feralcatai.github.io/ILLO/

TROUBLESHOOTING:
----------------
If the device doesn't start:
1. Check that CIRCUITPY drive is writable (disconnect USB, reconnect)
2. Verify CircuitPython firmware is 9.0.4 or newer
3. Check serial output for error messages

For support, visit: https://github.com/feralcatai/ILLO/issues
"""

        zipf.writestr("DEPLOYMENT_README.txt", readme_content)
        print("  Added: DEPLOYMENT_README.txt")

    # Get file size
    size_mb = output_path.stat().st_size / (1024 * 1024)
    print(f"\n[SUCCESS] Deployment package created successfully!")
    print(f"  Size: {size_mb:.2f} MB")
    print(f"  Location: {output_path}")
    print(f"\nTo deploy to Circuit Playground:")
    print(f"  1. Extract {output_path.name}")
    print(f"  2. Copy all files to CIRCUITPY drive")
    print(f"  3. Device will restart automatically")

    return output_path


def main():
    parser = argparse.ArgumentParser(
        description="Create ILLO CircuitPython deployment package",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python tools/create_deployment_package.py
  python tools/create_deployment_package.py --output releases/illo.zip
  python tools/create_deployment_package.py --version 2.1.0
        """
    )

    parser.add_argument(
        '--output', '-o',
        help='Output path for the ZIP file (default: dist/ILLO-CircuitPython-vX.X.X.zip)'
    )

    parser.add_argument(
        '--version', '-v',
        help='Version string (default: read from project.toml)'
    )

    args = parser.parse_args()

    try:
        create_deployment_package(output_path=args.output, version=args.version)
        return 0
    except Exception as e:
        print(f"\n[ERROR] Error creating deployment package: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
