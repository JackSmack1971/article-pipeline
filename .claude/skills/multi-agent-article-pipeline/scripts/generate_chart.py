#!/usr/bin/env python3
"""
generate_chart.py — VIZ-CANDIDATE Chart Generator
Usage: python3 generate_chart.py --spec SPEC_JSON_FILE [--output DIR]

SPEC_JSON format:
{
  "section": "Polling Gap",
  "chart_type": "bar",
  "title": "Violence Tolerance Gap by Political Affiliation",
  "takeaway": "25% vs 4-6% tolerance gap across partisan lines",
  "source": "PRRI American Values Survey, 2026",
  "data": {
    "labels": ["Democrat", "Republican", "Independent"],
    "values": [25, 5, 11],
    "unit": "%",
    "color_scheme": "partisan"
  },
  "output_filename": "violence-tolerance-gap-partisan-prri-2026.webp"
}

Chart types supported: bar, horizontal_bar, line, comparison_bar, donut
Color schemes: partisan (blue/red/purple), neutral (slate), signal (green/orange/red)

Exit codes:
  0 — Chart generated successfully
  1 — Spec validation error
  2 — Rendering error (matplotlib unavailable or write failure)
"""

import argparse
import json
import sys
from pathlib import Path


# ── Color palettes ─────────────────────────────────────────────────────────

COLOR_SCHEMES = {
    "partisan": ["#2563eb", "#dc2626", "#7c3aed", "#0891b2", "#059669"],
    "neutral": ["#475569", "#64748b", "#94a3b8", "#cbd5e1", "#1e293b"],
    "signal": ["#16a34a", "#ea580c", "#dc2626", "#0891b2", "#7c3aed"],
    "monochrome": ["#1e293b", "#334155", "#475569", "#64748b", "#94a3b8"],
}


# ── Spec validation ─────────────────────────────────────────────────────────

def validate_spec(spec: dict) -> list:
    """Returns list of error strings. Empty = valid."""
    errors = []
    required = ["section", "chart_type", "title", "takeaway", "source", "data", "output_filename"]
    for field in required:
        if field not in spec:
            errors.append(f"Missing required field: '{field}'")

    supported_types = ("bar", "horizontal_bar", "line", "comparison_bar", "donut")
    if "chart_type" in spec and spec["chart_type"] not in supported_types:
        errors.append(f"chart_type '{spec['chart_type']}' not in {supported_types}")

    if "data" in spec:
        data = spec["data"]
        if "labels" not in data or "values" not in data:
            errors.append("data must have 'labels' and 'values' arrays")
        elif len(data["labels"]) != len(data["values"]):
            errors.append("data.labels and data.values must have the same length")

    if "output_filename" in spec:
        fn = spec["output_filename"]
        if not any(fn.endswith(ext) for ext in (".webp", ".png", ".svg")):
            errors.append("output_filename must end with .webp, .png, or .svg")

    return errors


# ── Chart renderers ─────────────────────────────────────────────────────────

def render_chart(spec: dict, output_dir: Path) -> Path:
    """Render the chart and return the output file path."""
    try:
        import matplotlib
        matplotlib.use("Agg")  # non-interactive backend
        import matplotlib.pyplot as plt
        import matplotlib.patches as mpatches
    except ImportError:
        raise RuntimeError(
            "matplotlib is not installed. Run: pip install matplotlib --break-system-packages"
        )

    data = spec["data"]
    labels = data["labels"]
    values = data["values"]
    unit = data.get("unit", "")
    scheme = data.get("color_scheme", "neutral")
    colors = COLOR_SCHEMES.get(scheme, COLOR_SCHEMES["neutral"])
    colors = (colors * ((len(labels) // len(colors)) + 1))[: len(labels)]

    chart_type = spec["chart_type"]
    title = spec["title"]
    source = spec["source"]
    takeaway = spec["takeaway"]

    fig, ax = plt.subplots(figsize=(9, 5))
    fig.patch.set_facecolor("#f8fafc")
    ax.set_facecolor("#f8fafc")

    if chart_type == "bar":
        bars = ax.bar(labels, values, color=colors, width=0.55, zorder=2)
        ax.bar_label(bars, fmt=f"%.1f{unit}", padding=4, fontsize=10, fontweight="bold")
        ax.set_ylim(0, max(values) * 1.25)
        ax.set_ylabel(unit or "Value", fontsize=10)

    elif chart_type == "horizontal_bar":
        bars = ax.barh(labels, values, color=colors, height=0.5, zorder=2)
        ax.bar_label(bars, fmt=f"%.1f{unit}", padding=4, fontsize=10, fontweight="bold")
        ax.set_xlim(0, max(values) * 1.25)
        ax.set_xlabel(unit or "Value", fontsize=10)
        ax.invert_yaxis()

    elif chart_type == "line":
        ax.plot(labels, values, color=colors[0], linewidth=2.5, marker="o", markersize=7, zorder=2)
        for i, v in enumerate(values):
            ax.annotate(f"{v}{unit}", (labels[i], v), textcoords="offset points",
                        xytext=(0, 10), ha="center", fontsize=9, fontweight="bold")
        ax.set_ylim(0, max(values) * 1.25)

    elif chart_type == "comparison_bar":
        # Two-series bar chart: data.values is list of lists
        import numpy as np
        if not isinstance(values[0], list):
            raise ValueError("comparison_bar requires data.values to be a list of lists")
        series_labels = data.get("series_labels", [f"Series {i+1}" for i in range(len(values))])
        x = range(len(labels))
        width = 0.35
        for i, (series_vals, slabel) in enumerate(zip(values, series_labels)):
            offset = (i - len(values) / 2 + 0.5) * width
            rects = ax.bar([xi + offset for xi in x], series_vals,
                          width=width, label=slabel, color=colors[i], zorder=2)
            ax.bar_label(rects, fmt=f"%.1f{unit}", padding=3, fontsize=9)
        ax.set_xticks(list(x))
        ax.set_xticklabels(labels)
        ax.legend(fontsize=9)
        ax.set_ylim(0, max(max(s) for s in values) * 1.3)

    elif chart_type == "donut":
        wedges, texts, autotexts = ax.pie(
            values, labels=labels, colors=colors, autopct=f"%1.1f{unit}",
            startangle=90, pctdistance=0.8,
            wedgeprops={"width": 0.5, "edgecolor": "white", "linewidth": 2}
        )
        for at in autotexts:
            at.set_fontsize(10)
            at.set_fontweight("bold")

    # Common styling
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_alpha(0.3)
    ax.spines["bottom"].set_alpha(0.3)
    ax.grid(axis="y" if chart_type in ("bar", "line", "comparison_bar") else "x",
            alpha=0.25, zorder=1)
    ax.tick_params(labelsize=10)

    ax.set_title(title, fontsize=13, fontweight="bold", pad=14, loc="left")
    fig.text(0.01, -0.04, f"Source: {source}", fontsize=8, color="#64748b",
             transform=ax.transAxes)
    fig.text(0.01, -0.10, f"Takeaway: {takeaway}", fontsize=8.5, color="#1e293b",
             style="italic", transform=ax.transAxes)

    plt.tight_layout()

    output_dir.mkdir(parents=True, exist_ok=True)
    out_path = output_dir / spec["output_filename"]

    # WebP requires Pillow; fall back to PNG gracefully
    if str(out_path).endswith(".webp"):
        try:
            from PIL import Image
            import io
            buf = io.BytesIO()
            fig.savefig(buf, format="png", dpi=144, bbox_inches="tight")
            buf.seek(0)
            img = Image.open(buf)
            img.save(out_path, "webp", quality=88)
        except ImportError:
            # Pillow not available — save as PNG instead
            png_path = out_path.with_suffix(".png")
            fig.savefig(png_path, dpi=144, bbox_inches="tight", facecolor=fig.get_facecolor())
            out_path = png_path
            print(f"  ℹ️  Pillow not available — saved as PNG: {out_path.name}")
    else:
        fig.savefig(out_path, dpi=144, bbox_inches="tight", facecolor=fig.get_facecolor())

    plt.close(fig)
    return out_path


# ── Main ─────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Generate a chart from a VIZ-CANDIDATE spec.")
    parser.add_argument("--spec", required=True, help="Path to JSON spec file")
    parser.add_argument("--output", default="charts", help="Output directory for chart files")
    args = parser.parse_args()

    spec_path = Path(args.spec)
    if not spec_path.exists():
        print(f"❌ Spec file not found: {spec_path}")
        sys.exit(1)

    try:
        spec = json.loads(spec_path.read_text())
    except json.JSONDecodeError as e:
        print(f"❌ Spec JSON parse error: {e}")
        sys.exit(1)

    errors = validate_spec(spec)
    if errors:
        print("❌ Spec validation failed:")
        for e in errors:
            print(f"  • {e}")
        sys.exit(1)

    print(f"\n  Rendering chart: {spec['title']}")
    print(f"  Type: {spec['chart_type']} | Labels: {len(spec['data']['labels'])}")

    try:
        out_path = render_chart(spec, Path(args.output))
        print(f"  ✅ Chart saved: {out_path}")
        print(f"\nInsert into article_draft.md as:")
        print(f"  ![Chart: {spec['takeaway']} — {spec['source']}]({out_path})\n")
    except RuntimeError as e:
        print(f"❌ Rendering error: {e}")
        sys.exit(2)
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        sys.exit(2)


if __name__ == "__main__":
    main()
