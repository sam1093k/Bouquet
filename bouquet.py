"""
Bouquet animato in ASCII a colori, disegnato direttamente nel terminale.

Uso:
    pip install numpy
    python bouquet_ascii.py            # velocita' normale
    python bouquet_ascii.py 1.5        # 1.5x piu' veloce

La crescita avviene una sola volta; quando il bouquet e' completo i fiori
continuano a oscillare dolcemente, finche' non premi Ctrl+C. Serve un terminale con colori a 24 bit (Windows Terminal va bene).
Ingrandisci la finestra del terminale prima di avviarlo: l'animazione si adatta
alla dimensione (e si ridimensiona se la cambi mentre gira).
"""
import os
import sys
import time
import shutil
import numpy as np

# --- Parametri ---------------------------------------------------------
FPS = 40
N_FLOWERS = 9
T_STEMS = 32        # frame in cui finiscono di crescere gli steli
T_BLOOM = 85        # frame in cui finiscono di sbocciare i fiori
T_WRAP = 110        # frame in cui compare la carta con il nastro
TOTAL = 120         # frame in cui la composizione e' completa; poi i fiori continuano a oscillare
FLOWER_SCALE = 1.7   # dimensione dei fiori (piu' alto = fiori piu' grandi)
MAX_ROWS = 60

# Finestra del mondo: stretta e alta, per un bouquet slanciato
XMIN, XMAX = -5.0, 5.0
YMIN, YMAX = -1.0, 10.8
XSPAN, YSPAN = XMAX - XMIN, YMAX - YMIN


def rgb(h):
    h = h.lstrip("#")
    return (int(h[0:2], 16) << 16) | (int(h[2:4], 16) << 8) | int(h[4:6], 16)


PALETTE = [
    ("#ff6b9d", "#ffc2d9", "#ffd93d"),   # rosa
    ("#ff9f43", "#ffd8a8", "#a85a00"),   # arancio
    ("#a29bfe", "#dcd8ff", "#ffeaa7"),   # lilla
    ("#ff5252", "#ff9e9e", "#ffb347"),   # rosso
    ("#ffffff", "#f1f2f6", "#f6b93b"),   # margherita
    ("#fdcb6e", "#ffeaa7", "#a0541a"),   # girasole
]
PALETTE = [tuple(rgb(c) for c in p) for p in PALETTE]

# (petali esterni, bordo esterno, petali interni, bordo interno, centro)
STYLES = [
    ("@", "O", "%", "o", "&"),
    ("#", "H", "=", "+", "@"),
    ("0", "Q", "*", ".", "X"),
]

C_STEM = rgb("#3fbf63")
C_LEAF = rgb("#58c57a")
C_BUD = rgb("#4cb86b")
C_PAPER = rgb("#d9b382")
C_PAPER_DARK = rgb("#a67c4e")
C_BOW = rgb("#e84a5f")
C_KNOT = rgb("#c0392b")

# --- Dati dei fiori (stesso seed della versione matplotlib) -------------
rng = np.random.default_rng(7)
angles = np.linspace(-29, 29, N_FLOWERS) + rng.uniform(-1.5, 1.5, N_FLOWERS)
heights = 6.4 + 1.0 * np.cos(np.radians(angles) * 1.6) + rng.uniform(-0.25, 0.25, N_FLOWERS)
heights += np.array([1.8, 0.0, -1.8])[np.arange(N_FLOWERS) % 3]  # tre livelli: fiori ben separati
flowers = []
for i in range(N_FLOWERS):
    a = np.radians(angles[i])
    head = np.array([heights[i] * np.sin(a) * 0.78, heights[i] * np.cos(a)])
    flowers.append({
        "head": head,
        "colors": PALETTE[i % len(PALETTE)],
        "petals": int(rng.integers(7, 12)),
        "radius": rng.uniform(0.55, 0.85) * FLOWER_SCALE,
        "rot": rng.uniform(0, 360),
        "style": i % len(STYLES),
        "phase": rng.uniform(0, 2 * np.pi),
        "t_stem": rng.uniform(0, 11),
        "t_bloom": 32 + i * 4.5 + rng.uniform(0, 4),
    })


def ease(t):
    t = float(np.clip(t, 0, 1))
    return t * t * (3 - 2 * t)


def bezier(p0, p1, p2, s):
    s = s[:, None]
    return (1 - s) ** 2 * p0 + 2 * (1 - s) * s * p1 + s ** 2 * p2


# --- Renderer ----------------------------------------------------------
class Renderer:
    """Disegna su una griglia di caratteri. Mondo: x in [XMIN, XMAX], y in [YMIN, YMAX].
    Le celle del terminale sono alte circa il doppio che larghe."""

    def __init__(self, cols, lines):
        h = min(lines - 1, MAX_ROWS, int((cols - 1) * YSPAN / (2 * XSPAN)))
        self.H = max(h, 12)
        self.W = int(round(self.H * 2 * XSPAN / YSPAN))  # celle alte ~2x la larghezza
        self.left = max((cols - self.W) // 2, 0)
        self.top = max((lines - self.H) // 2, 0)
        xs = XMIN + (np.arange(self.W) + 0.5) / self.W * XSPAN
        ys = YMAX - (np.arange(self.H) + 0.5) / self.H * YSPAN
        self.XX, self.YY = np.meshgrid(xs, ys)
        self.ch = np.full((self.H, self.W), " ", dtype="<U1")
        self.pk = np.zeros((self.H, self.W), dtype=np.int64)
        self._esc = {}
        self._pos = [f"\x1b[{self.top + y + 1};{self.left + 1}H" for y in range(self.H)]

    # --- primitive ------------------------------------------------------
    def ellipse(self, c, a, b, ang, char, color, edge_char=None):
        W, H = self.W, self.H
        hs = max(a, b)
        x0 = max(int((c[0] - hs - XMIN) / XSPAN * W), 0)
        x1 = min(int((c[0] + hs - XMIN) / XSPAN * W) + 2, W)
        y0 = max(int((YMAX - (c[1] + hs)) / YSPAN * H), 0)
        y1 = min(int((YMAX - (c[1] - hs)) / YSPAN * H) + 2, H)
        if x0 >= x1 or y0 >= y1:
            return
        dx = self.XX[y0:y1, x0:x1] - c[0]
        dy = self.YY[y0:y1, x0:x1] - c[1]
        t = np.radians(ang)
        ct, st = np.cos(t), np.sin(t)
        u = (dx * ct + dy * st) / a
        v = (-dx * st + dy * ct) / b
        q = u * u + v * v
        m = q <= 1.0
        if not m.any():
            return
        sub_c = self.ch[y0:y1, x0:x1]
        if edge_char:
            sub_c[m] = np.where(q[m] < 0.45, char, edge_char)
        else:
            sub_c[m] = char
        self.pk[y0:y1, x0:x1][m] = color

    def triangle(self, p1, p2, p3, char, color):
        X, Y = self.XX, self.YY
        d1 = (X - p2[0]) * (p1[1] - p2[1]) - (p1[0] - p2[0]) * (Y - p2[1])
        d2 = (X - p3[0]) * (p2[1] - p3[1]) - (p2[0] - p3[0]) * (Y - p3[1])
        d3 = (X - p1[0]) * (p3[1] - p1[1]) - (p3[0] - p1[0]) * (Y - p1[1])
        neg = (d1 < 0) | (d2 < 0) | (d3 < 0)
        pos = (d1 > 0) | (d2 > 0) | (d3 > 0)
        m = ~(neg & pos)
        self.ch[m] = char
        self.pk[m] = color

    def polyline(self, pts, char, color, thick=2):
        cx = ((pts[:, 0] - XMIN) / XSPAN * self.W).astype(int)
        cy = ((YMAX - pts[:, 1]) / YSPAN * self.H).astype(int)
        for k in range(thick):
            xx = np.clip(cx + k, 0, self.W - 1)
            yy = np.clip(cy, 0, self.H - 1)
            self.ch[yy, xx] = char
            self.pk[yy, xx] = color

    # --- scena ----------------------------------------------------------
    def draw_flower(self, tip, f, bloom):
        if bloom <= 0:
            self.ellipse(tip, 0.16, 0.16, 0, "o", C_BUD)
            return
        r = f["radius"] * ease(bloom)
        c_main, c_light, c_center = f["colors"]
        n = f["petals"]
        spin = f["rot"] + 40 * (1 - ease(bloom))
        s_main, s_main_edge, s_in, s_in_edge, s_center = STYLES[f["style"]]
        for char, edge, col, scale, off in ((s_main, s_main_edge, c_main, 1.0, 0.0),
                                            (s_in, s_in_edge, c_light, 0.7, 180.0 / n)):
            for k in range(n):
                ang = spin + off + k * 360.0 / n
                rad = np.radians(ang)
                pc = tip + 0.5 * r * scale * np.array([np.cos(rad), np.sin(rad)])
                self.ellipse(pc, r * scale * 0.475, r * scale * 0.24, ang, char, col, edge)
        self.ellipse(tip, r * 0.24, r * 0.24, 0, s_center, c_center)

    def render(self, frame):
        self.ch[:] = " "
        ready = []

        for f in flowers:
            grow = ease((frame - f["t_stem"]) / (T_STEMS - 11))
            if grow <= 0:
                continue
            sway = 0.07 * np.sin(frame * 0.12 + f["phase"]) * ease((frame - T_BLOOM) / 20 + 0.2)
            p0 = np.array([0.0, 0.0])
            p2 = f["head"] + np.array([sway * f["head"][1], 0.0])
            p1 = np.array([f["head"][0] * 0.15, f["head"][1] * 0.5])
            pts = bezier(p0, p1, p2, np.linspace(0, grow, 90))
            self.polyline(pts, "|", C_STEM, thick=2)

            if grow > 0.6:
                s = ease((grow - 0.6) / 0.4)
                lp = pts[int(len(pts) * 0.55)]
                side = 1 if f["head"][0] >= 0 else -1
                self.ellipse(lp + np.array([0.28 * side, 0.1]), 0.35 * s, 0.13 * s,
                             side * 30, "~", C_LEAF)

            if grow >= 0.999:
                ready.append((f, p2, (frame - f["t_bloom"]) / 25))

        for f, tip, bloom in sorted(ready, key=lambda t: t[1][1]):
            self.draw_flower(tip, f, bloom)

        # carta di incarto + nastro
        w = ease((frame - T_BLOOM) / (T_WRAP - T_BLOOM))
        if w > 0.02:
            top = 3.6 * w
            self.triangle((-1.4 * w, top), (1.4 * w, top), (0.0, -0.9), ":", C_PAPER)
            fold = np.linspace(0, 1, 40)[:, None]
            self.polyline(np.array([0.0, -0.9]) * (1 - fold) + np.array([-0.35 * w, top]) * fold,
                          "/", C_PAPER_DARK, thick=1)
            if w > 0.9:
                b = ease((w - 0.9) / 0.1)
                if b > 0.05:
                    y = 1.1
                    self.triangle((0, y), (-0.6 * b, y + 0.3 * b), (-0.6 * b, y - 0.3 * b), "#", C_BOW)
                    self.triangle((0, y), (0.6 * b, y + 0.3 * b), (0.6 * b, y - 0.3 * b), "#", C_BOW)
                    self.ellipse(np.array([0.0, y]), 0.13 * b, 0.13 * b, 0, "O", C_KNOT)

        return self.to_ansi()

    def esc(self, p):
        e = self._esc.get(p)
        if e is None:
            e = f"\x1b[38;2;{p >> 16};{(p >> 8) & 255};{p & 255}m"
            self._esc[p] = e
        return e

    def to_ansi(self):
        rows = []
        chl = self.ch.tolist()
        pkl = self.pk.tolist()
        for y in range(self.H):
            parts = [self._pos[y]]
            prev = -1
            crow, prow = chl[y], pkl[y]
            for x in range(self.W):
                c = crow[x]
                if c == " ":
                    parts.append(" ")
                else:
                    p = prow[x]
                    if p != prev:
                        parts.append(self.esc(p))
                        prev = p
                    parts.append(c)
            parts.append("\x1b[0m")
            rows.append("".join(parts))
        return "".join(rows)


def main():
    speed = 1.0
    if len(sys.argv) > 1:
        try:
            speed = max(float(sys.argv[1]), 0.1)
        except ValueError:
            pass

    os.system("")  # abilita le sequenze ANSI nella console di Windows
    out = sys.stdout
    size = shutil.get_terminal_size((100, 40))
    r = Renderer(*size)
    out.write("\x1b[?1049h\x1b[?25l\x1b[2J")  # schermo alternativo, cursore nascosto
    try:
        t0 = time.perf_counter()
        last = -1
        while True:
            frame = int((time.perf_counter() - t0) * FPS * speed)  # cresce all'infinito: dopo TOTAL restano solo le oscillazioni
            new = shutil.get_terminal_size((100, 40))
            resized = new != size
            if resized:
                size = new
                r = Renderer(*size)
                out.write("\x1b[2J")
            if frame != last or resized:
                out.write(r.render(frame))  # un solo write per frame: niente flicker
                out.flush()
                last = frame
            time.sleep(1 / (FPS * 3))
    except KeyboardInterrupt:
        pass
    finally:
        out.write("\x1b[0m\x1b[?25h\x1b[?1049l")
        out.flush()


if __name__ == "__main__":
    main()
