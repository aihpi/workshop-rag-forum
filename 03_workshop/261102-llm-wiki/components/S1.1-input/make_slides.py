"""Build llm-wiki_intro.pptx, the S1.1 input deck of the RAG-Forum on 2026-11-02.

Starts from the AISC Light template (master, theme, logos), drops the template's own
slides and adds the 12 slides and the appendix X1 to X7 of the S1.1 component plan
(components/S1.1-input/plan.md, section 3). On-slide text and speaker notes are taken
from that plan; this script only formats and places them.

Slide 2 gets four click builds (appear on click) written as p:timing XML, because
python-pptx has no animation API.

Figures and the QR code come from make_figures.py; run that first.

Run from the repository root:
uv run --with python-pptx python 03_workshop/261102-llm-wiki/components/S1.1-input/make_slides.py

Template path: env TEMPLATE_PPTX, else ~/Presentations/Template/202608_AISC-Template_Light.pptx
"""

from __future__ import annotations

import copy
import itertools
import math
import os
from pathlib import Path

from lxml import etree
from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.dml import MSO_LINE_DASH_STYLE
from pptx.enum.shapes import MSO_CONNECTOR, MSO_SHAPE, PP_PLACEHOLDER
from pptx.enum.text import MSO_ANCHOR, MSO_AUTO_SIZE, PP_ALIGN
from pptx.oxml.ns import qn
from pptx.util import Inches, Pt

HERE = Path(__file__).resolve().parent
SESSION = HERE.parents[1]
ASSETS = HERE / "assets"
TEAM = ASSETS / "team"
TEMPLATE = Path(
    os.environ.get(
        "TEMPLATE_PPTX",
        Path.home() / "Presentations" / "Template" / "202608_AISC-Template_Light.pptx",
    )
)
OUT = SESSION / "llm-wiki_intro.pptx"

README_URL = (
    "https://github.com/aihpi/workshop-rag-forum/tree/main/03_workshop/261102-llm-wiki"
)
README_SHORT = README_URL.removeprefix("https://")
GIST_URL = "https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f"
STARMORPH_URL = "https://blog.starmorph.com/blog/karpathy-llm-wiki-knowledge-base-guide"

# HPI corporate design tokens
INK = RGBColor(0x21, 0x24, 0x27)
GREY = RGBColor(0x5A, 0x60, 0x65)
MID = RGBColor(0x83, 0x88, 0x8C)
LIGHT = RGBColor(0xAC, 0xB0, 0xB2)
RULE = RGBColor(0xD6, 0xD7, 0xD8)
RED = RGBColor(0xB1, 0x06, 0x3A)
NOTE = RGBColor(0xFD, 0xE9, 0xBF)
WHITE = RGBColor(0xFF, 0xFF, 0xFF)

BODY_FONT = "+mn-lt"  # theme body font of the template (Verdana)
MONO_FONT = "Courier New"

# Layout names in the AISC Light template
L_TITLE = "Titelfolie"
L_CONTENT = "Inhalt 1 - rot"  # dark grey corner, used for the main part
L_APPENDIX = "Inhalt 1 - grün"  # light grey corner, used for the appendix
L_DIVIDER = "Zwischentitel - dunkel"

X0, W = 0.77, 12.1  # left edge and width of the content area (inches)
TITLE_PT = 28


# ------------------------------------------------------------------ helpers
def layout(prs: Presentation, name: str):
    for lay in prs.slide_layouts:
        if lay.name == name:
            return lay
    raise KeyError(name)


def clear_slides(prs: Presentation) -> None:
    lst = prs.slides._sldIdLst
    for sld_id in list(lst):
        prs.part.drop_rel(sld_id.get(qn("r:id")))
        lst.remove(sld_id)


def drop_placeholders(slide, keep: tuple[int, ...] = (0,)) -> None:
    for ph in list(slide.placeholders):
        if ph.placeholder_format.idx not in keep:
            ph._element.getparent().remove(ph._element)


def add_slide_number(slide) -> None:
    """Copy the layout's slide-number placeholder onto the slide."""
    for ph in slide.slide_layout.placeholders:
        if ph.placeholder_format.type == PP_PLACEHOLDER.SLIDE_NUMBER:
            el = copy.deepcopy(ph._element)
            ids = [int(e.get("id")) for e in slide._element.iter(qn("p:cNvPr"))]
            el.find(".//" + qn("p:cNvPr")).set("id", str(max(ids, default=1) + 1))
            slide.shapes._spTree.append(el)
            return


def unstyle(shape) -> None:
    """Drop the theme style reference (it brings the template's drop shadow)."""
    style = shape._element.find(qn("p:style"))
    if style is not None:
        shape._element.remove(style)


def link(run, url: str) -> None:
    """Hyperlink that keeps the run colour (Office 2019+) instead of the theme's yellow."""
    run.hyperlink.address = url
    click = run._r.find(qn("a:rPr")).find(qn("a:hlinkClick"))
    ext_lst = etree.SubElement(click, qn("a:extLst"))
    ext = etree.SubElement(ext_lst, qn("a:ext"))
    ext.set("uri", "{A12FA001-AC4F-418D-AE19-62706E023703}")
    ns = "http://schemas.microsoft.com/office/drawing/2018/hyperlinkcolor"
    etree.SubElement(ext, f"{{{ns}}}hlinkClr", nsmap={"ahyp": ns}).set("val", "tx")


def set_bullet(p) -> None:
    pPr = p._p.get_or_add_pPr()
    indent = Inches(0.32)
    pPr.set("marL", str(int(indent)))
    pPr.set("indent", str(-int(indent)))
    for tag in (
        "a:buClr",
        "a:buFont",
        "a:buNone",
        "a:buChar",
        "a:buAutoNum",
        "a:buSzPct",
    ):
        for el in pPr.findall(qn(tag)):
            pPr.remove(el)
    clr = etree.SubElement(pPr, qn("a:buClr"))
    etree.SubElement(clr, qn("a:srgbClr")).set("val", "5A6065")
    etree.SubElement(pPr, qn("a:buFont")).set("typeface", "Arial")
    etree.SubElement(pPr, qn("a:buChar")).set("char", "•")


def fill(
    tf,
    paras,
    *,
    size=18,
    color=INK,
    bold=False,
    align=PP_ALIGN.LEFT,
    font=BODY_FONT,
    bullets=False,
    space_after=6,
    line_spacing=None,
) -> None:
    """Write paragraphs into a text frame.

    A paragraph is a str, a list of (text, options) runs, or a dict with key "runs"
    plus paragraph options (space_before, space_after, align, bullet).
    """
    for i, para in enumerate(paras):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        popts = {}
        if isinstance(para, dict):
            popts, runs = para, para["runs"]
        elif isinstance(para, str):
            runs = [(para, {})]
        else:
            runs = para
        if isinstance(runs, str):
            runs = [(runs, {})]
        for text, o in runs:
            r = p.add_run()
            r.text = text
            f = r.font
            f.size = Pt(o.get("size", popts.get("size", size)))
            f.bold = o.get("bold", popts.get("bold", bold))
            f.name = o.get("font", font)
            f.color.rgb = o.get("color", popts.get("color", color))
            if "link" in o:
                link(r, o["link"])
        p.alignment = popts.get("align", align)
        p.space_after = Pt(popts.get("space_after", space_after))
        if "space_before" in popts:
            p.space_before = Pt(popts["space_before"])
        if line_spacing:
            p.line_spacing = line_spacing
        if popts.get("bullet", bullets):
            set_bullet(p)


def frame(tf, *, margin=0.0, anchor=MSO_ANCHOR.TOP, wrap=True) -> None:
    tf.word_wrap = wrap
    tf.auto_size = MSO_AUTO_SIZE.NONE
    tf.margin_left = tf.margin_right = Inches(margin)
    tf.margin_top = tf.margin_bottom = Inches(margin / 2)
    tf.vertical_anchor = anchor


def text(shapes, x, y, w, h, paras, *, margin=0.0, anchor=MSO_ANCHOR.TOP, **kw):
    box = shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    frame(box.text_frame, margin=margin, anchor=anchor)
    fill(box.text_frame, paras, **kw)
    return box


def box(
    shapes,
    x,
    y,
    w,
    h,
    *,
    fill_rgb=None,
    line=None,
    line_w=1.0,
    dash=None,
    shape=MSO_SHAPE.RECTANGLE,
    radius=0.04,
    paras=None,
    margin=0.12,
    anchor=MSO_ANCHOR.MIDDLE,
    **kw,
):
    shp = shapes.add_shape(shape, Inches(x), Inches(y), Inches(w), Inches(h))
    unstyle(shp)
    if shape == MSO_SHAPE.ROUNDED_RECTANGLE:
        shp.adjustments[0] = radius
    if fill_rgb is None:
        shp.fill.background()
    else:
        shp.fill.solid()
        shp.fill.fore_color.rgb = fill_rgb
    if line is None:
        shp.line.fill.background()
    else:
        shp.line.color.rgb = line
        shp.line.width = Pt(line_w)
        if dash:
            shp.line.dash_style = dash
    shp.shadow.inherit = False
    frame(shp.text_frame, margin=margin, anchor=anchor)
    if paras:
        fill(shp.text_frame, paras, **kw)
    return shp


def line(shapes, x1, y1, x2, y2, *, color=GREY, width=1.0, arrow=False):
    c = shapes.add_connector(
        MSO_CONNECTOR.STRAIGHT, Inches(x1), Inches(y1), Inches(x2), Inches(y2)
    )
    unstyle(c)
    c.line.color.rgb = color
    c.line.width = Pt(width)
    if arrow:
        tail = etree.SubElement(c.line._get_or_add_ln(), qn("a:tailEnd"))
        tail.set("type", "triangle")
        tail.set("w", "med")
        tail.set("len", "med")
    return c


def picture(shapes, path: Path, x, y, w=None, h=None):
    return shapes.add_picture(
        str(path),
        Inches(x),
        Inches(y),
        Inches(w) if w else None,
        Inches(h) if h else None,
    )


def set_cell_borders(cell, sides: dict[str, tuple[str, float]]) -> None:
    """sides maps L/R/T/B to (hex colour, width in pt); missing sides get no line."""
    tcPr = cell._tc.get_or_add_tcPr()
    for tag in ("a:lnL", "a:lnR", "a:lnT", "a:lnB"):
        for el in tcPr.findall(qn(tag)):
            tcPr.remove(el)
    for k, (tag, key) in enumerate(
        (("a:lnL", "L"), ("a:lnR", "R"), ("a:lnT", "T"), ("a:lnB", "B"))
    ):
        ln = etree.Element(qn(tag))
        spec = sides.get(key)
        if spec:
            ln.set("w", str(int(Pt(spec[1]))))
            sf = etree.SubElement(ln, qn("a:solidFill"))
            etree.SubElement(sf, qn("a:srgbClr")).set("val", spec[0])
        else:
            ln.set("w", "0")
            etree.SubElement(ln, qn("a:noFill"))
        tcPr.insert(k, ln)


def table(
    shapes,
    x,
    y,
    col_w,
    rows,
    *,
    row_h=None,
    size=16,
    header=True,
    header_color=GREY,
    first_col_bold=False,
    accent_col=None,
):
    """rows: list of rows; each cell is a str or a paragraph list for fill()."""
    gf = shapes.add_table(
        len(rows),
        len(col_w),
        Inches(x),
        Inches(y),
        Inches(sum(col_w)),
        Inches(0.4 * len(rows)),
    )
    tbl = gf.table
    tblPr = tbl._tbl.tblPr
    tblPr.set("firstRow", "0")
    tblPr.set("bandRow", "0")
    sid = tblPr.find(qn("a:tableStyleId"))
    if sid is None:
        sid = etree.SubElement(tblPr, qn("a:tableStyleId"))
    sid.text = "{2D5ABB26-0587-4C30-8999-92F81FD0307C}"  # No Style, No Grid
    for j, cw in enumerate(col_w):
        tbl.columns[j].width = Inches(cw)
    for i, row in enumerate(rows):
        if row_h:
            tbl.rows[i].height = Inches(row_h[i])
        for j, val in enumerate(row):
            cell = tbl.cell(i, j)
            cell.fill.background()
            cell.margin_left = Inches(0.1 if j else 0.0)
            cell.margin_right = Inches(0.1)
            cell.margin_top = Inches(0.08)
            cell.margin_bottom = Inches(0.08)
            cell.vertical_anchor = MSO_ANCHOR.TOP
            cell.text_frame.word_wrap = True
            paras = [val] if isinstance(val, str) else val
            is_head = header and i == 0
            colour = header_color if is_head else INK
            if is_head and accent_col is not None and j == accent_col:
                colour = RED
            fill(
                cell.text_frame,
                paras,
                size=size,
                color=colour,
                bold=is_head or (first_col_bold and j == 0),
                space_after=2,
            )
            rule = ("D6D7D8", 1.0)
            if is_head:
                rule = ("B1063A", 2.0) if j == accent_col else ("5A6065", 1.0)
            set_cell_borders(cell, {"B": rule})
    return gf


def notes(slide, body: str, checkpoint: str | None) -> None:
    txt = body if not checkpoint else f"{body}\n\nCheckpoint: {checkpoint}"
    slide.notes_slide.notes_text_frame.text = txt


def content_slide(prs, title: str, *, appendix=False):
    slide = prs.slides.add_slide(layout(prs, L_APPENDIX if appendix else L_CONTENT))
    drop_placeholders(slide)
    t = slide.shapes.title
    t.left, t.top, t.width, t.height = (
        Inches(X0),
        Inches(0.18),
        Inches(10.3),
        Inches(0.97),
    )
    p = t.text_frame.paragraphs[0]
    p.line_spacing = 1.0
    r = p.add_run()
    r.text = title
    r.font.size = Pt(TITLE_PT)
    add_slide_number(slide)
    return slide


def add_click_builds(slide, shape_ids: list[int]) -> None:
    """One 'appear' entrance per click, in the given order."""
    ids = itertools.count(3)
    clicks = []
    for spid in shape_ids:
        a, b, c, d = next(ids), next(ids), next(ids), next(ids)
        clicks.append(
            f'<p:par><p:cTn id="{a}" fill="hold"><p:stCondLst><p:cond delay="indefinite"/>'
            f'</p:stCondLst><p:childTnLst><p:par><p:cTn id="{b}" fill="hold"><p:stCondLst>'
            f'<p:cond delay="0"/></p:stCondLst><p:childTnLst><p:par><p:cTn id="{c}" presetID="1" '
            f'presetClass="entr" presetSubtype="0" fill="hold" grpId="0" nodeType="clickEffect">'
            f'<p:stCondLst><p:cond delay="0"/></p:stCondLst><p:childTnLst><p:set><p:cBhvr>'
            f'<p:cTn id="{d}" dur="1" fill="hold"><p:stCondLst><p:cond delay="0"/></p:stCondLst>'
            f'</p:cTn><p:tgtEl><p:spTgt spid="{spid}"/></p:tgtEl><p:attrNameLst>'
            f"<p:attrName>style.visibility</p:attrName></p:attrNameLst></p:cBhvr><p:to>"
            f'<p:strVal val="visible"/></p:to></p:set></p:childTnLst></p:cTn></p:par>'
            f"</p:childTnLst></p:cTn></p:par></p:childTnLst></p:cTn></p:par>"
        )
    ns = "http://schemas.openxmlformats.org/presentationml/2006/main"
    xml = (
        f'<p:timing xmlns:p="{ns}"><p:tnLst><p:par><p:cTn id="1" dur="indefinite" '
        f'restart="never" nodeType="tmRoot"><p:childTnLst><p:seq concurrent="1" nextAc="seek">'
        f'<p:cTn id="2" dur="indefinite" nodeType="mainSeq"><p:childTnLst>{"".join(clicks)}'
        f'</p:childTnLst></p:cTn><p:prevCondLst><p:cond evt="onPrev" delay="0"><p:tgtEl>'
        f'<p:sldTgt/></p:tgtEl></p:cond></p:prevCondLst><p:nextCondLst><p:cond evt="onNext" '
        f'delay="0"><p:tgtEl><p:sldTgt/></p:tgtEl></p:cond></p:nextCondLst></p:seq>'
        f"</p:childTnLst></p:cTn></p:par></p:tnLst></p:timing>"
    )
    slide._element.find(qn("p:clrMapOvr")).addnext(etree.fromstring(xml))


# ------------------------------------------------------------------- slides
def s01_title(prs) -> None:
    slide = prs.slides.add_slide(layout(prs, L_TITLE))
    drop_placeholders(slide, keep=(0, 1))
    t = slide.shapes.title
    t.left, t.top, t.width, t.height = (
        Inches(1.11),
        Inches(0.9),
        Inches(9.2),
        Inches(1.55),
    )
    r = t.text_frame.paragraphs[0].add_run()
    r.text = "Das KISZ-Wiki: Wissen verdichten statt suchen"
    sub = slide.placeholders[1]
    sub.left, sub.top, sub.width, sub.height = (
        Inches(1.11),
        Inches(2.62),
        Inches(9.2),
        Inches(0.6),
    )
    sub.text_frame.paragraphs[
        0
    ].add_run().text = "Warum wir für das Wissen unseres Teams kein RAG nutzen"
    text(
        slide.shapes,
        1.35,
        3.35,
        7.0,
        0.8,
        [
            "Hanno Müller, KI-Servicezentrum Berlin-Brandenburg",
            "RAG-Forum, 2. November 2026",
        ],
        size=14,
        color=GREY,
        space_after=2,
    )
    notes(
        slide,
        "Ich erzähle Ihnen heute in einem RAG-Forum, warum wir für das Wissen unseres eigenen "
        "Teams kein RAG nutzen, sondern ein Wiki, das eine KI schreibt und wir freigeben. Am Ende "
        "kennen Sie vier Fragen, mit denen Sie das für Ihr eigenes Team entscheiden können.",
        None,
    )


TASKS_CORE = "PoCs bauen, Blueprints ableiten"
TASKS_2 = ["Protokolle schreiben", "Veranstaltungen organisieren", "Workshops geben"]
TASKS_3 = ["Lehre", "Vorträge auf Einladung", "Beratung in Sprechstunden"]


def s02_engineers(prs) -> None:
    slide = content_slide(prs, "Sechs Engineers am KISZ")
    sh = slide.shapes
    d, gap, top = 1.7, 0.38, 2.45
    for i, name in enumerate(["Hanno", "Felix", "Mario", "Paras", "David", "Jill"]):
        x = X0 + i * (d + gap)
        picture(sh, TEAM / f"{name.lower()}.png", x, top, d, d)
        text(
            sh,
            x,
            top + d + 0.08,
            d,
            0.4,
            [name],
            size=16,
            color=GREY,
            align=PP_ALIGN.CENTER,
        )

    def label(group, x, y, w, words, core=False):
        box(
            group.shapes,
            x,
            y,
            w,
            0.55,
            shape=MSO_SHAPE.ROUNDED_RECTANGLE,
            radius=0.08,
            fill_rgb=GREY if core else RULE,
            line=WHITE,
            line_w=1.5,
            paras=[words],
            size=16,
            bold=core,
            color=WHITE if core else INK,
            align=PP_ALIGN.CENTER,
            space_after=0,
            margin=0.08,
        )

    # labels pile up over the portraits; the question band (click 4) leaves them readable
    g1 = sh.add_group_shape()
    label(g1, 1.0, 2.3, 4.6, TASKS_CORE, core=True)
    g2 = sh.add_group_shape()
    label(g2, 6.45, 1.95, 2.95, TASKS_2[0])
    label(g2, 3.0, 1.5, 3.95, TASKS_2[1])
    label(g2, 9.85, 2.4, 2.45, TASKS_2[2])
    g3 = sh.add_group_shape()
    label(g3, 8.4, 4.25, 1.2, TASKS_3[0])
    label(g3, 1.3, 4.75, 3.2, TASKS_3[1])
    label(g3, 4.95, 4.55, 3.6, TASKS_3[2])
    g4 = sh.add_group_shape()
    box(
        g4.shapes,
        1.3,
        3.05,
        10.7,
        1.0,
        fill_rgb=RED,
        paras=["Wie schaffen wir das nebenbei, während wir Engineering machen?"],
        size=24,
        bold=True,
        color=WHITE,
        align=PP_ALIGN.CENTER,
        space_after=0,
        margin=0.2,
    )
    add_click_builds(slide, [g.shape_id for g in (g1, g2, g3, g4)])
    notes(
        slide,
        "Das sind die sechs Engineers des KI-Servicezentrums. [Klick] Unsere wichtigste Aufgabe "
        "ist, mit Partnern Prototypen zu bauen, sogenannte Proofs of Concept, und daraus "
        "Blueprints abzuleiten, also Vorlagen, die andere wiederverwenden können. [Klick] Daneben "
        "schreiben wir Protokolle, organisieren Veranstaltungen wie dieses Forum und geben "
        "Workshops. [Klick] Wir lehren, halten Vorträge auf Einladung und beraten in "
        "Sprechstunden. Jede dieser Aufgaben braucht Informationen, die irgendwo im Team schon "
        "entstanden sind: ein Termin, ein Raum, wer welchen Workshop schon gegeben hat. Oft sind "
        "sie veraltet, wenn man sie findet. [Klick] Die Frage ist also: Wie schaffen wir das "
        "nebenbei, während wir eigentlich Engineering machen?",
        "Kennen Sie das aus Ihrem Team? (rhetorisch, Blick in den Raum)",
    )


def s03_system(prs) -> None:
    slide = content_slide(prs, "Ein System, das uns kennt")
    sh = slide.shapes
    text(
        sh,
        X0,
        1.55,
        4.9,
        3.6,
        [
            {"runs": "Weiß, wie wir arbeiten", "bullet": True},
            {"runs": "Weiß, wer wann welche Information braucht", "bullet": True},
            {"runs": "Weiß, wann diese Information entsteht", "bullet": True},
            {"runs": "Heute:", "bold": True, "space_before": 18, "space_after": 0},
            {"runs": "sein Rückgrat, unser Wiki", "bold": True},
        ],
        size=20,
        space_after=10,
    )
    # ring of the tasks from slide 2 around the wiki
    cx, cy, a, b = 9.35, 3.3, 2.6, 1.72
    labels = [
        (["PoCs bauen,", "Blueprints ableiten"], True),
        (["Protokolle", "schreiben"], False),
        (["Veranstaltungen", "organisieren"], False),
        (["Workshops geben"], False),
        (["Lehre"], False),
        (["Vorträge auf", "Einladung"], False),
        (["Beratung in", "Sprechstunden"], False),
    ]
    lh = 0.62
    centres = []
    for k in range(len(labels)):
        ang = math.radians(-90 + k * 360 / len(labels))
        centres.append((cx + a * math.cos(ang), cy + b * math.sin(ang)))
    for x, y in centres:
        line(sh, x, y, cx, cy, color=LIGHT, width=1.0)
    for (x, y), (words, core) in zip(centres, labels, strict=True):
        lw = 2.4 if core else 1.9
        box(
            sh,
            x - lw / 2,
            y - lh / 2,
            lw,
            lh,
            shape=MSO_SHAPE.ROUNDED_RECTANGLE,
            radius=0.08,
            fill_rgb=GREY if core else RULE,
            paras=words,
            size=13,
            bold=core,
            color=WHITE if core else INK,
            align=PP_ALIGN.CENTER,
            space_after=0,
            margin=0.05,
        )
    box(
        sh,
        cx - 0.8,
        cy - 0.36,
        1.6,
        0.72,
        fill_rgb=INK,
        paras=["Wiki"],
        size=20,
        bold=True,
        color=WHITE,
        align=PP_ALIGN.CENTER,
        space_after=0,
    )
    # route of the evening, proportional to the minutes
    parts = [
        ("20 min Input", 20),
        ("15 min Live-Demo", 15),
        ("30 min Gespräche in Dreiergruppen", 30),
    ]
    x, total, g = X0, sum(m for _, m in parts), 0.06
    for k, (label_txt, mins) in enumerate(parts):
        w = (W - g * 2) * mins / total
        box(
            sh,
            x,
            5.55,
            w,
            0.45,
            fill_rgb=RED if k == 0 else None,
            line=None if k == 0 else LIGHT,
            paras=[label_txt],
            size=14,
            bold=k == 0,
            color=WHITE if k == 0 else INK,
            align=PP_ALIGN.CENTER,
            space_after=0,
            margin=0.05,
        )
        x += w + g
    notes(
        slide,
        "Unsere Antwort ist ein System, das uns kennt. Teile davon sind kleine KI-Assistenten, "
        "zum Beispiel einer, der aus dem Transkript einer Sprechstunde ein Protokoll schreibt, "
        "oder einer, der für einen Workshop Raum, Grafik und Ankündigung anfragt. Alle greifen "
        "auf dasselbe Wissen zu: unser Wiki. Das ganze System kann ich in 20 Minuten nicht "
        "zeigen, nur dieses Rückgrat. Danach zeige ich das Wiki 15 Minuten live, und dann "
        "sprechen Sie in drei kurzen Runden in Dreiergruppen über die Wissensablage Ihres "
        "eigenen Teams.",
        "Ist klar, wohin wir gehen?",
    )


def s04_three_ways(prs) -> None:
    slide = content_slide(prs, "Wie pflegen wir das Rückgrat ohne Overhead?")
    sh = slide.shapes
    cols = [
        (
            "Wiki von Hand",
            ["Menschen schreiben Seiten", "Kostet Zeit", "Seiten veralten"],
        ),
        (
            "RAG",
            [
                "Niemand pflegt",
                "Bei jeder Frage passende Ausschnitte aus den Rohdokumenten suchen",
            ],
        ),
        (
            "LLM-Wiki",
            [
                "KI liest jede Quelle einmal",
                "Schreibt und pflegt Seiten",
                "Menschen geben frei",
            ],
        ),
    ]
    cw, cg, top, ch = 3.75, 0.425, 1.5, 3.4
    for k, (head, items) in enumerate(cols):
        x = X0 + k * (cw + cg)
        accent = k == 2
        box(
            sh,
            x,
            top,
            cw,
            ch,
            shape=MSO_SHAPE.ROUNDED_RECTANGLE,
            radius=0.02,
            line=RED if accent else RULE,
            line_w=1.5 if accent else 1.0,
        )
        text(
            sh,
            x + 0.3,
            top + 0.25,
            cw - 0.6,
            0.5,
            [head],
            size=20,
            bold=True,
            color=RED if accent else INK,
        )
        line(sh, x + 0.3, top + 0.85, x + cw - 0.3, top + 0.85, color=RULE, width=1.0)
        text(
            sh,
            x + 0.3,
            top + 1.05,
            cw - 0.6,
            ch - 1.2,
            items,
            size=17,
            bullets=True,
            space_after=8,
        )
    box(
        sh,
        X0,
        5.2,
        W,
        0.75,
        fill_rgb=NOTE,
        shape=MSO_SHAPE.ROUNDED_RECTANGLE,
        radius=0.05,
        paras=[
            [
                ("Handzeichen: ", {"bold": True}),
                ("Wer hat schon über RAG für die eigene Teamablage nachgedacht?", {}),
            ]
        ],
        size=18,
        space_after=0,
        margin=0.3,
    )
    notes(
        slide,
        "Overhead heißt hier: Arbeit, die niemand neben dem Engineering machen will. Die "
        "klassische Antwort ist ein Wiki, das Menschen von Hand pflegen, etwa in Confluence. Das "
        "kostet genau die Zeit, die wir nicht haben, und die Seiten veralten. In einem RAG-Forum "
        "liegt eine zweite Antwort nahe: gar nicht pflegen. RAG lässt die Dokumente, wie sie "
        "sind, und sucht bei jeder Frage die passenden Ausschnitte heraus. Wer von Ihnen hat "
        "schon über so ein System für die Ablage des eigenen Teams nachgedacht? [Handzeichen] "
        "Für Sie gibt es am Ende vier Fragen, mit denen Sie das entscheiden, und in der zweiten "
        "Gruppenrunde wenden Sie sie an. Wir haben einen dritten Weg gewählt, ein LLM-Wiki. "
        "Eine KI liest jede Quelle einmal und verdichtet sie: Aus vielen Dokumenten wird eine "
        "kurze Seite pro Person, Projekt oder Veranstaltung. Die KI hält diese Seiten aktuell, "
        "und Menschen geben jede Änderung frei. Warum nicht RAG, sage ich Ihnen am Ende; erst "
        "zeige ich, wie das Wiki funktioniert.",
        "Handzeichen (rund 0,5 min)",
    )


def s05_layers(prs) -> None:
    slide = content_slide(prs, "Das KISZ-Wiki: drei Schichten")
    sh = slide.shapes
    picture(sh, ASSETS / "fig-layers.png", X0, 1.45, W, 4.5)
    text(
        sh,
        6.87,
        6.1,
        6.0,
        0.35,
        [[("Idee: Andrej Karpathy, ", {}), ('"LLM Wiki" (2026)', {"link": GIST_URL})]],
        size=12,
        color=GREY,
        align=PP_ALIGN.RIGHT,
        space_after=0,
    )
    notes(
        slide,
        "Die Idee stammt von Andrej Karpathy, Mitgründer von OpenAI, der sie im April 2026 als "
        "LLM-Wiki beschrieben hat. Unser Wiki hat drei Schichten. Unten liegen die Quellen: "
        "Code-Ablagen auf GitHub, Veranstaltungen auf Eventbrite, unsere Homepage, Dokumente in "
        "Nextcloud und Gespräche mit Kolleg:innen. Die KI liest sie, verändert sie aber nie. In "
        "der Mitte liegen rund 140 Seiten in einfachem Text, eine Seite pro Person, Projekt, "
        "Workshop, Veranstaltung und Ablauf. Diese Seiten schreibt die KI, Menschen geben sie "
        "frei, und Menschen lesen sie auch selbst, im Browser wie jede andere Dokumentation. "
        "Oben liegt eine einzige Datei mit Regeln: wie eine Seite aussieht, woher jede Aussage "
        "stammen muss und was nie hineindarf, zum Beispiel Daten von Teilnehmenden. Diese "
        "Regeln schreibt das Team. Kurze Kontrolle: Wer schreibt die Seiten, und wer gibt sie "
        "frei?",
        "Wer schreibt die Seiten, und wer gibt sie frei? (Antwort aus dem Raum: die KI schreibt, "
        "Menschen geben frei)",
    )


def s06_query(prs) -> None:
    slide = content_slide(prs, "So beantwortet die KI eine Frage")
    sh = slide.shapes
    arrow_w = 0.45
    widths = [
        2.95,
        2.6,
        2.6,
        2.6,
    ]  # the question box is wider so "RAG-Forum?" stays whole
    top, bh = 1.5, 1.6
    steps = [
        [
            {"runs": "Frage:", "size": 14, "color": GREY, "space_after": 4},
            {"runs": "Wann und wo ist das nächste", "bold": True, "space_after": 0},
            {"runs": "RAG-Forum?", "bold": True},
        ],
        ["1. Ganzes Inhaltsverzeichnis lesen: eine Zeile pro Seite"],
        ["2. Selbst die passende Seite wählen und ganz lesen"],
        [
            "3. Antworten:",
            {"runs": "2. November 2026, 17:30 Uhr, D-Space", "bold": True},
        ],
    ]
    xs = [X0 + sum(widths[:k]) + k * arrow_w for k in range(4)]
    for k, (x, bw, paras) in enumerate(zip(xs, widths, steps, strict=True)):
        box(
            sh,
            x,
            top,
            bw,
            bh,
            shape=MSO_SHAPE.ROUNDED_RECTANGLE,
            radius=0.04,
            fill_rgb=NOTE if k == 0 else None,
            line=None if k == 0 else LIGHT,
            paras=paras,
            size=16,
            space_after=2,
            margin=0.18,
            anchor=MSO_ANCHOR.MIDDLE,
        )
        if k < 3:
            line(
                sh,
                x + bw + 0.06,
                top + bh / 2,
                x + bw + arrow_w - 0.06,
                top + bh / 2,
                color=GREY,
                width=1.5,
                arrow=True,
            )
    # excerpt of the index: neighbouring lines as grey bars, the real line highlighted
    cx0, cy0, cw, chh = xs[1], 3.55, X0 + W - xs[1], 2.4
    box(
        sh, cx0, cy0, cw, chh, shape=MSO_SHAPE.ROUNDED_RECTANGLE, radius=0.02, line=RULE
    )
    line(
        sh,
        xs[1] + widths[1] / 2,
        top + bh,
        xs[1] + widths[1] / 2,
        cy0,
        color=LIGHT,
        width=1.0,
    )
    for y, frac in ((cy0 + 0.25, 0.72), (cy0 + 0.5, 0.84)):
        box(sh, cx0 + 0.3, y, (cw - 0.6) * frac, 0.12, fill_rgb=RULE)
    box(
        sh,
        cx0 + 0.18,
        cy0 + 0.78,
        cw - 0.36,
        0.82,
        fill_rgb=NOTE,
        line=RED,
        line_w=1.25,
        paras=[
            "events/community/2026-11-02-rag-forum.md:",
            "RAG Forum in German on 2 November 2026 in the D-Space; ...",
        ],
        size=14,
        font=MONO_FONT,
        space_after=0,
        margin=0.12,
    )
    for y, frac in ((cy0 + 1.8, 0.66), (cy0 + 2.05, 0.79)):
        box(sh, cx0 + 0.3, y, (cw - 0.6) * frac, 0.12, fill_rgb=RULE)
    notes(
        slide,
        "Fragt jemand das Wiki, liest die KI zuerst das ganze Inhaltsverzeichnis, eine Zeile "
        'pro Seite. Für die Frage "Wann und wo ist das nächste RAG-Forum?" findet sie dort '
        "diese Zeile, öffnet die eine Seite und antwortet: heute, 17:30 Uhr, im D-Space. Der "
        "Unterschied zu RAG: Bei RAG wählt eine Suche Ausschnitte aus, bevor das Modell "
        "irgendetwas sieht. Hier sieht das Modell das ganze Inhaltsverzeichnis und entscheidet "
        "selbst, welche ganze, freigegebene Seite es liest. Die Zeile ist übrigens englisch, "
        "weil das Wiki auf Englisch geschrieben ist.",
        "Wer hat entschieden, welche Seite gelesen wird? (Antwort: die KI selbst, nach dem "
        "ganzen Inhaltsverzeichnis; bei RAG eine Suche vorab)",
    )


def s07_cycle(prs) -> None:
    slide = content_slide(prs, "Wie Neues hineinkommt")
    sh = slide.shapes
    picture(sh, ASSETS / "fig-cycle.png", X0, 1.4, 8.3, 4.6)
    box(
        sh,
        9.45,
        2.7,
        X0 + W - 9.45,
        1.9,
        fill_rgb=NOTE,
        shape=MSO_SHAPE.ROUNDED_RECTANGLE,
        radius=0.04,
        paras=[
            {"runs": "Unsere Arbeit:", "color": GREY, "size": 18},
            {"runs": "Quellen geben und freigeben, nicht schreiben", "bold": True},
        ],
        size=20,
        space_after=4,
        margin=0.25,
    )
    notes(
        slide,
        "So kommt Neues ins Wiki. Jemand aus dem Team gibt der KI eine Quelle, zum Beispiel den "
        "Link zu einer neuen Veranstaltung auf Eventbrite, oder sagt nach einem Gespräch einfach "
        '"ins Wiki". Die KI liest die Quelle, zeigt, welche Seiten sich ändern würden, und fragt '
        "einmal nach, ob sie weitermachen soll. Dann schreibt sie den Entwurf. Was die Quelle "
        "nicht hergibt oder was einer anderen Quelle widerspricht, rät sie nicht. Beim ersten "
        "RAG-Forum nannte Eventbrite den 15. Juni, unser Ordner in Nextcloud den 15. Mai; die KI "
        "hat den Widerspruch notiert, statt ein Datum zu wählen, und ich habe den Ordner "
        "korrigiert. Jede Änderung ist ein Änderungsvorschlag, in der Softwareentwicklung heißt "
        "das Merge Request. Erst wenn ein Mensch freigibt, steht die Änderung im Wiki. Unsere "
        "Arbeit ist also Quellen geben und freigeben, nicht schreiben.",
        "Welcher Schritt bleibt bei uns Menschen? (Antwort: Quellen geben und freigeben)",
    )


def s08_maintenance(prs) -> None:
    slide = content_slide(prs, "Wie das Wiki aktuell bleibt")
    sh = slide.shapes
    text(
        sh,
        X0,
        1.6,
        5.6,
        4.2,
        [
            "Alle zwei Wochen: KI bietet eine Wartungssitzung an",
            "KI sucht Widersprüche zwischen Seiten, Lücken, doppelten Text",
            "Ein Befund pro Frage, mit Beleg; ein Mensch entscheidet",
        ],
        size=20,
        bullets=True,
        space_after=16,
    )
    # finding card
    x, y, w, h = 6.85, 1.45, X0 + W - 6.85, 4.55
    box(
        sh,
        x,
        y,
        w,
        h,
        shape=MSO_SHAPE.ROUNDED_RECTANGLE,
        radius=0.02,
        line=LIGHT,
        line_w=1.0,
    )
    pad = 0.3
    text(
        sh,
        x + pad,
        y + 0.22,
        3.0,
        0.4,
        ["Durchsicht am 9. Oktober"],
        size=14,
        color=GREY,
        space_after=0,
    )
    text(
        sh,
        x + w - pad - 2.6,
        y + 0.18,
        2.6,
        0.4,
        ["Befund 21 von 52"],
        size=16,
        bold=True,
        align=PP_ALIGN.RIGHT,
        space_after=0,
    )
    line(sh, x + pad, y + 0.68, x + w - pad, y + 0.68, color=RULE)
    for k, (tag, claim, where) in enumerate(
        [
            (
                "Seite A",
                "Vorbereitung beginnt, sobald das Material fertig ist.",
                "how-to/README.md:14",
            ),
            (
                "Seite B",
                "Das Material muss nicht fertig sein.",
                "how-to/workshop-preparation.md:8",
            ),
        ]
    ):
        yy = y + 0.85 + k * 1.3
        text(
            sh,
            x + pad,
            yy,
            w - 2 * pad,
            1.2,
            [
                {"runs": tag, "size": 13, "color": GREY, "space_after": 2},
                {"runs": claim, "size": 17, "space_after": 4},
                {"runs": [(where, {"font": MONO_FONT})], "size": 13, "color": GREY},
            ],
            space_after=0,
        )
    text(
        sh,
        x + pad,
        y + 3.42,
        3.0,
        0.3,
        ["Entscheidung"],
        size=13,
        color=GREY,
        space_after=0,
    )
    box(
        sh,
        x + pad,
        y + 3.72,
        w - 2 * pad,
        0.55,
        line=RED,
        line_w=1.25,
        dash=MSO_LINE_DASH_STYLE.DASH,
    )
    notes(
        slide,
        "Auch Wiki-Seiten veralten oder widersprechen sich. Alle zwei Wochen bietet die KI, wenn "
        "jemand aus dem Team mit ihr zu arbeiten beginnt, eine Wartungssitzung an. Sie sucht "
        "Widersprüche zwischen Seiten, Lücken und doppelten Text und legt jeden Befund einzeln "
        "vor, mit der Stelle, an der sie ihn gefunden hat. Entscheiden muss ein Mensch. Bei der "
        "ersten Durchsicht am 9. Oktober kamen 52 Befunde zusammen. Einer davon: Eine Seite "
        "sagt, die Vorbereitung eines Workshops beginnt, sobald das Material fertig ist; eine "
        "andere sagt, das Material muss dafür nicht fertig sein. Welche stimmt, weiß nur das "
        "Team.",
        "Wer entscheidet, was stimmt? (Antwort: ein Mensch)",
    )


def s09_triggers(prs) -> None:
    slide = content_slide(prs, "Was das Wiki anstößt")
    sh = slide.shapes
    rows = [
        ("Jede freigegebene Änderung", "Zusammenfassung in Slack", "automatisch"),
        (
            "Offene Fragen",
            "To-dos mit Namen; einmal im Monat Erinnerung",
            "automatisch",
        ),
        (
            "Alle zwei Wochen",
            "KI schlägt Seiten für neue Code-Ablagen vor",
            "automatisch",
        ),
        (
            "Auf Zuruf",
            "Anfrage an die Öffentlichkeitsarbeit, mit Angaben aus dem Wiki",
            "auf Zuruf",
        ),
    ]
    top, rh = 1.6, 1.0
    line(sh, X0, top, X0 + W, top, color=RULE)
    for k, (trigger, action, mark) in enumerate(rows):
        y = top + k * rh
        text(
            sh,
            X0,
            y,
            4.1,
            rh,
            [trigger],
            size=19,
            anchor=MSO_ANCHOR.MIDDLE,
            space_after=0,
        )
        line(sh, 4.95, y + rh / 2, 5.6, y + rh / 2, color=GREY, width=1.5, arrow=True)
        text(
            sh,
            5.8,
            y,
            5.2,
            rh,
            [action],
            size=19,
            anchor=MSO_ANCHOR.MIDDLE,
            space_after=0,
        )
        text(
            sh,
            11.1,
            y,
            X0 + W - 11.1,
            rh,
            [mark],
            size=13,
            color=RED if mark == "auf Zuruf" else GREY,
            align=PP_ALIGN.RIGHT,
            anchor=MSO_ANCHOR.MIDDLE,
            space_after=0,
        )
        line(sh, X0, y + rh, X0 + W, y + rh, color=RULE)
    notes(
        slide,
        "Weil jede Änderung als Änderungsvorschlag durch dieselbe Stelle läuft, kann das Wiki "
        "auch etwas anstoßen. Nach jeder freigegebenen Änderung fasst eine KI automatisch "
        "zusammen, was sich geändert hat, und schreibt es in einen Slack-Kanal des Teams. Jede "
        "offene Frage aus dem Entwurf wird ein To-do mit Namen, und einmal im Monat erinnert die "
        "KI jede Person an ihre To-dos, wenn sie mit ihr zu arbeiten beginnt. Alle zwei Wochen "
        "schlägt sie Seiten für neue Code-Ablagen auf GitHub vor. Und auf Zuruf schreibt sie mit "
        "den Angaben aus dem Wiki die Anfrage an unsere Öffentlichkeitsarbeit, so wie für dieses "
        "Forum. Auch diesen Vortrag habe ich mit dem Wiki geplant: Datum, Raum und frühere "
        "Teilnehmerzahlen kamen von dort.",
        'rhetorisch ("Welchen davon gäbe es bei Ihnen auch? Darüber sprechen Sie in Runde 3.")',
    )


def s10_why_not_rag(prs) -> None:
    slide = content_slide(prs, "Warum kein RAG?")
    sh = slide.shapes
    text(
        sh,
        X0,
        1.55,
        W,
        2.4,
        [
            "Sprachmodell liest pro Anfrage begrenzt viel Text: das Kontextfenster",
            "Inhaltsverzeichnis: rund 8.000 Tokens",
            "gpt-oss-120b, am HPI selbst gehostet: 128.000 Tokens pro Anfrage",
            [("Belegt: rund 6 %, keine Suche nötig", {"bold": True})],
        ],
        size=20,
        bullets=True,
        space_after=10,
    )
    picture(sh, ASSETS / "fig-context-window.png", X0, 3.95, W, 1.45)
    notes(
        slide,
        "Zurück zur Frage vom Anfang: Warum kein RAG? Ein Sprachmodell liest pro Anfrage nur "
        "eine begrenzte Menge Text, das sogenannte Kontextfenster. RAG sucht Ausschnitte heraus, "
        "weil die Dokumente nicht ganz hineinpassen. Unser Inhaltsverzeichnis umfasst rund "
        "8.000 Tokens, also Wortstücke. Wir arbeiten mit Claude, einem Modell in der Cloud; aber "
        "selbst gpt-oss-120b, ein offenes Modell, das wir am HPI selbst betreiben, liest "
        "128.000 Tokens pro Anfrage. Das zählt für alle, die ihre Daten nicht in eine Cloud "
        "geben dürfen. Das Inhaltsverzeichnis belegt davon rund 6 Prozent; die KI muss nicht "
        "suchen, sie liest. Dazu kommt, was Sie gerade gesehen haben: Die Seiten sind "
        "freigegeben, zeigen den aktuellen Stand, und Widersprüche fallen auf, statt im "
        "Suchergebnis unterzugehen.",
        "Was müsste passieren, damit das nicht mehr reicht?",
    )


def s11_where_rag_wins(prs) -> None:
    slide = content_slide(prs, "Wo RAG gewinnt")
    sh = slide.shapes
    text(
        sh,
        X0,
        1.5,
        W,
        2.2,
        [
            "10x Seiten: Inhaltsverzeichnis rund 80.000 Tokens, knapp zwei Drittel des Fensters",
            "20x Seiten: passt nicht mehr; nötig wären riesige Kontextfenster, lokal kaum zu "
            "betreiben",
            "Täglich viel Neues: eine Handvoll Menschen gibt nicht mehr alles frei",
            [("RAG liest nur passende Ausschnitte und wächst mit", {"bold": True})],
        ],
        size=18,
        bullets=True,
        space_after=8,
    )
    picture(sh, ASSETS / "fig-context-scale.png", X0, 3.6, W, 2.55)
    notes(
        slide,
        "Genau hier gewinnt RAG. Jede Seite kostet im Inhaltsverzeichnis rund 60 Tokens. Bei "
        "zehnmal so vielen Seiten belegt es rund 80.000 Tokens, knapp zwei Drittel des "
        "Fensters, bevor die KI eine einzige Seite geöffnet hat. Bei zwanzigmal so vielen passt "
        "es gar nicht mehr hinein. Dann braucht das Wiki Modelle mit riesigem Kontextfenster, "
        "und die lassen sich lokal kaum betreiben. Die zweite Grenze sind wir selbst: Kommt "
        "täglich viel Neues hinzu, kann eine Handvoll Menschen nicht mehr jede Änderung "
        "freigeben. RAG liest dagegen immer nur die passenden Ausschnitte und braucht keine "
        "Freigabe pro Dokument; es wächst mit. Rechnerisch reicht unser Fenster für rund 1.000 "
        "Seiten; Erfahrungsberichte aus der Community sehen erste Grenzen schon ab 100 bis 200 "
        "Seiten, und da liegen wir mit rund 140.",
        "Wo steht Ihr Team: eher bei 1x oder bei 20x?",
    )


def s12_four_questions(prs) -> None:
    slide = content_slide(prs, "Wiki oder RAG? Vier Fragen")
    sh = slide.shapes
    rows = [
        ["", "Wiki", "RAG"],
        [
            [
                {"runs": "Passt es?", "bold": True, "size": 16},
                "Umfang (wie viele Seiten: Personen, Projekte, Termine, Abläufe) gegen Hosting "
                "(Fenster des Modells, das Sie nutzen dürfen)",
            ],
            "einige hundert Seiten (rechnerisch bis rund 1.000 bei 128.000 Tokens)",
            "tausende Seiten",
        ],
        [
            [
                {"runs": "Schaffen wir es?", "bold": True, "size": 16},
                "Zufluss (Neues pro Woche) gegen Prüfende (Menschen, die freigeben)",
            ],
            "eine Handvoll schafft es nebenbei",
            "täglich mehr, als sie freigeben können",
        ],
    ]
    table(
        sh,
        X0,
        1.4,
        [5.9, 3.3, 2.9],
        rows,
        row_h=[0.5, 1.2, 0.95],
        size=15,
        accent_col=1,
    )
    box(
        sh,
        X0,
        4.3,
        9.85,
        1.65,
        fill_rgb=NOTE,
        shape=MSO_SHAPE.ROUNDED_RECTANGLE,
        radius=0.04,
        paras=[
            [("Faustregel: ", {"bold": True}), ("Beide Paare gehen auf: Wiki.", {})],
            "Eins geht nicht auf: RAG, oder ein Wiki für den kleinen Kern und RAG für die Masse "
            "(z. B. Projektseiten als Wiki, das Archiv aller Protokolle über RAG).",
        ],
        size=16,
        space_after=4,
        margin=0.25,
        anchor=MSO_ANCHOR.MIDDLE,
    )
    picture(sh, ASSETS / "qr-readme.png", 11.07, 4.3, 1.65, 1.65)
    text(
        sh,
        5.0,
        6.05,
        X0 + W - 5.0,
        0.3,
        [[(README_SHORT, {"link": README_URL})]],
        size=10,
        color=GREY,
        align=PP_ALIGN.RIGHT,
        space_after=0,
    )
    notes(
        slide,
        "Ob das für Ihr Team gilt, entscheiden vier Fragen, die paarweise zusammengehören. Das "
        "erste Paar fragt, ob es passt: Wie viele Seiten würde Ihr Wiki haben, eine pro Person, "
        "Projekt, Termin oder Ablauf, und welches Modell dürfen Sie nutzen? Mit einem selbst "
        "gehosteten Modell wie unserem reicht es für einige hundert Seiten. Das zweite Paar "
        "fragt, ob Sie es schaffen: Wie viel Neues kommt pro Woche hinzu, und wie viele Menschen "
        "geben frei? Gehen beide Paare auf, nehmen Sie das Wiki. Geht eins nicht auf, nehmen Sie "
        "RAG, oder ein Wiki für den kleinen Kern und RAG für die Masse. Kurz gesagt: RAG liest "
        "bei jeder Frage die Rohdokumente neu; ein Wiki verdichtet sie einmal, Menschen geben "
        "frei, und die KI hält es aktuell. Das Wiki gewinnt, solange wenige Dokumente langsam "
        "wachsen. Die vier Fragen brauchen Sie gleich in den Gruppenrunden; der QR-Code führt zu "
        "einer Seite mit allem zum Nachlesen. Vorher zeige ich Ihnen live, wie viel Arbeit die "
        "Pflege im Alltag ist.",
        "Können Sie die vier Fragen für Ihr Team beantworten? (Antwort folgt in S1.3)",
    )


# ----------------------------------------------------------------- appendix
def divider(prs) -> None:
    slide = prs.slides.add_slide(layout(prs, L_DIVIDER))
    drop_placeholders(slide)
    slide.shapes.title.text_frame.paragraphs[0].add_run().text = "Anhang"


def x_list(prs, title, items, note) -> None:
    slide = content_slide(prs, title, appendix=True)
    text(slide.shapes, X0, 1.6, W, 4.3, items, size=20, bullets=True, space_after=14)
    notes(slide, note, None)


def x_table(prs, title, rows, col_w, note, size=18) -> None:
    slide = content_slide(prs, title, appendix=True)
    table(
        slide.shapes, X0, 1.6, col_w, rows, size=size, header=False, first_col_bold=True
    )
    notes(slide, note, None)


def x6_reading(prs) -> None:
    slide = content_slide(prs, "Zum Nachlesen", appendix=True)
    entries = [
        ("Andrej Karpathy, LLM Wiki:", GIST_URL),
        ("Überblick:", STARMORPH_URL),
        ("README dieser Sitzung mit den vier Fragen und den Folien", README_URL),
    ]
    paras = []
    for label_txt, url in entries:
        paras.append({"runs": label_txt, "size": 20, "space_after": 4})
        paras.append(
            {
                "runs": [(url, {"link": url})],
                "size": 14,
                "color": GREY,
                "space_after": 26,
            }
        )
    text(slide.shapes, X0, 1.6, 9.9, 4.4, paras)
    picture(slide.shapes, ASSETS / "qr-readme.png", 11.0, 4.0, 1.85, 1.85)
    slide.notes_slide.notes_text_frame.text = ""


def x7_community(prs) -> None:
    slide = content_slide(prs, "Umsetzungen aus der Community", appendix=True)
    projects = [
        (
            "llmwiki",
            "Dokumente hochladen, Claude über MCP verbinden, Wiki schreiben lassen",
            "github.com/lucasastorian/llmwiki",
        ),
        (
            "obsidian-wiki",
            "Rahmen für KI-Agenten, die Obsidian-Wikis nach Karpathys Muster bauen",
            "github.com/Ar9av/obsidian-wiki",
        ),
        (
            "second-brain",
            "von einem LLM gepflegte persönliche Wissensbasis für Obsidian",
            "github.com/NicholasSpisak/second-brain",
        ),
        (
            "llm-wiki-compiler",
            "verdichtet Markdown-Dateien zu Wikis nach Themen",
            "github.com/ussumant/llm-wiki-compiler",
        ),
        (
            "CacheZero",
            "das Muster als ein npm-Paket",
            "news.ycombinator.com/item?id=47667723",
        ),
        (
            "wiki-skills",
            "Claude-Code-Skills für das Muster",
            "github.com/kfchou/wiki-skills",
        ),
        (
            "LLM Wiki v2",
            "erweitertes Muster mit Gedächtnis-Lebenszyklus und Vertrauenswerten",
            "gist.github.com/rohitg00/2067ab416f7bbe447c1977edaaa681e2",
        ),
    ]
    rows = [["Projekt", "Beschreibung", "Link"]]
    for name, desc, link in projects:
        rows.append(
            [name, desc, [[(link, {"link": "https://" + link, "color": GREY})]]]
        )
    table(slide.shapes, X0, 1.4, [2.0, 4.3, 5.8], rows, size=12, first_col_bold=True)
    text(
        slide.shapes,
        4.0,
        6.1,
        X0 + W - 4.0,
        0.3,
        [
            [
                ("Quelle: Starmorph, ", {}),
                ('"How to Build Karpathy\'s LLM Wiki"', {"link": STARMORPH_URL}),
                (", 2026-04-09", {}),
            ]
        ],
        size=11,
        color=GREY,
        align=PP_ALIGN.RIGHT,
        space_after=0,
    )
    notes(
        slide,
        "Für Rückfragen: Unser Wiki ist eine eigene Umsetzung mit Claude Code, GitLab und einer "
        "Regeldatei; LLM Wiki v2 hat wie wir Vertrauenswerte.",
        None,
    )


def appendix(prs) -> None:
    divider(prs)
    x_list(
        prs,
        "Was ein eigenes Wiki braucht",
        [
            "Git-Repository mit Änderungsvorschlägen (bei uns GitLab)",
            "KI-Assistent mit Dateizugriff (bei uns Claude Code)",
            "Eine Regeldatei",
            "Ein Prüfskript für Pflichtfelder und Datenschutz",
            "Quellen bleiben, wo sie sind (Nextcloud, Confluence)",
        ],
        "Für Rückfragen in S1.2.",
    )
    x_table(
        prs,
        "Freigabe und Bestätigung",
        [
            ["Freigabe", "ein Mensch stimmt einer Änderung zu"],
            [
                "Bestätigung",
                "die Person, um deren Seite es geht, bestätigt den Inhalt (Stempel "
                "mit Datum, Name, Prüfsumme)",
            ],
            ["Status", "bestätigt, nach Bestätigung geändert, unbestätigt"],
            [
                "Vertrauen",
                "Punkte für Quellen und Bestätigung, Abzug für Alter und offene Fragen",
            ],
        ],
        [3.0, 9.1],
        "Freigeben und bestätigen sind zwei Dinge: Eine Änderung kann freigegeben sein, ohne "
        "dass die zuständige Person den Inhalt bestätigt hat. Die Prüfsumme ist ein "
        "Fingerabdruck des Seitentexts; ändert sich ein Zeichen, passt sie nicht mehr. "
        "Vertrauen wird berechnet, nie von Hand gesetzt.",
    )
    x_list(
        prs,
        "Automatische Prüfungen bei jedem Änderungsvorschlag",
        [
            "Inhaltsverzeichnis aktuell",
            "Pflichtfelder vorhanden",
            "Links lösen auf",
            "Keine Mailadressen oder Telefonnummern",
            "Stempel nur von der Person, die bestätigt hat",
        ],
        "Diese Prüfungen laufen in der CI von GitLab (wiki.py index --check, people --check, "
        "lint, privacy, reviewers).",
    )
    x_table(
        prs,
        "Wer darf was ändern",
        [
            ["Frei", "neue Seiten, Themenseiten"],
            ["Nach Ja", "Änderungen an bestehenden Seiten und Personenseiten"],
            [
                "Nur auf eigenes Wort",
                "Arbeitsweise und Ansprache auf der eigenen Personenseite",
            ],
        ],
        [3.6, 8.5],
        "Die Stufen stehen in der Regeldatei; jede Änderung landet trotzdem nur über einen "
        "freigegebenen Änderungsvorschlag im Wiki.",
    )
    x_list(
        prs,
        "Was nie ins Wiki kommt",
        [
            "Daten von Teilnehmenden",
            "Private Mailadressen und Telefonnummern",
            "Bewertungen von Kolleg:innen",
            "Als vertraulich markierte Details",
            "Alles, was eine Person aus einer Sprechstunde erkennbar macht",
        ],
        "Ein Prüfskript lässt jeden Änderungsvorschlag scheitern, der Mailadressen oder "
        "Telefonnummern enthält; der Rest ist Regel für die KI und Prüfpunkt für Menschen.",
    )
    x6_reading(prs)
    x7_community(prs)


def main() -> None:
    prs = Presentation(str(TEMPLATE))
    clear_slides(prs)
    for build in (
        s01_title,
        s02_engineers,
        s03_system,
        s04_three_ways,
        s05_layers,
        s06_query,
        s07_cycle,
        s08_maintenance,
        s09_triggers,
        s10_why_not_rag,
        s11_where_rag_wins,
        s12_four_questions,
        appendix,
    ):
        build(prs)
    prs.save(str(OUT))
    print(f"wrote {OUT} ({len(prs.slides)} slides)")


if __name__ == "__main__":
    main()
