"""
preview.py – PNG-Vorschau eines Blatts.

Nutzt matplotlib (falls installiert), sonst Pillow, sonst wird keine Vorschau erzeugt.
Holz = hellbraun gefüllt (Löcher ausgespart), Schnitt = schwarz, Gravur = blau.
"""
from __future__ import annotations

from typing import Optional

from steckwerk import Config, Sheet


def render_sheet(sheet: Sheet, cfg: Config, path: str, title: str = "", dpi: int = 110) -> Optional[str]:
    try:
        return _render_mpl(sheet, cfg, path, title, dpi)
    except ImportError:
        pass
    try:
        return _render_pil(sheet, cfg, path)
    except ImportError:
        return None


def _render_mpl(sheet: Sheet, cfg: Config, path: str, title: str, dpi: int) -> str:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.patches import PathPatch, Rectangle
    from matplotlib.path import Path

    scale = 1 / 25.4 * 1.6
    fig, ax = plt.subplots(figsize=(max(sheet.width * scale, 4), max(sheet.height * scale, 3)))
    ax.add_patch(Rectangle((0, 0), sheet.width, sheet.height, fill=True, fc="#f4f1ea",
                           ec="#bbbbbb", lw=0.6, ls="--"))
    for p in sheet.parts:
        verts, codes = [], []
        for poly in [p.outline] + list(p.holes):
            verts += list(poly) + [poly[0]]
            codes += [Path.MOVETO] + [Path.LINETO] * (len(poly) - 1) + [Path.CLOSEPOLY]
        ax.add_patch(PathPatch(Path(verts, codes), fc="#e2c08d", ec="none"))
        for s in p.engrave:
            xs = [q[0] for q in s.points] + ([s.points[0][0]] if s.closed else [])
            ys = [q[1] for q in s.points] + ([s.points[0][1]] if s.closed else [])
            ax.plot(xs, ys, color=cfg.engrave_color, lw=0.45)
        for poly in [p.outline] + list(p.holes):
            xs = [q[0] for q in poly] + [poly[0][0]]
            ys = [q[1] for q in poly] + [poly[0][1]]
            ax.plot(xs, ys, color=cfg.cut_color, lw=0.6)
        x0, y0, x1, y1 = p.bbox()
        ax.text((x0 + x1) / 2, y1 + 2.5, p.name.split("_", 1)[-1] if "_" in p.name else p.name,
                ha="center", va="top", fontsize=5, color="#555555")
    ax.set_xlim(-2, sheet.width + 2)
    ax.set_ylim(sheet.height + 2, -2)
    ax.set_aspect("equal")
    ax.set_xlabel("mm")
    ax.tick_params(labelsize=6)
    if title:
        ax.set_title(title, fontsize=8)
    fig.tight_layout()
    fig.savefig(path, dpi=dpi)
    plt.close(fig)
    return path


def _render_pil(sheet: Sheet, cfg: Config, path: str, px_per_mm: float = 3.0) -> str:
    from PIL import Image, ImageDraw
    w, h = int(sheet.width * px_per_mm), int(sheet.height * px_per_mm)
    img = Image.new("RGB", (w, h), "#f4f1ea")
    dr = ImageDraw.Draw(img)

    def tr(poly):
        return [(x * px_per_mm, y * px_per_mm) for x, y in poly]
    for p in sheet.parts:
        dr.polygon(tr(p.outline), fill="#e2c08d", outline=cfg.cut_color)
        for hole in p.holes:
            dr.polygon(tr(hole), fill="#f4f1ea", outline=cfg.cut_color)
        for s in p.engrave:
            pts = tr(s.points + ([s.points[0]] if s.closed else []))
            dr.line(pts, fill=cfg.engrave_color, width=1)
    img.save(path)
    return path
