from __future__ import annotations

import subprocess
import sys
from pathlib import Path
from zipfile import ZipFile


def _run_step(step_name: str, command: list[str]) -> None:
    print(f"\n==> {step_name}")
    print(" ".join(command))
    subprocess.run(command, check=True)


def _assert_build_artifacts(dist_dir: Path) -> Path:
    if not dist_dir.exists():
        raise RuntimeError("Build output directory 'dist/' was not created.")

    wheels = sorted(dist_dir.glob("*.whl"))
    source_dists = sorted(dist_dir.glob("*.tar.gz"))

    if not wheels:
        raise RuntimeError("No wheel artifact (*.whl) found in dist/.")
    if not source_dists:
        raise RuntimeError("No source distribution artifact (*.tar.gz) found in dist/.")

    print(f"Found {len(wheels)} wheel artifact(s) and {len(source_dists)} source distribution(s).")
    return wheels[-1]


def _assert_wheel_contents(wheel_path: Path) -> None:
    with ZipFile(wheel_path) as wheel_archive:
        names = wheel_archive.namelist()

    has_engine_package = any(name.startswith("axiomatic_engine/") for name in names)
    banned_paths = [
        name
        for name in names
        if name.startswith("tests/") or name.startswith("scripts/")
    ]

    if not has_engine_package:
        raise RuntimeError(
            "Built wheel does not include the expected 'axiomatic_engine' package."
        )
    if banned_paths:
        sample = ", ".join(banned_paths[:5])
        raise RuntimeError(
            "Built wheel contains excluded paths (tests/scripts). "
            f"Examples: {sample}"
        )

    print("Wheel content check passed: package present and excluded paths absent.")


def main() -> int:
    repo_root = Path(__file__).resolve().parents[1]
    dist_dir = repo_root / "dist"

    _run_step("Run unit tests", [sys.executable, "-m", "pytest"])
    _run_step("Build package distributions", [sys.executable, "-m", "build"])
    _run_step("Validate distribution metadata", [sys.executable, "-m", "twine", "check", "dist/*"])

    built_wheel = _assert_build_artifacts(dist_dir=dist_dir)
    _assert_wheel_contents(wheel_path=built_wheel)

    print("\nQuality gate passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
