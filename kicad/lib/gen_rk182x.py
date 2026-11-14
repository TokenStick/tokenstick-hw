"""Generate KiCad symbol + footprint for Rockchip RK1820/RK1828 (FCBGA-746) from the datasheet pin list."""
import csv, os, re, sys

PINS_CSV, OUT = sys.argv[1], sys.argv[2]
LIB = "TokenStick"
FP_NAME = "Rockchip_RK182X_FCBGA-746_19.0x19.0mm_Layout28x28_P0.65mm"
ROWS = "A B C D E F G H J K L M N P R T U V W Y AA AB AC AD AE AF AG AH".split()
PITCH, PAD, BODY = 0.65, 0.30, 19.0

pins = {}
with open(PINS_CSV) as fh:
    for r in csv.DictReader(fh):
        pins[r["pin"]] = r["name"]
assert len(pins) == 746


def split(p):
    m = re.fullmatch(r"([A-Z]+)(\d+)", p)
    return m.group(1), int(m.group(2))


def key(p):
    r, c = split(p)
    return ROWS.index(r), c


# ---------------- footprint ----------------
def footprint():
    half = (len(ROWS) - 1) * PITCH / 2
    b = BODY / 2
    o = [f'(footprint "{FP_NAME}" (version 20221018) (generator tokenstick_gen)',
         '  (layer "F.Cu")',
         '  (descr "Rockchip RK1820/RK1828 FCBGA-746, 19x19mm, 28x28 grid, 0.65mm pitch, 0.36mm ball (datasheet Rev 1.4, Fig. 2-4/2-6)")',
         '  (tags "BGA 746 0.65 Rockchip RK1820 RK1828")',
         '  (attr smd)',
         f'  (fp_text reference "REF**" (at 0 {-b - 1.6:.3f}) (layer "F.SilkS") (effects (font (size 1 1) (thickness 0.15))))',
         f'  (fp_text value "{FP_NAME}" (at 0 {b + 1.6:.3f}) (layer "F.Fab") (effects (font (size 1 1) (thickness 0.15))))',
         '  (fp_text user "${REFERENCE}" (at 0 0) (layer "F.Fab") (effects (font (size 1 1) (thickness 0.15))))']

    def line(x1, y1, x2, y2, layer, w):
        o.append(f'  (fp_line (start {x1:.3f} {y1:.3f}) (end {x2:.3f} {y2:.3f}) (stroke (width {w}) (type solid)) (layer "{layer}"))')

    # fab outline with chamfered A1 corner
    ch = 1.0
    pts = [(-b + ch, -b), (b, -b), (b, b), (-b, b), (-b, -b + ch), (-b + ch, -b)]
    for (x1, y1), (x2, y2) in zip(pts, pts[1:]):
        line(x1, y1, x2, y2, "F.Fab", 0.1)
    # silk corners + A1 marker
    s, L = b + 0.11, 1.5
    for sx, sy in ((1, -1), (1, 1), (-1, 1)):
        line(sx * s, sy * s, sx * (s - L), sy * s, "F.SilkS", 0.12)
        line(sx * s, sy * s, sx * s, sy * (s - L), "F.SilkS", 0.12)
    line(-s, -s + L, -s, -s + 0.6, "F.SilkS", 0.12)
    line(-s + 0.6, -s, -s + L, -s, "F.SilkS", 0.12)
    o.append(f'  (fp_circle (center {-s - 0.5:.3f} {-s - 0.5:.3f}) (end {-s - 0.3:.3f} {-s - 0.5:.3f}) (stroke (width 0.2) (type solid)) (fill solid) (layer "F.SilkS"))')
    c = b + 1.0
    o.append(f'  (fp_rect (start {-c:.2f} {-c:.2f}) (end {c:.2f} {c:.2f}) (stroke (width 0.05) (type solid)) (fill none) (layer "F.CrtYd"))')
    for p in sorted(pins, key=key):
        r, col = key(p)
        x, y = -half + (col - 1) * PITCH, -half + r * PITCH
        o.append(f'  (pad "{p}" smd circle (at {x:.3f} {y:.3f}) (size {PAD} {PAD}) (layers "F.Cu" "F.Paste" "F.Mask"))')
    o.append(")")
    return "\n".join(o) + "\n"


# ---------------- symbol ----------------
def classify(name):
    if re.fullmatch(r"VSS_\d+", name): return "gnd", "VSS"
    if re.fullmatch(r"AVSS_\d+", name): return "gnd", "AVSS"
    if name in ("PLL_AVSS", "TVSS"): return "gnd", name
    if re.fullmatch(r"VDD_LOGIC_\d+", name): return "core", "VDD_LOGIC"
    if re.fullmatch(r"VDD_TOP_\d+", name): return "core", "VDD_TOP"
    if name in ("VDD_PMU_0V9", "VDD_LOGIC_SENSE_P", "VSS_SENSE_N") or name.startswith("VDD_LOGIC_PDN"): return "core", name
    if name == "DRAM_VMONI": return "dram", name
    m = re.fullmatch(r"(DRAM_[A-Z]+_\dV\d)_\d+", name)
    if m: return "dram", m.group(1)
    if "AVDD" in name or name.startswith("VCCIO"): return "apwr", name
    if "GPIO0_" in name: return "gpio0", name
    if "GPIO1_" in name: return "gpio1", name
    return "sys", name


UNITS = [("sys", "USB / PCIe / clock / system"), ("gpio0", "GPIO0 bank"), ("gpio1", "GPIO1 bank"),
         ("core", "Core power 0.9V"), ("dram", "DRAM power"), ("apwr", "Analog and IO power"), ("gnd", "Ground")]
POWER_UNITS = {"core", "dram", "apwr", "gnd"}
SENSE = {"VDD_LOGIC_SENSE_P", "VSS_SENSE_N", "VDD_LOGIC_PDN_0", "VDD_LOGIC_PDN_1", "DRAM_VMONI"}

groups = {u: {} for u, _ in UNITS}  # unit -> name -> [pin numbers]
for p in sorted(pins, key=key):
    u, n = classify(pins[p])
    groups[u].setdefault(n, []).append(p)


def etype(unit, name):
    if name in SENSE: return "passive"
    if unit in POWER_UNITS: return "power_in"
    if name == "OSC_XIN" or name in ("NPOR_DET", "USB0_DRD_VBUSDET", "USB0_DRD_ID") or name.startswith("SARADC_IN"): return "input"
    if name == "OSC_XOUT": return "output"
    return "bidirectional"


def symbol():
    o = ['(kicad_symbol_lib (version 20220914) (generator tokenstick_gen)',
         '  (symbol "RK1828" (in_bom yes) (on_board yes)']
    props = [("Reference", "U", "0 6.35", False), ("Value", "RK1828", "0 3.81", False),
             ("Footprint", f"{LIB}:{FP_NAME}", "0 -2.54", True),
             ("Datasheet", "RK1820/RK1828 Datasheet Rev 1.4", "0 -5.08", True),
             ("ki_keywords", "Rockchip RK1820 RK1828 AI coprocessor NPU LLM", "0 0", True),
             ("ki_description", "Rockchip RK1820/RK1828 AI co-processor, 20 TOPS NPU, in-package DRAM (2.5GB/5GB), FCBGA-746", "0 0", True)]
    for k, v, at, hide in props:
        o.append(f'    (property "{k}" "{v}" (at {at} 0) (effects (font (size 1.27 1.27)) (justify left){" hide" if hide else ""}))')
    for ui, (u, title) in enumerate(UNITS, 1):
        names = list(groups[u])
        longest = max(len(n) for n in names)
        w = max(25.4, round((longest * 1.05 + 6) / 2.54) * 2.54)
        h = (len(names) + 1) * 2.54
        top = 0
        o.append(f'    (symbol "RK1828_{ui}_1"')
        o.append(f'      (rectangle (start 0 {top:.2f}) (end {w:.2f} {top - h:.2f}) (stroke (width 0.254) (type default)) (fill (type background)))')
        o.append(f'      (text "{title}" (at 0 {top + 1.4:.2f} 0) (effects (font (size 1.27 1.27)) (justify left)))')
        for i, n in enumerate(names):
            y = top - (i + 1) * 2.54
            for j, p in enumerate(groups[u][n]):
                t = etype(u, n) if j == 0 else "passive"
                hide = " hide" if j else ""
                o.append(f'      (pin {t} line (at -5.08 {y:.2f} 0) (length 5.08){hide}'
                         f' (name "{n}" (effects (font (size 1.27 1.27))))'
                         f' (number "{p}" (effects (font (size 1.27 1.27)))))')
        o.append('    )')
    o.append('  )')
    o.append(')')
    return "\n".join(o) + "\n"


os.makedirs(os.path.join(OUT, f"{LIB}.pretty"), exist_ok=True)
with open(os.path.join(OUT, f"{LIB}.pretty", FP_NAME + ".kicad_mod"), "w") as fh:
    fh.write(footprint())
with open(os.path.join(OUT, f"{LIB}.kicad_sym"), "w") as fh:
    fh.write(symbol())
for u, t in UNITS:
    print(f"{t}: {len(groups[u])} pin names, {sum(len(v) for v in groups[u].values())} balls")
print("total balls", sum(len(v) for g in groups.values() for v in g.values()))
