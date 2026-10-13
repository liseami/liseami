"""
[INPUT]: fusion-pixel 10px 简中等宽字体（argv[1]，原生 10px 渲染保像素锐利）；Pillow 光栅化
[OUTPUT]: assets/banner.svg（argv[2]）—— 左栏名字贡献图，右栏 neofetch 终端信息，CRT 扫描线
[POS]: 主页横幅的唯一生成器。改横幅文案改本文件后重跑，禁手改 SVG —— 代价是下次重生成被覆盖
[PROTOCOL]: 变更时更新此头部，然后检查 CLAUDE.md
用法: python3 scripts/banner.py ~/Library/Fonts/fusion-pixel-10px-monospaced-zh_hans.ttf assets/banner.svg
"""
import sys, random
from PIL import ImageFont, Image, ImageDraw
FONT = ImageFont.truetype(sys.argv[1], 10)
OUT = sys.argv[2]
random.seed(6666)

# ---------- 调色板 (GitHub dark) ----------
BG, PANEL, LINE = "#0d1117", "#161b22", "#30363d"
FG, MUTE = "#e6edf3", "#7d8590"
GREENS = ["#0e4429", "#006d32", "#26a641", "#39d353"]
EMPTY = "#161b22"

def bitmap(text):
    w = int(FONT.getlength(text)) + 2
    im = Image.new("1", (w, 12), 0)
    d = ImageDraw.Draw(im); d.fontmode = "1"; d.text((0, 0), text, font=FONT, fill=1)
    return [[im.getpixel((x, y)) for x in range(w)] for y in range(1, 11)], w

def text_path(text, x, y, s, color):
    """一行像素字：同行连续像素合并为一段 run，整行一个 path。"""
    rows, w = bitmap(text)
    d = []
    for ry, row in enumerate(rows):
        rx = 0
        while rx < w:
            if row[rx]:
                st = rx
                while rx < w and row[rx]: rx += 1
                d.append(f"M{x+st*s} {y+ry*s}h{(rx-st)*s}v{s}h-{(rx-st)*s}z")
            else:
                rx += 1
    return f'<path fill="{color}" d="{"".join(d)}"/>', int(FONT.getlength(text)) * s

def line(parts, x, y, s=2):
    out = []
    for text, color in parts:
        p, w = text_path(text, x, y, s, color); out.append(p); x += w
    return "".join(out), x

W, H = 960, 340
svg = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" shape-rendering="crispEdges" role="img" aria-label="赵纯想 · 程序员 / 作家 / AI 实践者">',
       '<defs><pattern id="scan" width="4" height="4" patternUnits="userSpaceOnUse"><rect width="4" height="2" fill="#000" opacity=".18"/></pattern></defs>',
       f'<rect width="{W}" height="{H}" fill="{BG}"/>',
       f'<rect x="2" y="2" width="{W-4}" height="{H-4}" fill="none" stroke="{LINE}" stroke-width="4"/>']

# ---------- 标题栏 ----------
svg.append(f'<rect x="4" y="4" width="{W-8}" height="36" fill="{PANEL}"/><rect x="4" y="40" width="{W-8}" height="4" fill="{LINE}"/>')
for i, c in enumerate(["#ff5f56", "#ffbd2e", "#27c93f"]):
    svg.append(f'<rect x="{22+i*22}" y="16" width="12" height="12" fill="{c}"/>')
t, _ = line([("liseami@chunxiang.ai: ~", MUTE)], 400, 13); svg.append(t)

# ---------- 左栏：名字贡献图 ----------
L_X, L_Y = 44, 70
t, _ = line([("$ ", GREENS[3]), ("whoami", FG)], L_X, L_Y); svg.append(t)
rows, _ = bitmap("赵纯想")
CELL, SQ, COLS, ROWS = 12, 10, 32, 11
gx, gy = L_X, L_Y + 40
cells = []
for r in range(ROWS):
    for c in range(COLS):
        on = 1 <= r <= 9 and 1 <= c <= 30 and rows[r - 1][c - 1]
        # 字形格只取两档高亮保可读；底格偶撒最暗档，像真实贡献图
        color = random.choice(GREENS[2:] + GREENS[3:]) if on else (GREENS[0] if random.random() < .1 else EMPTY)
        cells.append(f'<rect x="{gx+c*CELL}" y="{gy+r*CELL}" width="{SQ}" height="{SQ}" fill="{color}"/>')
svg.append(f'<g>{"".join(cells)}</g>')
# 扫描光条：静态帧名字完整可见，动画只是叠加层，SMIL 不播也不缺内容
svg.append(f'<clipPath id="grid"><rect x="{gx}" y="{gy}" width="{COLS*CELL}" height="{ROWS*CELL}"/></clipPath>'
           f'<g clip-path="url(#grid)"><rect x="{gx-3*CELL}" y="{gy}" width="{3*CELL}" height="{ROWS*CELL}" fill="{GREENS[3]}" opacity=".22">'
           f'<animateTransform attributeName="transform" type="translate" values="0 0;{(COLS+3)*CELL} 0" dur="3.2s" repeatCount="indefinite"/></rect></g>')
legend_y = gy + ROWS * CELL + 14
t, lx = line([("Less ", MUTE)], gx + COLS * CELL - 150, legend_y); svg.append(t)
for i, c in enumerate([EMPTY] + GREENS):
    svg.append(f'<rect x="{lx+i*14}" y="{legend_y+2}" width="10" height="10" fill="{c}"/>')
t, _ = line([(" More", MUTE)], lx + 5 * 14, legend_y); svg.append(t)
t, cx = line([("$ ", GREENS[3]), ("cat ./人间", FG)], L_X, legend_y + 40); svg.append(t)
svg.append(f'<rect x="{cx+6}" y="{legend_y+40}" width="10" height="20" fill="{GREENS[3]}">'
           '<animate attributeName="opacity" values="1;0" dur="1.1s" calcMode="discrete" repeatCount="indefinite"/></rect>')

# ---------- 右栏：neofetch ----------
R_X, y, LH = 480, 70, 26
t, _ = line([("liseami", GREENS[3]), ("@", FG), ("github", GREENS[3])], R_X, y); svg.append(t)
y += LH; t, _ = line([("-" * 14, MUTE)], R_X, y); svg.append(t)
for k, v in [("Name", "赵纯想 Zhao Chunxiang"), ("Role", "程序员 / 作家 / AI 实践者"), ("Motto", "在人间，写小说、代码和剧本"),
             ("Build", "Laper · Bellybook · Vibe Coding"), ("Books", "《坏一坏》《人生灿灿》"),
             ("Award", "极客公园 IF 2025 年度开发者"), ("Home", "chunxiang.ai")]:
    y += LH; t, _ = line([(f"{k:<7}", GREENS[2]), (v, FG)], R_X, y); svg.append(t)
y += LH + 8
for i, c in enumerate(["#484f58", "#ff7b72", "#3fb950", "#d29922", "#58a6ff", "#bc8cff", "#39c5cf", "#e6edf3"]):
    svg.append(f'<rect x="{R_X+i*24}" y="{y}" width="24" height="16" fill="{c}"/>')

svg.append(f'<rect x="4" y="44" width="{W-8}" height="{H-48}" fill="url(#scan)"/></svg>')
open(OUT, "w").write("\n".join(svg) + "\n")
