"""
benchmarks/run_full_benchmark.py
=================================
Runs each RLM-style benchmark family independently and accumulates results
into a single CSV. Designed to be resilient to timeouts — each family writes
its own partial CSV, and results are merged at the end.

Usage:
  python benchmarks/run_full_benchmark.py --output benchmark_results/
"""
from __future__ import annotations

import csv
import subprocess
import sys
import tempfile
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
_BENCH = _ROOT / "benchmarks"
_EVAL = _BENCH / "rlm_style_waggle_eval.py"
_PYTHON = sys.executable

FAMILIES = ["sniah", "multihop", "pairwise", "codeqa", "linear_agg"]
SCALES = [128, 512, 2048]
METHODS = ["raw_context", "query_graph", "build_context"]
TOKEN_BUDGET = 1200
SEED = 42

# Per-family timeout in seconds (linear_agg is slow at large scale)
FAMILY_TIMEOUTS = {
    "sniah": 60,
    "multihop": 60,
    "pairwise": 60,
    "codeqa": 90,
    "linear_agg": 120,
}


def run_family(family: str, scales: list[int], output_dir: Path) -> Path | None:
    """Run one family and return path to its partial CSV, or None on failure."""
    partial_dir = output_dir / "partial"
    partial_dir.mkdir(parents=True, exist_ok=True)
    partial_out = partial_dir / f"{family}.csv"

    # Remove stale partial
    if partial_out.exists():
        partial_out.unlink()

    cmd = [
        _PYTHON, str(_EVAL),
        "--db", f"/tmp/waggle_rlm_{family}",
        "--scales", *[str(s) for s in scales],
        "--methods", *METHODS,
        "--families", family,
        "--token-budget", str(TOKEN_BUDGET),
        "--seed", str(SEED),
        "--output", str(partial_dir / family),
    ]

    timeout = FAMILY_TIMEOUTS.get(family, 90)
    print(f"  Running {family} (timeout={timeout}s)...", end=" ", flush=True)

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=str(_ROOT),
        )
        if result.returncode != 0:
            print(f"FAILED (exit {result.returncode})")
            if result.stderr:
                print(f"    stderr: {result.stderr[-300:]}")
            return None

        # The benchmark writes to output/rlm_style_waggle_results.csv
        written = partial_dir / family / "rlm_style_waggle_results.csv"
        if written.exists():
            print(f"OK ({written.stat().st_size} bytes)")
            return written
        else:
            print("FAILED (no output file)")
            return None

    except subprocess.TimeoutExpired:
        print(f"TIMEOUT after {timeout}s")
        return None
    except Exception as exc:
        print(f"ERROR: {exc}")
        return None


def merge_csvs(partial_paths: list[Path], output_path: Path) -> int:
    """Merge multiple partial CSVs into one, deduplicating by (family, scale, method)."""
    all_rows: list[dict] = []
    seen: set[tuple] = set()
    fieldnames: list[str] = []

    for path in partial_paths:
        if not path or not path.exists():
            continue
        with open(path, newline="") as f:
            reader = csv.DictReader(f)
            if not fieldnames and reader.fieldnames:
                fieldnames = list(reader.fieldnames)
            for row in reader:
                key = (row["benchmark_family"], row["scale_n"], row["method"])
                if key not in seen:
                    seen.add(key)
                    all_rows.append(row)

    if not all_rows or not fieldnames:
        return 0

    # Sort for readability
    all_rows.sort(key=lambda r: (r["benchmark_family"], int(r["scale_n"]), r["method"]))

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(all_rows)

    return len(all_rows)


def main() -> int:
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", default="benchmark_results")
    parser.add_argument("--scales", nargs="+", type=int, default=SCALES)
    parser.add_argument("--families", nargs="+", default=FAMILIES)
    args = parser.parse_args()

    out = Path(args.output)
    print(f"Running RLM-style benchmark suite")
    print(f"  families: {args.families}")
    print(f"  scales:   {args.scales}")
    print(f"  output:   {out}")
    print()

    partial_paths: list[Path | None] = []
    for family in args.families:
        path = run_family(family, args.scales, out)
        partial_paths.append(path)

    # Merge all partials
    valid_paths = [p for p in partial_paths if p is not None]
    merged_csv = out / "rlm_style_waggle_results.csv"
    n = merge_csvs(valid_paths, merged_csv)
    print(f"\nMerged {n} rows into {merged_csv}")

    # Regenerate markdown and JSON from merged CSV
    if n > 0:
        cmd = [
            _PYTHON, str(_EVAL),
            "--db", "/tmp/waggle_rlm_noop",
            "--scales", "1",
            "--methods", "raw_context",
            "--families", "sniah",
            "--token-budget", "1",
            "--seed", "42",
            "--output", str(out),
            "--append",
        ]
        # Actually just call write_results directly
        sys.path.insert(0, str(_ROOT / "src"))
        sys.path.insert(0, str(_BENCH))
        from rlm_style_waggle_eval import BenchResult, write_results
        import csv as _csv

        rows: list[BenchResult] = []
        with open(merged_csv, newline="") as f:
            for row in _csv.DictReader(f):
                rows.append(BenchResult(
                    benchmark_family=row["benchmark_family"],
                    scale_n=int(row["scale_n"]),
                    method=row["method"],
                    score=float(row["score"]),
                    exact_match=float(row["exact_match"]),
                    f1=float(row["f1"]),
                    evidence_coverage=float(row["evidence_coverage"]),
                    tokens_returned=int(row["tokens_returned"]),
                    latency_ms=float(row["latency_ms"]),
                    context_pack_tokens=int(row["context_pack_tokens"]),
                    notes=row.get("notes", ""),
                ))

        paths = write_results(rows, str(out))
        print(f"Results written:")
        for fmt, p in paths.items():
            print(f"  {fmt}: {p}")

    return 0 if n > 0 else 1


if __name__ == "__main__":
    sys.exit(main())
