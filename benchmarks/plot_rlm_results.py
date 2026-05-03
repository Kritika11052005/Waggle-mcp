"""
benchmarks/plot_rlm_results.py
================================
Generate Score-vs-Scale and Tokens-vs-Scale charts from the RLM-style
Waggle benchmark results CSV.

Produces:
  benchmark_results/charts/score_vs_scale_{family}.png
  benchmark_results/charts/tokens_vs_scale_{family}.png
  benchmark_results/charts/score_vs_scale_all.png
  benchmark_results/charts/tokens_vs_scale_all.png
  benchmark_results/charts/token_reduction_vs_scale.png

Usage:
  python benchmarks/plot_rlm_results.py \\
    --input benchmark_results/rlm_style_waggle_results.csv \\
    --output benchmark_results/charts/
"""
from __future__ import annotations

import argparse
import csv
import sys
from collections import defaultdict
from pathlib import Path

# ---------------------------------------------------------------------------
# Path bootstrap
# ---------------------------------------------------------------------------
_ROOT = Path(__file__).resolve().parent.parent
_SRC = _ROOT / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

try:
    import matplotlib
    matplotlib.use("Agg")  # non-interactive backend
    import matplotlib.pyplot as plt
    import matplotlib.ticker as mticker
    import numpy as np
    HAS_MPL = True
except ImportError:
    HAS_MPL = False

# ---------------------------------------------------------------------------
# Colour / style constants
# ---------------------------------------------------------------------------
METHOD_COLORS = {
    "raw_context":    "#e05c5c",   # red
    "query_graph":    "#5c8ee0",   # blue
    "prime_context":  "#e0a85c",   # orange
    "build_context":  "#3dba6e",   # green
    "hybrid_baseline":"#9b5ce0",   # purple
}
METHOD_MARKERS = {
    "raw_context":    "o",
    "query_graph":    "s",
    "prime_context":  "^",
    "build_context":  "D",
    "hybrid_baseline":"P",
}
METHOD_LABELS = {
    "raw_context":    "Raw context dump",
    "query_graph":    "query_graph (single)",
    "prime_context":  "prime_context",
    "build_context":  "build_context (recursive)",
    "hybrid_baseline":"Hybrid baseline",
}

FAMILY_TITLES = {
    "S-NIAH-style":           "S-NIAH-style\n(needle retrieval, O(1))",
    "BrowseComp-Plus-style":  "BrowseComp-Plus-style\n(multi-hop QA)",
    "OOLONG-style":           "OOLONG-style\n(linear aggregation, O(n))",
    "OOLONG-Pairs-style":     "OOLONG-Pairs-style\n(pairwise conflict, O(n²))",
    "CodeQA-style":           "CodeQA-style\n(codebase understanding)",
}

SCORE_METRIC_LABEL = {
    "S-NIAH-style":           "Score (contains_answer)",
    "BrowseComp-Plus-style":  "Score (exact_match)",
    "OOLONG-style":           "F1 (blocked task IDs)",
    "OOLONG-Pairs-style":     "Pairwise F1 (conflict pairs)",
    "CodeQA-style":           "Score (exact_match)",
}

# ---------------------------------------------------------------------------
# Data loading
# ---------------------------------------------------------------------------


def load_csv(path: str) -> list[dict]:
    with open(path, newline="") as f:
        return list(csv.DictReader(f))


def pivot(rows: list[dict]) -> dict:
    """
    Returns nested dict:
      data[family][method][scale] = {score, f1, tokens_returned, latency_ms, ...}
    """
    data: dict = defaultdict(lambda: defaultdict(dict))
    for row in rows:
        fam = row["benchmark_family"]
        method = row["method"]
        scale = int(row["scale_n"])
        data[fam][method][scale] = {
            "score":            float(row["score"]),
            "f1":               float(row["f1"]),
            "tokens_returned":  int(row["tokens_returned"]),
            "latency_ms":       float(row["latency_ms"]),
            "evidence_coverage":float(row["evidence_coverage"]),
        }
    return data


# ---------------------------------------------------------------------------
# Chart helpers
# ---------------------------------------------------------------------------


def _sorted_scales(method_data: dict) -> list[int]:
    scales: set[int] = set()
    for method_scales in method_data.values():
        scales.update(method_scales.keys())
    return sorted(scales)


def _methods_present(method_data: dict, preferred_order: list[str]) -> list[str]:
    present = set(method_data.keys())
    return [m for m in preferred_order if m in present] + [m for m in present if m not in preferred_order]


_METHOD_ORDER = ["raw_context", "query_graph", "prime_context", "build_context", "hybrid_baseline"]


def _apply_style(ax, title: str, xlabel: str, ylabel: str, scales: list[int]) -> None:
    ax.set_title(title, fontsize=11, fontweight="bold", pad=8)
    ax.set_xlabel(xlabel, fontsize=9)
    ax.set_ylabel(ylabel, fontsize=9)
    ax.set_xticks(scales)
    ax.set_xticklabels([str(s) for s in scales], fontsize=8)
    ax.tick_params(axis="y", labelsize=8)
    ax.grid(axis="y", linestyle="--", alpha=0.4)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.legend(fontsize=8, framealpha=0.7)


# ---------------------------------------------------------------------------
# Per-family charts
# ---------------------------------------------------------------------------


def plot_score_vs_scale(
    family: str,
    method_data: dict,
    output_dir: Path,
    score_key: str = "score",
) -> Path:
    scales = _sorted_scales(method_data)
    methods = _methods_present(method_data, _METHOD_ORDER)

    fig, ax = plt.subplots(figsize=(6, 4))
    for method in methods:
        ys = [method_data[method].get(s, {}).get(score_key, float("nan")) for s in scales]
        ax.plot(
            scales, ys,
            marker=METHOD_MARKERS.get(method, "o"),
            color=METHOD_COLORS.get(method, "#888"),
            label=METHOD_LABELS.get(method, method),
            linewidth=2,
            markersize=7,
        )

    ax.set_ylim(-0.05, 1.10)
    ax.yaxis.set_major_formatter(mticker.PercentFormatter(xmax=1.0))
    title = FAMILY_TITLES.get(family, family)
    ylabel = SCORE_METRIC_LABEL.get(family, "Score")
    _apply_style(ax, title, "Memory scale (nodes)", ylabel, scales)

    out = output_dir / f"score_vs_scale_{_slug(family)}.png"
    fig.tight_layout()
    fig.savefig(out, dpi=150)
    plt.close(fig)
    return out


def plot_tokens_vs_scale(
    family: str,
    method_data: dict,
    output_dir: Path,
) -> Path:
    scales = _sorted_scales(method_data)
    methods = _methods_present(method_data, _METHOD_ORDER)

    fig, ax = plt.subplots(figsize=(6, 4))
    for method in methods:
        ys = [method_data[method].get(s, {}).get("tokens_returned", float("nan")) for s in scales]
        ax.plot(
            scales, ys,
            marker=METHOD_MARKERS.get(method, "o"),
            color=METHOD_COLORS.get(method, "#888"),
            label=METHOD_LABELS.get(method, method),
            linewidth=2,
            markersize=7,
        )

    title = FAMILY_TITLES.get(family, family)
    _apply_style(ax, title, "Memory scale (nodes)", "Tokens returned", scales)

    out = output_dir / f"tokens_vs_scale_{_slug(family)}.png"
    fig.tight_layout()
    fig.savefig(out, dpi=150)
    plt.close(fig)
    return out


# ---------------------------------------------------------------------------
# Combined all-families charts (2×3 grid)
# ---------------------------------------------------------------------------


def plot_all_families_score(data: dict, output_dir: Path) -> Path:
    families = list(data.keys())
    n = len(families)
    ncols = 3
    nrows = (n + ncols - 1) // ncols

    fig, axes = plt.subplots(nrows, ncols, figsize=(5 * ncols, 4 * nrows))
    axes_flat = np.array(axes).flatten()

    for i, family in enumerate(families):
        ax = axes_flat[i]
        method_data = data[family]
        scales = _sorted_scales(method_data)
        methods = _methods_present(method_data, _METHOD_ORDER)

        for method in methods:
            ys = [method_data[method].get(s, {}).get("score", float("nan")) for s in scales]
            ax.plot(
                scales, ys,
                marker=METHOD_MARKERS.get(method, "o"),
                color=METHOD_COLORS.get(method, "#888"),
                label=METHOD_LABELS.get(method, method),
                linewidth=2,
                markersize=6,
            )

        ax.set_ylim(-0.05, 1.10)
        ax.yaxis.set_major_formatter(mticker.PercentFormatter(xmax=1.0))
        title = FAMILY_TITLES.get(family, family)
        ylabel = SCORE_METRIC_LABEL.get(family, "Score")
        _apply_style(ax, title, "Scale", ylabel, scales)

    # Hide unused subplots
    for j in range(i + 1, len(axes_flat)):
        axes_flat[j].set_visible(False)

    fig.suptitle(
        "Score vs Scale — Waggle RLM-style Benchmark\n"
        "(raw_context vs query_graph vs build_context)",
        fontsize=13, fontweight="bold", y=1.01,
    )
    out = output_dir / "score_vs_scale_all.png"
    fig.tight_layout()
    fig.savefig(out, dpi=150, bbox_inches="tight")
    plt.close(fig)
    return out


def plot_all_families_tokens(data: dict, output_dir: Path) -> Path:
    families = list(data.keys())
    n = len(families)
    ncols = 3
    nrows = (n + ncols - 1) // ncols

    fig, axes = plt.subplots(nrows, ncols, figsize=(5 * ncols, 4 * nrows))
    axes_flat = np.array(axes).flatten()

    for i, family in enumerate(families):
        ax = axes_flat[i]
        method_data = data[family]
        scales = _sorted_scales(method_data)
        methods = _methods_present(method_data, _METHOD_ORDER)

        for method in methods:
            ys = [method_data[method].get(s, {}).get("tokens_returned", float("nan")) for s in scales]
            ax.plot(
                scales, ys,
                marker=METHOD_MARKERS.get(method, "o"),
                color=METHOD_COLORS.get(method, "#888"),
                label=METHOD_LABELS.get(method, method),
                linewidth=2,
                markersize=6,
            )

        title = FAMILY_TITLES.get(family, family)
        _apply_style(ax, title, "Scale", "Tokens returned", scales)

    for j in range(i + 1, len(axes_flat)):
        axes_flat[j].set_visible(False)

    fig.suptitle(
        "Tokens Returned vs Scale — Waggle RLM-style Benchmark\n"
        "(raw_context vs query_graph vs build_context)",
        fontsize=13, fontweight="bold", y=1.01,
    )
    out = output_dir / "tokens_vs_scale_all.png"
    fig.tight_layout()
    fig.savefig(out, dpi=150, bbox_inches="tight")
    plt.close(fig)
    return out


# ---------------------------------------------------------------------------
# Token reduction chart: build_context / raw_context ratio
# ---------------------------------------------------------------------------


def plot_token_reduction(data: dict, output_dir: Path) -> Path:
    """
    Bar chart: for each family × scale, show
    tokens(build_context) / tokens(raw_context) as a percentage.
    Lower is better.
    """
    families = list(data.keys())
    all_scales = sorted({s for fam in data.values() for m in fam.values() for s in m})

    # Collect ratios
    records = []
    for family in families:
        for scale in all_scales:
            bc = data[family].get("build_context", {}).get(scale, {})
            rc = data[family].get("raw_context", {}).get(scale, {})
            if bc and rc and rc.get("tokens_returned", 0) > 0:
                ratio = bc["tokens_returned"] / rc["tokens_returned"]
                records.append({
                    "family": family,
                    "scale": scale,
                    "ratio": ratio,
                    "bc_score": bc.get("score", 0),
                    "rc_score": rc.get("score", 0),
                })

    if not records:
        fig, ax = plt.subplots(figsize=(8, 4))
        ax.text(0.5, 0.5, "No data", ha="center", va="center")
        out = output_dir / "token_reduction_vs_scale.png"
        fig.savefig(out, dpi=150)
        plt.close(fig)
        return out

    # Group by family for grouped bar chart
    n_scales = len(all_scales)
    n_families = len(families)
    bar_width = 0.8 / n_scales
    x = list(range(n_families))

    fig, ax = plt.subplots(figsize=(max(8, n_families * 2), 5))

    scale_colors = ["#4a90d9", "#e07b39", "#3dba6e"]
    for si, scale in enumerate(all_scales):
        ratios = []
        for family in families:
            rec = next((r for r in records if r["family"] == family and r["scale"] == scale), None)
            ratios.append(rec["ratio"] if rec else float("nan"))

        offsets = [xi + (si - n_scales / 2 + 0.5) * bar_width for xi in x]
        bars = ax.bar(
            offsets, ratios,
            width=bar_width * 0.9,
            color=scale_colors[si % len(scale_colors)],
            alpha=0.85,
            label=f"scale={scale}",
        )
        # Annotate bars with percentage
        for bar, ratio in zip(bars, ratios):
            if not (ratio != ratio):  # not nan
                ax.text(
                    bar.get_x() + bar.get_width() / 2,
                    bar.get_height() + 0.01,
                    f"{ratio:.0%}",
                    ha="center", va="bottom", fontsize=7,
                )

    ax.axhline(1.0, color="#e05c5c", linestyle="--", linewidth=1.2, label="raw_context baseline (100%)")
    ax.set_xticks(x)
    ax.set_xticklabels(
        [FAMILY_TITLES.get(f, f).split("\n")[0] for f in families],
        fontsize=8, rotation=15, ha="right",
    )
    ax.set_ylabel("build_context tokens / raw_context tokens\n(lower = more efficient)", fontsize=9)
    ax.set_title(
        "Token Reduction: build_context vs raw_context\n"
        "(100% = same tokens as raw dump; lower is better)",
        fontsize=11, fontweight="bold",
    )
    ax.set_ylim(0, 1.3)
    ax.yaxis.set_major_formatter(mticker.PercentFormatter(xmax=1.0))
    ax.legend(fontsize=8, framealpha=0.7)
    ax.grid(axis="y", linestyle="--", alpha=0.4)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)

    out = output_dir / "token_reduction_vs_scale.png"
    fig.tight_layout()
    fig.savefig(out, dpi=150)
    plt.close(fig)
    return out


# ---------------------------------------------------------------------------
# Score × Token efficiency scatter (summary chart)
# ---------------------------------------------------------------------------


def plot_score_token_scatter(data: dict, output_dir: Path) -> Path:
    """
    Scatter: x=tokens_returned, y=score, one point per (family, scale, method).
    build_context points should cluster top-left (high score, low tokens).
    """
    fig, ax = plt.subplots(figsize=(8, 6))

    plotted: set[str] = set()
    for family, method_data in data.items():
        for method, scale_data in method_data.items():
            for scale, vals in scale_data.items():
                tokens = vals.get("tokens_returned", 0)
                score = vals.get("score", 0)
                color = METHOD_COLORS.get(method, "#888")
                marker = METHOD_MARKERS.get(method, "o")
                label = METHOD_LABELS.get(method, method) if method not in plotted else "_nolegend_"
                plotted.add(method)
                ax.scatter(
                    tokens, score,
                    c=color, marker=marker, s=60, alpha=0.75,
                    label=label, zorder=3,
                )

    ax.set_xlabel("Tokens returned", fontsize=10)
    ax.set_ylabel("Score", fontsize=10)
    ax.yaxis.set_major_formatter(mticker.PercentFormatter(xmax=1.0))
    ax.set_title(
        "Score vs Tokens Returned (all families, all scales)\n"
        "Top-left = high accuracy + low token cost",
        fontsize=11, fontweight="bold",
    )
    ax.grid(linestyle="--", alpha=0.35)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)

    # Deduplicate legend
    handles, labels = ax.get_legend_handles_labels()
    seen: dict[str, int] = {}
    dedup_h, dedup_l = [], []
    for h, l in zip(handles, labels):
        if l not in seen:
            seen[l] = 1
            dedup_h.append(h)
            dedup_l.append(l)
    ax.legend(dedup_h, dedup_l, fontsize=9, framealpha=0.7)

    out = output_dir / "score_token_scatter.png"
    fig.tight_layout()
    fig.savefig(out, dpi=150)
    plt.close(fig)
    return out


# ---------------------------------------------------------------------------
# ASCII fallback (no matplotlib)
# ---------------------------------------------------------------------------


def print_ascii_charts(data: dict) -> None:
    """Print compact ASCII tables when matplotlib is unavailable."""
    print("\n=== Score vs Scale ===")
    for family, method_data in data.items():
        print(f"\n{family}")
        scales = _sorted_scales(method_data)
        methods = _methods_present(method_data, _METHOD_ORDER)
        header = f"  {'Method':<28}" + "".join(f"{s:>8}" for s in scales)
        print(header)
        for method in methods:
            row = f"  {METHOD_LABELS.get(method, method):<28}"
            for s in scales:
                v = method_data[method].get(s, {}).get("score", float("nan"))
                row += f"{v:>8.3f}" if v == v else f"{'—':>8}"
            print(row)

    print("\n=== Tokens Returned vs Scale ===")
    for family, method_data in data.items():
        print(f"\n{family}")
        scales = _sorted_scales(method_data)
        methods = _methods_present(method_data, _METHOD_ORDER)
        header = f"  {'Method':<28}" + "".join(f"{s:>8}" for s in scales)
        print(header)
        for method in methods:
            row = f"  {METHOD_LABELS.get(method, method):<28}"
            for s in scales:
                v = method_data[method].get(s, {}).get("tokens_returned", None)
                row += f"{v:>8}" if v is not None else f"{'—':>8}"
            print(row)

    print("\n=== Token Reduction (build_context / raw_context) ===")
    for family, method_data in data.items():
        scales = _sorted_scales(method_data)
        parts = []
        for s in scales:
            bc = method_data.get("build_context", {}).get(s, {}).get("tokens_returned")
            rc = method_data.get("raw_context", {}).get(s, {}).get("tokens_returned")
            if bc and rc:
                parts.append(f"scale={s}: {bc/rc:.0%}")
        if parts:
            print(f"  {family}: {', '.join(parts)}")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _slug(s: str) -> str:
    return s.lower().replace(" ", "_").replace("-", "_").replace("(", "").replace(")", "").replace("/", "_")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Plot RLM-style Waggle benchmark results")
    parser.add_argument(
        "--input",
        default="benchmark_results/rlm_style_waggle_results.csv",
        help="Path to results CSV",
    )
    parser.add_argument(
        "--output",
        default="benchmark_results/charts",
        help="Output directory for chart images",
    )
    parser.add_argument(
        "--no-matplotlib",
        action="store_true",
        help="Print ASCII tables instead of generating PNG charts",
    )
    args = parser.parse_args(argv)

    csv_path = Path(args.input)
    if not csv_path.exists():
        print(f"ERROR: Input file not found: {csv_path}", file=sys.stderr)
        print("Run the benchmark first:", file=sys.stderr)
        print("  python benchmarks/rlm_style_waggle_eval.py --scales 128 512 2048", file=sys.stderr)
        return 1

    rows = load_csv(str(csv_path))
    if not rows:
        print("ERROR: CSV is empty.", file=sys.stderr)
        return 1

    data = pivot(rows)

    if args.no_matplotlib or not HAS_MPL:
        if not HAS_MPL:
            print("matplotlib not available — printing ASCII tables instead.")
            print("Install with: pip install matplotlib")
        print_ascii_charts(data)
        return 0

    out_dir = Path(args.output)
    out_dir.mkdir(parents=True, exist_ok=True)

    generated: list[Path] = []

    # Per-family charts
    for family, method_data in data.items():
        generated.append(plot_score_vs_scale(family, method_data, out_dir))
        generated.append(plot_tokens_vs_scale(family, method_data, out_dir))

    # Combined all-families charts
    generated.append(plot_all_families_score(data, out_dir))
    generated.append(plot_all_families_tokens(data, out_dir))

    # Token reduction bar chart
    generated.append(plot_token_reduction(data, out_dir))

    # Score × token scatter
    generated.append(plot_score_token_scatter(data, out_dir))

    print(f"Generated {len(generated)} charts in {out_dir}/")
    for p in generated:
        print(f"  {p}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
