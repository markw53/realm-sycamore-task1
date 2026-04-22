"""Deterministic verifier for Realm Sycamore translation tasks."""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any, Dict, List, Optional

ROOT = Path(__file__).resolve().parents[1]
GOLDEN_REPO = ROOT / "golden_repo"
BEHAVIORAL_TESTS = ROOT / "behavioral_tests"
TASK_CONFIG = ROOT / "submission" / "task_config.json"
IGNORE_PATTERNS = shutil.ignore_patterns(
    ".git", ".pytest_cache", "__pycache__", ".DS_Store", "node_modules", "dist"
)


def _load_config() -> Dict[str, Any]:
    with TASK_CONFIG.open() as fh:
        return json.load(fh)


def _copy_dir(src: Path, dst: Path) -> None:
    if dst.exists():
        shutil.rmtree(dst)
    shutil.copytree(src, dst, ignore=IGNORE_PATTERNS)


def _inject_tests(repo_root: Path) -> None:
    """Copy behavioral test files into the translated repo's tests/ directory."""
    tests_dir = repo_root / "tests"
    tests_dir.mkdir(exist_ok=True)
    for test_file in BEHAVIORAL_TESTS.glob("test_*.py"):
        shutil.copy2(test_file, tests_dir / test_file.name)


def _run_npm_install(repo_root: Path) -> Dict[str, Any]:
    """Install Node.js dependencies."""
    process = subprocess.run(
        ["npm", "install"],
        cwd=repo_root,
        capture_output=True,
        text=True,
        timeout=120,
    )
    return {
        "command": "npm install",
        "returncode": process.returncode,
        "stdout": process.stdout.strip(),
        "stderr": process.stderr.strip(),
    }


def _run_build(repo_root: Path) -> Dict[str, Any]:
    """Compile TypeScript to JavaScript."""
    process = subprocess.run(
        ["npx", "tsc"],
        cwd=repo_root,
        capture_output=True,
        text=True,
        timeout=120,
    )
    return {
        "command": "npx tsc",
        "returncode": process.returncode,
        "stdout": process.stdout.strip(),
        "stderr": process.stderr.strip(),
    }


def _run_tests(repo_root: Path) -> Dict[str, Any]:
    """Run pytest behavioral tests against the compiled TypeScript."""
    process = subprocess.run(
        ["python", "-m", "pytest", "tests/", "-v", "--tb=short"],
        cwd=repo_root,
        capture_output=True,
        text=True,
        timeout=300,
    )

    # Parse pytest output
    passed = 0
    failed = 0
    errors = 0
    for line in process.stdout.split("\n"):
        if " PASSED" in line:
            passed += 1
        elif " FAILED" in line:
            failed += 1
        elif " ERROR" in line:
            errors += 1

    # Also check the summary line (e.g., "84 passed, 0 failed")
    for line in process.stdout.split("\n"):
        line = line.strip()
        if "passed" in line and ("failed" in line or "error" in line or line.startswith("=")):
            # This is the pytest summary line
            break

    return {
        "command": "python -m pytest tests/ -v --tb=short",
        "returncode": process.returncode,
        "stdout": process.stdout.strip(),
        "stderr": process.stderr.strip(),
        "passed": passed,
        "failed": failed,
        "errors": errors,
    }


def _evaluate_golden() -> Dict[str, Any]:
    """Evaluate the golden translation."""
    tempdir = tempfile.TemporaryDirectory()
    try:
        workspace = Path(tempdir.name) / "repo"
        _copy_dir(GOLDEN_REPO, workspace)

        # Install dependencies
        install_result = _run_npm_install(workspace)
        if install_result["returncode"] != 0:
            return {
                "install": install_result,
                "build": None,
                "tests": None,
                "passed": False,
                "reason": "npm install failed",
            }

        # Compile TypeScript
        build_result = _run_build(workspace)
        if build_result["returncode"] != 0:
            return {
                "install": install_result,
                "build": build_result,
                "tests": None,
                "passed": False,
                "reason": "tsc compilation failed",
            }

        # Verify dist/ was created
        if not (workspace / "dist").exists():
            return {
                "install": install_result,
                "build": build_result,
                "tests": None,
                "passed": False,
                "reason": "dist/ directory not created after tsc",
            }

        # Inject and run behavioral tests
        _inject_tests(workspace)
        test_result = _run_tests(workspace)

        config = _load_config()
        expected = config.get("scoring", {}).get("expected_test_count", 0)

        return {
            "install": install_result,
            "build": build_result,
            "tests": test_result,
            "passed": (
                test_result["returncode"] == 0
                and test_result["failed"] == 0
                and test_result["errors"] == 0
                and test_result["passed"] == expected
            ),
            "expected_tests": expected,
            "actual_passed": test_result["passed"],
        }
    finally:
        tempdir.cleanup()


def _evaluate_submission(submission_path: Path) -> Dict[str, Any]:
    """Evaluate an agent's translated repository."""
    tempdir = tempfile.TemporaryDirectory()
    try:
        workspace = Path(tempdir.name) / "repo"
        _copy_dir(submission_path, workspace)

        # Gate check: package.json must exist
        if not (workspace / "package.json").exists():
            return {
                "install": None,
                "build": None,
                "tests": None,
                "passed": False,
                "reason": "package.json not found",
            }

        # Gate check: tsconfig.json must exist
        if not (workspace / "tsconfig.json").exists():
            return {
                "install": None,
                "build": None,
                "tests": None,
                "passed": False,
                "reason": "tsconfig.json not found",
            }

        # Gate check: src/ directory must exist
        if not (workspace / "src").is_dir():
            return {
                "install": None,
                "build": None,
                "tests": None,
                "passed": False,
                "reason": "src/ directory not found",
            }

        # Install dependencies
        install_result = _run_npm_install(workspace)
        if install_result["returncode"] != 0:
            return {
                "install": install_result,
                "build": None,
                "tests": None,
                "passed": False,
                "reason": "npm install failed",
            }

        # Compile TypeScript
        build_result = _run_build(workspace)
        if build_result["returncode"] != 0:
            return {
                "install": install_result,
                "build": build_result,
                "tests": None,
                "passed": False,
                "reason": "tsc compilation failed",
            }

        # Verify dist/ was created
        if not (workspace / "dist").exists():
            return {
                "install": install_result,
                "build": build_result,
                "tests": None,
                "passed": False,
                "reason": "dist/ directory not created after tsc",
            }

        # Logic stripping check: verify src/ has substantive content
        ts_files = list((workspace / "src").rglob("*.ts"))
        if len(ts_files) < 10:
            return {
                "install": install_result,
                "build": build_result,
                "tests": None,
                "passed": False,
                "reason": f"Insufficient source files: found {len(ts_files)} .ts files, expected >= 10",
            }

        # Check for stub/empty files (Gate B: no logic stripping)
        empty_files = []
        for ts_file in ts_files:
            content = ts_file.read_text().strip()
            # Exclude files that are just imports/exports with no logic
            lines = [
                l.strip()
                for l in content.split("\n")
                if l.strip()
                and not l.strip().startswith("//")
                and not l.strip().startswith("import")
                and not l.strip().startswith("export")
            ]
            if len(lines) < 3:
                empty_files.append(str(ts_file.relative_to(workspace)))

        if len(empty_files) > 3:
            return {
                "install": install_result,
                "build": build_result,
                "tests": None,
                "passed": False,
                "reason": f"Possible logic stripping: {len(empty_files)} near-empty files: {empty_files[:5]}",
            }

        # Inject and run behavioral tests
        _inject_tests(workspace)
        test_result = _run_tests(workspace)

        config = _load_config()
        expected = config.get("scoring", {}).get("expected_test_count", 0)

        return {
            "install": install_result,
            "build": build_result,
            "tests": test_result,
            "passed": (
                test_result["returncode"] == 0
                and test_result["failed"] == 0
                and test_result["errors"] == 0
                and test_result["passed"] == expected
            ),
            "expected_tests": expected,
            "actual_passed": test_result["passed"],
            "source_files": len(ts_files),
        }
    finally:
        tempdir.cleanup()


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        description="Grade a Realm Sycamore translation task (Python → TypeScript)."
    )
    parser.add_argument(
        "--mode",
        choices=("golden", "submission", "both"),
        default="golden",
        help="What to evaluate: golden translation, a submission, or both.",
    )
    parser.add_argument(
        "--submission",
        type=str,
        default=None,
        help="Path to the agent's translated repository (required for submission/both modes).",
    )
    args = parser.parse_args(argv)

    results: Dict[str, Any] = {"mode": args.mode}
    overall_pass = True

    if args.mode in {"golden", "both"}:
        print("=" * 60)
        print("Evaluating golden translation...")
        print("=" * 60)
        golden_result = _evaluate_golden()
        results["golden"] = golden_result
        overall_pass = overall_pass and golden_result["passed"]

        if golden_result["passed"]:
            print(
                f"✓ Golden: PASSED ({golden_result.get('actual_passed', '?')}"
                f"/{golden_result.get('expected_tests', '?')} tests)"
            )
        else:
            print(f"✗ Golden: FAILED — {golden_result.get('reason', 'unknown')}")
            if golden_result.get("tests"):
                print(
                    f"  Tests: {golden_result['tests']['passed']} passed,"
                    f" {golden_result['tests']['failed']} failed,"
                    f" {golden_result['tests']['errors']} errors"
                )

    if args.mode in {"submission", "both"}:
        if not args.submission:
            print(
                "Error: --submission path required for submission/both modes",
                file=sys.stderr,
            )
            return 1
        submission_path = Path(args.submission)
        if not submission_path.exists():
            print(f"Error: submission path not found: {submission_path}", file=sys.stderr)
            return 1

        print("=" * 60)
        print(f"Evaluating submission: {submission_path}")
        print("=" * 60)
        submission_result = _evaluate_submission(submission_path)
        results["submission"] = submission_result
        overall_pass = overall_pass and submission_result["passed"]

        if submission_result["passed"]:
            print(
                f"✓ Submission: PASSED ({submission_result.get('actual_passed', '?')}"
                f"/{submission_result.get('expected_tests', '?')} tests)"
            )
        else:
            print(f"✗ Submission: FAILED — {submission_result.get('reason', 'unknown')}")
            if submission_result.get("tests"):
                print(
                    f"  Tests: {submission_result['tests']['passed']} passed,"
                    f" {submission_result['tests']['failed']} failed,"
                    f" {submission_result['tests']['errors']} errors"
                )

    print()
    print(json.dumps(results, indent=2))
    return 0 if overall_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())