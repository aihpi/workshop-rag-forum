"""Render the figures and the QR code for the S1.1 deck (llm-wiki_intro.pptx).

Writes into ``assets/`` next to this script:

- ``fig-layers.png``          slide 5, the three layers of the KISZ wiki
- ``fig-cycle.png``           slide 7, the maintenance cycle with four stations
- ``fig-context-window.png``  slide 10, index inside the 128,000-token window
- ``fig-context-scale.png``   slide 11, the same bar at 1x, 10x and 20x pages
- ``qr-readme.png``           slide 12 and X6, QR code to the session README

Every figure is drawn at its display size on the slide, so point sizes here are
point sizes on the slide. Style follows figures-bw (greys first, one accent).

Run from the repository root:
uv run --with matplotlib --with "qrcode[pil]" python 03_workshop/261102-llm-wiki/components/S1.1-input/make_figures.py
"""

from __future__ import annotations

import textwrap
from pathlib import Path

import matplotlib as mpl

mpl.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import qrcode  # noqa: E402
from matplotlib.patches import FancyArrowPatch, Rectangle  # noqa: E402
from matplotlib.path import Path as MplPath  # noqa: E402

HERE = Path(__file__).resolve().parent
ASSETS = HERE / "assets"

README_URL = (
    "https://github.com/aihpi/workshop-rag-forum/tree/main/03_workshop/261102-llm-wiki"
)

INK, GREY, MID, LIGHT, RULE = "#212427", "#5a6065", "#83888c", "#acb0b2", "#d6d7d8"
ACCENT, WHITE = "#b1063a", "#ffffff"

mpl.rcParams.update(
    {
        "font.family": "sans-serif",
        "font.sans-serif": ["Verdana", "Inter", "DejaVu Sans", "Arial"],
        "text.color": INK,
        "figure.facecolor": WHITE,
        "savefig.facecolor": WHITE,
        "savefig.dpi": 300,
    }
)


def canvas(width: float, height: float) -> tuple[plt.Figure, plt.Axes]:
    """Figure whose data coordinates are inches from the top-left corner."""
    fig = plt.figure(figsize=(width, height))
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(0, width)
    ax.set_ylim(height, 0)
    ax.set_axis_off()
    return fig, ax


def save(fig: plt.Figure, name: str) -> None:
    fig.savefig(ASSETS / name)
    plt.close(fig)
    print(f"wrote {ASSETS / name}")


def de(n: int) -> str:
    """German thousands separator: 128000 -> 128.000."""
    return f"{n:,}".replace(",", ".")


# ------------------------------------------------------------------ slide 5
def layers() -> None:
    w, h = 12.1, 4.5
    fig, ax = canvas(w, h)
    area = 7.6  # width reserved for the bands
    cx = area / 2
    band_h, gap, top = 1.2, 0.15, 0.45
    bands = [
        (
            "Regeln",
            "eine Datei; wie Seiten aussehen, was nie hineindarf",
            5.2,
            RULE,
            INK,
        ),
        (
            "Seiten",
            "rund 140 Textseiten zu Team, Projekten, Workshops, Veranstaltungen, Abläufen",
            area,
            INK,
            WHITE,
        ),
        (
            "Quellen",
            "GitHub, Eventbrite, Homepage, Nextcloud, Gespräche",
            6.4,
            LIGHT,
            INK,
        ),
    ]
    cells = [
        ("das Team", ""),
        ("die KI", "Menschen"),
        ("liest die KI, verändert sie nie", None),
    ]
    col1, col2 = 9.05, 11.1  # centres of the columns "schreibt" and "gibt frei"
    ax.text(col1, 0.22, "schreibt", ha="center", va="center", fontsize=14, color=GREY)
    ax.text(col2, 0.22, "gibt frei", ha="center", va="center", fontsize=14, color=GREY)
    ax.plot([8.05, w], [0.42, 0.42], color=RULE, lw=1)
    for i, ((name, desc, bw, fill, fg), (c1, c2)) in enumerate(
        zip(bands, cells, strict=True)
    ):
        y = top + i * (band_h + gap)
        x = cx - bw / 2
        ax.add_patch(Rectangle((x, y), bw, band_h, facecolor=fill, edgecolor="none"))
        ax.text(
            x + 0.25, y + 0.3, name, fontsize=18, weight="bold", color=fg, va="center"
        )
        chars = int((bw - 0.5) / 0.118)
        ax.text(
            x + 0.25,
            y + 0.62,
            "\n".join(textwrap.wrap(desc, chars)),
            fontsize=14,
            color=fg,
            va="top",
            linespacing=1.3,
        )
        yc = y + band_h / 2
        if c2 is None:  # one statement across both columns
            ax.text(
                (col1 + col2) / 2,
                yc,
                "\n".join(textwrap.wrap(c1, 18)),
                ha="center",
                va="center",
                fontsize=16,
                linespacing=1.3,
            )
        else:
            ax.text(col1, yc, c1, ha="center", va="center", fontsize=16)
            ax.text(col2, yc, c2, ha="center", va="center", fontsize=16)
        if i < 2:
            ax.plot([8.05, w], [y + band_h + gap / 2] * 2, color=RULE, lw=1)
    save(fig, "fig-layers.png")


# ------------------------------------------------------------------ slide 7
def cycle() -> None:
    w, h = 8.3, 4.6
    fig, ax = canvas(w, h)
    cx, cy, r, node = 4.15, 2.3, 1.3, 0.2
    # stations clockwise from the top; angles in screen coordinates (y down)
    stations = [
        (-90, ACCENT, 'Jemand gibt der KI eine Quelle: Link, Text, "ins Wiki"', 34),
        (0, GREY, "KI zeigt, welche Seiten sich ändern, fragt einmal nach", 19),
        (
            90,
            GREY,
            "KI schreibt den Entwurf; Unbekanntes wird offene Frage mit Namen",
            40,
        ),
        (180, ACCENT, "Änderungsvorschlag: ein Mensch gibt frei", 20),
    ]
    gap = np.degrees((node + 0.12) / r)
    for k, (ang, *_rest) in enumerate(stations):
        a0 = ang + gap
        a1 = stations[(k + 1) % 4][0] + (360 if k == 3 else 0) - gap
        t = np.radians(np.linspace(a0, a1, 60))
        pts = np.column_stack([cx + r * np.cos(t), cy + r * np.sin(t)])
        ax.add_patch(
            FancyArrowPatch(
                path=MplPath(pts),
                arrowstyle="-|>",
                mutation_scale=16,
                color=GREY,
                lw=1.6,
            )
        )
    for ang, colour, label, chars in stations:
        x = cx + r * np.cos(np.radians(ang))
        y = cy + r * np.sin(np.radians(ang))
        ax.add_patch(
            plt.Circle((x, y), node, facecolor=colour, edgecolor="none", zorder=3)
        )
        text = "\n".join(textwrap.wrap(label, chars))
        kw = dict(fontsize=15, linespacing=1.3, color=INK)
        if ang == -90:
            ax.text(x, y - node - 0.15, text, ha="center", va="bottom", **kw)
        elif ang == 90:
            ax.text(x, y + node + 0.15, text, ha="center", va="top", **kw)
        elif ang == 0:
            ax.text(x + node + 0.2, y, text, ha="left", va="center", **kw)
        else:
            ax.text(x - node - 0.2, y, text, ha="right", va="center", **kw)
    save(fig, "fig-cycle.png")


# ------------------------------------------------------------ slides 10, 11
WINDOW = 128_000
X0, SCALE = 1.0, 9.0 / WINDOW  # inches: bar origin, inches per token (shared by both)


def _frame(ax: plt.Axes, y: float, bar_h: float) -> None:
    ax.add_patch(
        Rectangle(
            (X0, y),
            WINDOW * SCALE,
            bar_h,
            facecolor="none",
            edgecolor=GREY,
            lw=1.4,
            zorder=2,
        )
    )


def context_window() -> None:
    w, h = 12.1, 1.45
    fig, ax = canvas(w, h)
    y, bar_h = 0.55, 0.6
    _frame(ax, y, bar_h)
    ax.add_patch(
        Rectangle((X0, y), 8_000 * SCALE, bar_h, facecolor=ACCENT, edgecolor="none")
    )
    ax.text(
        X0,
        y - 0.15,
        "Inhaltsverzeichnis: rund 8.000 Tokens",
        fontsize=15,
        va="bottom",
        color=ACCENT,
    )
    ax.text(
        X0 + WINDOW * SCALE,
        y - 0.15,
        f"Kontextfenster: {de(WINDOW)} Tokens",
        fontsize=15,
        va="bottom",
        ha="right",
        color=GREY,
    )
    save(fig, "fig-context-window.png")


def context_scale() -> None:
    w, h = 12.1, 2.55
    fig, ax = canvas(w, h)
    bar_h, step, top = 0.5, 0.68, 0.55
    rows = [("1x", 8_000, ACCENT), ("10x", 80_000, MID), ("20x", 160_000, INK)]
    ax.text(
        X0 + WINDOW * SCALE,
        top - 0.15,
        f"Kontextfenster: {de(WINDOW)} Tokens",
        fontsize=15,
        va="bottom",
        ha="right",
        color=GREY,
    )
    for i, (label, tokens, colour) in enumerate(rows):
        y = top + i * step
        ax.text(X0 - 0.2, y + bar_h / 2, label, ha="right", va="center", fontsize=16)
        ax.add_patch(
            Rectangle(
                (X0, y), tokens * SCALE, bar_h, facecolor=colour, edgecolor="none"
            )
        )
        if tokens > WINDOW:  # the part that no longer fits
            ax.add_patch(
                Rectangle(
                    (X0 + WINDOW * SCALE, y),
                    (tokens - WINDOW) * SCALE,
                    bar_h,
                    facecolor=WHITE,
                    edgecolor=INK,
                    hatch="///",
                    lw=1.2,
                    zorder=3,
                )
            )
            ax.text(
                X0 + WINDOW * SCALE - 0.15,
                y + bar_h / 2,
                f"rund {de(tokens)}",
                ha="right",
                va="center",
                fontsize=15,
                color=WHITE,
                zorder=4,
            )
        else:
            ax.text(
                X0 + tokens * SCALE + 0.15,
                y + bar_h / 2,
                f"rund {de(tokens)}",
                ha="left",
                va="center",
                fontsize=15,
            )
        _frame(ax, y, bar_h)
    save(fig, "fig-context-scale.png")


# ----------------------------------------------------------------- QR code
def qr_readme() -> None:
    qr = qrcode.QRCode(
        error_correction=qrcode.constants.ERROR_CORRECT_M, box_size=20, border=2
    )
    qr.add_data(README_URL)
    qr.make(fit=True)
    qr.make_image(fill_color=INK, back_color=WHITE).save(ASSETS / "qr-readme.png")
    print(f"wrote {ASSETS / 'qr-readme.png'}")


if __name__ == "__main__":
    ASSETS.mkdir(exist_ok=True)
    layers()
    cycle()
    context_window()
    context_scale()
    qr_readme()
