#!/usr/bin/env uv run

import argparse
import subprocess
import sys
from pathlib import Path


def run_vulture(src_dir: Path):
    """Statically scans an entire directory for dead/unused code."""
    print(f"\n🔍 PHASE 1: Dead Code Analysis (Scanning: {src_dir})")
    print("─" * 55)
    try:
        subprocess.run(
            [sys.executable, "-m", "vulture", str(src_dir)], check=False, text=True
        )
    except Exception as e:
        print(f"⚠️ Vulture failed: {e}")


def run_tracing(entry_point: Path, output_file: Path):
    """Traces line-by-line execution of the entry point."""
    print(f"\n🛤️ PHASE 2: Execution Tracing (Running: {entry_point.name})")
    print("─" * 55)
    print("Tracing execution... (This may take a while due to overhead)")

    with open(output_file, "w", encoding="utf-8") as f:
        try:
            subprocess.run(
                [sys.executable, "-m", "trace", "--trace", str(entry_point)],
                stdout=f,
                stderr=subprocess.STDOUT,
                check=True,
            )
            print(f"✅ Trace saved to: {output_file}")
        except subprocess.CalledProcessError:
            print("⚠️ Target script exited with an error during tracing.")
        except Exception as e:
            print(f"💥 Tracing failed: {e}")


def run_profiling(entry_point: Path, output_file: Path):
    """Generates a machine-readable JSON profile/flame chart."""
    print(f"\n🔥 PHASE 3: Profiling & Flame Chart (Running: {entry_point.name})")
    print("─" * 55)

    try:
        subprocess.run(
            [
                sys.executable,
                "-m",
                "pyinstrument",
                "--renderer",
                "json",
                "-o",
                str(output_file),
                str(entry_point),
            ],
            check=False,
        )
        print(f"✅ Machine-readable profile saved to: {output_file}")
        print(
            "   (Upload this JSON to https://www.speedscope.app/ to view the flame graph)"
        )
    except Exception as e:
        print(f"💥 Profiling failed: {e}")


def main():
    parser = argparse.ArgumentParser(
        description="Analyze a Python package and profile its execution."
    )
    parser.add_argument(
        "--entry",
        type=str,
        default="src/app.py",
        help="The entry point script to run (e.g., src/app.py)",
    )
    parser.add_argument(
        "--src",
        type=str,
        default="src",
        help="The source directory to scan for dead code (default: 'src')",
    )
    args = parser.parse_args()

    entry_path = Path(args.entry)
    src_path = Path(args.src)

    if not entry_path.exists() or not entry_path.is_file():
        print(f"❌ Error: Entry point '{args.entry}' does not exist.")
        sys.exit(1)

    if not src_path.exists() or not src_path.is_dir():
        print(f"❌ Error: Source directory '{args.src}' does not exist.")
        sys.exit(1)

    reports_dir = Path.cwd() / "reports"
    reports_dir.mkdir(parents=True, exist_ok=True)

    profile_out = reports_dir / "profile.json"

    # Run the suite
    run_vulture(src_path)
    # Uncomment to emit a full trace log into reports/execution_trace.log.
    # run_tracing(entry_path, reports_dir / "execution_trace.log")
    run_profiling(entry_path, profile_out)

    print("\n✨ Analysis Complete!")


if __name__ == "__main__":
    main()
