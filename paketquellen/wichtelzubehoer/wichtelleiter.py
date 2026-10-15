"""
Wichtelleiter – Paket „Wichtelzubehör“.

Zwei Holme mit Schlitzen, die Sprossen stecken mit Zapfen an beiden Enden darin. Zum Anlehnen an das
Wichtelhaus, die Wichteltür oder ein Regal.
"""
from steckwerk import Assembly, Part, oriented
from pakete import bibliothek, num, sel

Z = bibliothek("verzierungen")
K = Z.K

UEBERSETZUNG = {"en": {
    "Wichtelleiter": "Elf ladder", "Wichtelzubehör": "Elf accessories",
    "Steckleiter zum Anlehnen: zwei Holme, die Sprossen werden mit Zapfen eingesteckt.":
        "Slot-together ladder to lean against something: two rails, the rungs plug in with tabs.",
    "Höhe": "Height", "Breite": "Width", "Sprossenabstand": "Rung spacing", "Holme oben": "Rail tops",
    "rund": "round", "spitz": "pointed", "mit Kugel": "with ball",
    "Die Sprossen mit ihren Zapfen in die Schlitze der beiden Holme stecken.":
        "Push the rungs with their tabs into the slots of both rails.",
}}

INFO = dict(
    label="Wichtelleiter", group="Wichtelzubehör",
    desc="Steckleiter zum Anlehnen: zwei Holme, die Sprossen werden mit Zapfen eingesteckt.",
    params=[
        num("hoehe", "Höhe", 100, 40, 300),
        num("breite", "Breite", 28, 16, 80),
        num("abstand", "Sprossenabstand", 15, 8, 40),
        sel("oben", "Holme oben", [("rund", "rund"), ("spitz", "spitz"), ("kugel", "mit Kugel")], "kugel"),
    ],
)


def build(cfg, name="wichtelleiter", hoehe=100.0, breite=28.0, abstand=15.0, oben="kugel"):
    T = cfg.T
    H, B, a = cfg.s(hoehe), cfg.s(breite), cfg.s(abstand)
    tw = max(cfg.min_tab_width + 0.6, min(cfg.tab_factor * T, 6.0))
    rand = max(2.2, T * 0.8)
    hb = tw + 2 * rand                                   # Holmbreite (Tiefe der Leiter)
    Li = B - 2 * T                                       # Sprossen zwischen den Holmen
    if Li < 8:
        raise ValueError("Die Leiter ist für diese Materialstärke zu schmal")
    ys = []
    y = a * 0.8
    while y < H - a * 0.6 - hb:
        ys.append(y)
        y += a
    if len(ys) < 2:
        raise ValueError("Zu wenige Sprossen – die Leiter höher machen oder den Abstand verkleinern")
    asm = Assembly(name, params=dict(hoehe=H, breite=B, sprossen=len(ys)))
    for seite, s0 in (("links", 0), ("rechts", 1)):
        pts = _holm(hb, H, oben)
        holm = Part(f"holm_{seite}", oriented(pts, True))
        for k, y in enumerate(ys):
            Z.schlitz(holm, f"sprosse{k}", 0.0, y, tw, T, 10 + 2 * k + s0)
        asm.parts.append(holm)
    for k in range(len(ys)):
        sp = Z.brett(f"sprosse{k + 1}", Li - 0.2, hb - 1.0, T,
                     links=[((hb - 1.0) / 2, tw, "links", 10 + 2 * k)], rechts=[((hb - 1.0) / 2, tw, "rechts", 11 + 2 * k)])
        asm.parts.append(sp)
        asm.connect(f"sprosse{k + 1}:links", f"holm_links:sprosse{k}")
        asm.connect(f"sprosse{k + 1}:rechts", f"holm_rechts:sprosse{k}")
    asm.notes.append("Die Sprossen mit ihren Zapfen in die Schlitze der beiden Holme stecken.")
    return asm


def _holm(b, H, oben):
    """Holm (x −b/2 … b/2, y 0 … H) mit gestaltetem Kopf."""
    if oben == "spitz":
        return [(-b / 2, 0), (b / 2, 0), (b / 2, H - b * 0.9), (0, H), (-b / 2, H - b * 0.9)]
    if oben == "kugel":
        r = b * 0.62
        hals = b * 0.32
        yk = H - r
        import math
        a0 = math.asin(hals / r)
        arc = K.arc(0, yk, r, -math.pi / 2 + a0, 3 * math.pi / 2 - a0, 40)
        y_hals = yk - r * math.cos(a0)
        return [(-b / 2, 0), (b / 2, 0), (b / 2, y_hals - b * 0.5), (hals, y_hals - b * 0.15)] + arc + \
               [(-hals, y_hals - b * 0.15), (-b / 2, y_hals - b * 0.5)]
    r = b / 2
    return [(-b / 2, 0), (b / 2, 0), (b / 2, H - r)] + K.arc(0, H - r, r, 0, 3.14159265, 20)[1:-1] + [(-b / 2, H - r)]
