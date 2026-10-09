#!/usr/bin/env python3
"""
make_icon.py – zeichnet das App-Symbol (braucht Pillow) und schreibt

  packaging/macos/Laserforge.icns   Symbol der Mac-App (PNG-Einträge 16–1024 px)
  web/icon.png                      Favicon der Weboberfläche (256 px)

Nur nötig, wenn sich das Symbol ändern soll – beide Dateien liegen fertig bei.
"""
import io
import os
import struct

from PIL import Image, ImageDraw, ImageFilter

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
S = 2048                                   # Zeichenfläche (4× für Kantenglättung), Ziel 512/1024

PINE, PINE_DARK = (29, 106, 84), (16, 66, 52)
PLY, PLY_EDGE = (227, 199, 146), (176, 140, 84)
BEAM = (255, 92, 54)


def draw() -> Image.Image:
    img = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    # Grundfläche nach macOS-Raster: 824/1024 mit abgerundeten Ecken, leichter Verlauf
    m, r = int(S * 100 / 1024), int(S * 185 / 1024)
    grad = Image.new("RGBA", (S, S))
    gd = ImageDraw.Draw(grad)
    for y in range(S):
        t = y / S
        gd.line([(0, y), (S, y)], fill=tuple(int(a + (b - a) * t) for a, b in zip(PINE, PINE_DARK)) + (255,))
    mask = Image.new("L", (S, S), 0)
    ImageDraw.Draw(mask).rounded_rectangle([m, m, S - m, S - m], r, fill=255)
    shadow = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    ImageDraw.Draw(shadow).rounded_rectangle([m, m + 24, S - m, S - m + 24], r, fill=(0, 0, 0, 90))
    img.alpha_composite(shadow.filter(ImageFilter.GaussianBlur(28)))
    img.paste(grad, (0, 0), mask)

    # Wichtelhaus aus Sperrholz mit Zinken – das Laserforge-Motiv
    d = ImageDraw.Draw(img)
    cx, base, w, wall = S // 2, int(S * 0.76), int(S * 0.46), int(S * 0.22)
    x0, x1, eave = cx - w // 2, cx + w // 2, base - wall
    peak = eave - int(w * 0.5)
    house = [(x0, base), (x0, eave), (cx, peak), (x1, eave), (x1, base)]
    d.polygon(house, fill=PLY)
    # Dachüberstand als Streifen
    t = int(S * 0.035)
    for sx in (-1, 1):
        ex = cx + sx * (w // 2 + int(S * 0.04))
        d.line([(cx, peak - t), (ex, eave + int(S * 0.012))], fill=PLY_EDGE, width=int(t * 1.25))
    # Zinken an der Sockelkante
    n, fw = 7, w / 7
    for i in range(n):
        if i % 2 == 0:
            d.rectangle([x0 + i * fw, base, x0 + (i + 1) * fw, base + int(S * 0.035)], fill=PLY)
    # Tür (Rundbogen) und Rundfenster als Ausschnitte
    dw, dh = int(w * 0.24), int(wall * 0.62)
    d.rectangle([cx - dw // 2, base - dh + dw // 2, cx + dw // 2, base], fill=PINE_DARK)
    d.ellipse([cx - dw // 2, base - dh, cx + dw // 2, base - dh + dw], fill=PINE_DARK)
    wr = int(w * 0.085)
    wy = eave - int(w * 0.16)
    d.ellipse([cx - wr, wy - wr, cx + wr, wy + wr], fill=PINE_DARK)

    # Laserstrahl auf den First, mit Glühen
    glow = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    gl = ImageDraw.Draw(glow)
    top = int(S * 0.13)
    gl.line([(cx, top), (cx, peak - t)], fill=BEAM + (255,), width=int(S * 0.03))
    gl.ellipse([cx - 60, peak - t - 60, cx + 60, peak - t + 60], fill=BEAM + (255,))
    img.alpha_composite(glow.filter(ImageFilter.GaussianBlur(26)))
    d = ImageDraw.Draw(img)
    d.line([(cx, top), (cx, peak - t)], fill=(255, 214, 196, 255), width=int(S * 0.009))
    d.ellipse([cx - 22, peak - t - 22, cx + 22, peak - t + 22], fill=(255, 240, 230, 255))
    return img


def png(img: Image.Image, size: int) -> bytes:
    buf = io.BytesIO()
    img.resize((size, size), Image.LANCZOS).save(buf, "PNG", optimize=True)
    return buf.getvalue()


def icns(img: Image.Image) -> bytes:
    kinds = [("icp4", 16), ("icp5", 32), ("icp6", 64), ("ic07", 128), ("ic08", 256), ("ic09", 512),
             ("ic10", 1024), ("ic11", 32), ("ic12", 64), ("ic13", 256), ("ic14", 512)]
    body = b"".join(k.encode() + struct.pack(">I", len(data) + 8) + data
                    for k, data in ((k, png(img, s)) for k, s in kinds))
    return b"icns" + struct.pack(">I", len(body) + 8) + body


if __name__ == "__main__":
    im = draw()
    with open(os.path.join(ROOT, "packaging", "macos", "Laserforge.icns"), "wb") as fh:
        fh.write(icns(im))
    with open(os.path.join(ROOT, "web", "icon.png"), "wb") as fh:
        fh.write(png(im, 256))
    im.resize((512, 512), Image.LANCZOS).save(os.path.join(ROOT, "packaging", "macos", "icon_512.png"))
    print("Symbol geschrieben")
