"""Render the meeting's figures from data/results/study_{R,K}.json.

    uv run python 03_workshop/260901-rag-bias/03_make_figures.py
"""

from __future__ import annotations

import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

REPO_ROOT = Path(__file__).resolve().parents[2]
RESULTS_DIR = REPO_ROOT / "data" / "results"
OUT_DIR = Path(__file__).resolve().parent

# Categorical slots 1, 2, 3 of the reference palette: the only prefix that clears
# the all-pairs CVD and normal-vision floors, which grouped bars need.
SERIES = ["#2a78d6", "#eb6834", "#1baf7a"]
INK, INK_MUTED, GRID, SURFACE = "#0b0b0b", "#52514e", "#e4e3df", "#fcfcfb"
GROUP_LABEL = {"female": "Frauen", "male": "Männer", "other": "andere"}

plt.rcParams.update({
    "figure.facecolor": SURFACE, "axes.facecolor": SURFACE, "axes.edgecolor": GRID,
    "axes.labelcolor": INK_MUTED, "axes.titlecolor": INK, "text.color": INK,
    "xtick.color": INK_MUTED, "ytick.color": INK_MUTED,
    "font.size": 10, "axes.titlesize": 12, "axes.titleweight": "bold", "figure.dpi": 150,
})


def style(ax, ylabel: str = "") -> None:
    ax.spines[["top", "right"]].set_visible(False)
    ax.spines[["left", "bottom"]].set_color(GRID)
    ax.yaxis.grid(True, color=GRID, linewidth=0.8)
    ax.set_axisbelow(True)
    ax.set_ylabel(ylabel, color=INK_MUTED)
    ax.margins(y=0.18)


def legend(ax) -> None:
    handles, labels = ax.get_legend_handles_labels()
    if len(handles) < 2:
        return
    ax.legend(handles, labels, frameon=False, fontsize=9, ncol=min(len(handles), 4),
              loc="upper center", bbox_to_anchor=(0.5, -0.11))


def neutral_line(ax, n_categories: int) -> None:
    """A = 1 is the whole reference; it must be the most visible line on the axes."""
    ax.axhline(1.0, color=INK_MUTED, linestyle=(0, (4, 3)), linewidth=1.3)
    ax.annotate("A = 1 (neutral)", (1.0, 1.0), xycoords=("axes fraction", "data"),
                xytext=(6, -3), textcoords="offset points", ha="left",
                fontsize=8, color=INK_MUTED)


def load(variant: str) -> dict | None:
    path = RESULTS_DIR / f"study_{variant}.json"
    return json.loads(path.read_text()) if path.exists() else None


def strata_of(results: dict) -> list[str]:
    return [s["occupation"] for s in results["strata"]]


def block(results: dict, occupation: str, k: int) -> dict:
    stratum = next(s for s in results["strata"] if s["occupation"] == occupation)
    return stratum["by_k"][str(k)]


def _bars(ax, categories, series, errors=None, fmt="{:.2f}"):
    n = len(series)
    slot = 0.8 / n
    width = slot * 0.88
    for i, (label, values) in enumerate(series.items()):
        offset = (i - (n - 1) / 2) * slot
        xs = [x + offset for x in range(len(categories))]
        plotted = [0.0 if v is None else v for v in values]
        err = None
        if errors:
            lo, hi = errors[label]
            err = [
                [0.0 if v is None else max(0.0, v - l) for v, l in zip(plotted, lo)],
                [0.0 if v is None else max(0.0, h - v) for v, h in zip(plotted, hi)],
            ]
        bars = ax.bar(xs, plotted, width, label=label, color=SERIES[i % len(SERIES)],
                      linewidth=0)
        if err:
            ax.errorbar(xs, plotted, yerr=err, fmt="none", ecolor=INK_MUTED,
                        elinewidth=1.1, capsize=3)
        for bar, value in zip(bars, values):
            text = "n/a" if value is None else fmt.format(value)
            ax.annotate(text, (bar.get_x() + bar.get_width() / 2, bar.get_height()),
                        textcoords="offset points", xytext=(0, 4), ha="center",
                        fontsize=8, color=INK_MUTED)
    ax.set_xticks(range(len(categories)))
    ax.set_xticklabels(categories)


def fig_amplification(results: dict, k: int = 10) -> None:
    occupations = strata_of(results)
    groups = results["config"]["groups"]
    series, errors = {}, {}
    for group in groups:
        values, lows, highs = [], [], []
        for occ in occupations:
            b = block(results, occ, k)
            a = b["amplification"][group]
            ci = b["amplification_ci95"][group]
            values.append(a)
            lows.append(ci[0] if ci else (a or 0.0))
            highs.append(ci[1] if ci else (a or 0.0))
        series[GROUP_LABEL.get(group, group)] = values
        errors[GROUP_LABEL.get(group, group)] = (lows, highs)

    fig, ax = plt.subplots(figsize=(10, 4.8))
    _bars(ax, occupations, series, errors)
    neutral_line(ax, len(occupations))
    style(ax, ylabel=f"A = p_{k} / p₀")
    ax.set_title(f"Variante {results['variant']} · k={k} · {results['config']['embedder']}")
    legend(ax)
    fig.suptitle("Wie stark verschiebt das Retrieval eine Gruppe gegenüber ihrer Basisrate?",
                 fontsize=13, fontweight="bold")
    fig.tight_layout()
    fig.savefig(OUT_DIR / f"fig_amplification_{results['variant']}_k{k}.png",
                bbox_inches="tight")
    plt.close(fig)


def fig_base_vs_topk(results: dict, k: int = 10) -> None:
    """p₀ against p_k: the two numbers A is built from, before the division."""
    occupations = strata_of(results)
    series = {
        "p₀ (Basisrate im Korpus)": [
            block(results, o, k)["base_rate"]["female"] for o in occupations
        ],
        f"p_{k} (Anteil in Top-{k})": [
            block(results, o, k)["top_k_share"]["female"] for o in occupations
        ],
    }
    fig, ax = plt.subplots(figsize=(9, 4.4))
    _bars(ax, occupations, series, fmt="{:.0%}")
    style(ax, ylabel="Frauenanteil")
    ax.set_title(f"Variante {results['variant']} · k={k}")
    legend(ax)
    fig.suptitle("Frauenanteil im Korpus gegenüber Frauenanteil in den Treffern",
                 fontsize=13, fontweight="bold")
    fig.tight_layout()
    fig.savefig(OUT_DIR / f"fig_base_vs_topk_{results['variant']}_k{k}.png",
                bbox_inches="tight")
    plt.close(fig)


def fig_variants(r: dict, kk: dict, k: int = 10) -> None:
    """R against K. K removes the corpus as an explanation, so what is left is
    attributable to the pipeline."""
    occupations = [o for o in strata_of(r) if o in strata_of(kk)]
    series, errors = {}, {}
    for label, results in (("Variante R (realistisch)", r), ("Variante K (50/50)", kk)):
        values, lows, highs = [], [], []
        for occ in occupations:
            b = block(results, occ, k)
            a = b["amplification"]["female"]
            ci = b["amplification_ci95"]["female"]
            values.append(a)
            lows.append(ci[0] if ci else (a or 0.0))
            highs.append(ci[1] if ci else (a or 0.0))
        series[label] = values
        errors[label] = (lows, highs)

    fig, ax = plt.subplots(figsize=(9.5, 4.6))
    _bars(ax, occupations, series, errors)
    neutral_line(ax, len(occupations))
    style(ax, ylabel=f"A für Frauen (k={k})")
    ax.set_title(f"{r['config']['embedder']} · k={k}")
    legend(ax)
    fig.suptitle("Bleibt die Schieflage bestehen, wenn der Korpus 50/50 ist?",
                 fontsize=13, fontweight="bold")
    fig.tight_layout()
    fig.savefig(OUT_DIR / f"fig_variants_k{k}.png", bbox_inches="tight")
    plt.close(fig)


def fig_wording(results: dict, k: int = 10) -> None:
    """Section 10: does the grammatical gender of the query drive the result?"""
    occupations = strata_of(results)
    wordings = ["generisch maskulin", "feminin", "geschlechtsneutral"]
    series = {w: [] for w in wordings}
    for occ in occupations:
        b = block(results, occ, k)
        per_query = list(b["per_query_amplification"].values())
        for i, wording in enumerate(wordings):
            series[wording].append(
                per_query[i]["female"] if i < len(per_query) else None
            )

    fig, ax = plt.subplots(figsize=(10, 4.6))
    _bars(ax, occupations, series)
    neutral_line(ax, len(occupations))
    style(ax, ylabel=f"A für Frauen (k={k})")
    ax.set_title(f"Variante {results['variant']} · {results['config']['embedder']}")
    legend(ax)
    fig.suptitle("Dieselbe Frage, drei Formulierungen — wie viel hängt am Wortlaut?",
                 fontsize=13, fontweight="bold")
    fig.tight_layout()
    fig.savefig(OUT_DIR / f"fig_wording_{results['variant']}_k{k}.png", bbox_inches="tight")
    plt.close(fig)


def main() -> None:
    r, kk = load("R"), load("K")
    if r is None and kk is None:
        raise SystemExit(f"no study_*.json in {RESULTS_DIR}; run 02_run_study.py first")
    for results in (r, kk):
        if results is None:
            continue
        for k in results["config"]["ks"]:
            fig_amplification(results, k)
            fig_base_vs_topk(results, k)
        fig_wording(results, results["config"]["ks"][0])
    if r and kk:
        fig_variants(r, kk, r["config"]["ks"][0])
    print(f"Wrote figures to {OUT_DIR}")


if __name__ == "__main__":
    main()
