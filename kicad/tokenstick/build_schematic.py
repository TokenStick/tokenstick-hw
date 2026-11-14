#!/usr/bin/env python3
"""Generate tokenstick.kicad_sch (KiCad 7) from the netlist in build_board.py.

Every connected pin gets a global label with its net name; there are no drawn wires.
Unused pins get a no-connect flag, except on the RK1828, whose remaining pins are not designed yet.
Run:  python3 build_schematic.py   (needs the KiCad symbol libraries)
"""
import csv, os, re, uuid
import build_board as bb

HERE = os.path.dirname(os.path.abspath(__file__))
SYMDIR = os.environ.get("KICAD7_SYMBOL_DIR", "/usr/share/kicad/symbols")
LIBDIR = os.path.join(HERE, "..", "lib")
PROJECT = "tokenstick"
ROOT = "6f1c2f0e-7d1a-4c55-9b7e-2a4d5f3e8c01"
U = lambda: str(uuid.uuid4())

# ---- symbols written by this script: name -> (left pins, right pins), pin = (number, name, type)
OWN = {
    "HD3SS3220": ([("30", "VDD5", "power_in"), ("8", "VCC33", "power_in"), ("2", "CC1", "bidirectional"), ("1", "CC2", "bidirectional"),
                   ("5", "VBUS_DET", "input"), ("4", "PORT", "input"), ("3", "CURRENT_MODE", "input"), ("22", "ADDR", "input"),
                   ("29", "ENn_CC", "input"), ("12", "ENn_MUX", "input"), ("11", "DIR", "open_collector"), ("27", "ID", "open_collector"),
                   ("23", "INT_N/OUT3", "open_collector"), ("24", "VCONN_FAULT_N", "open_collector"), ("25", "SDA/OUT1", "bidirectional"),
                   ("26", "SCL/OUT2", "bidirectional"), ("13", "GND", "power_in"), ("28", "GND", "power_in"), ("31", "EP", "power_in")],
                  [("6", "TXp", "passive"), ("7", "TXn", "passive"), ("9", "RXp", "passive"), ("10", "RXn", "passive"),
                   ("17", "TX1p", "passive"), ("16", "TX1n", "passive"), ("15", "RX1p", "passive"), ("14", "RX1n", "passive"),
                   ("21", "TX2p", "passive"), ("20", "TX2n", "passive"), ("19", "RX2p", "passive"), ("18", "RX2n", "passive")]),
    "TPD4E05U06DQA": ([("1", "D1+", "passive"), ("2", "D1-", "passive"), ("4", "D2+", "passive"), ("5", "D2-", "passive"), ("3", "GND", "power_in")],
                      [("10", "D1+", "passive"), ("9", "D1-", "passive"), ("7", "D2+", "passive"), ("6", "D2-", "passive"), ("8", "GND", "power_in")]),
    "AP2112K-3.3": ([("1", "VIN", "power_in"), ("3", "EN", "input"), ("2", "GND", "power_in")], [("5", "VOUT", "power_out"), ("4", "NC", "no_connect")]),
    "AON7403": ([("4", "G", "input")], [("1", "S", "passive"), ("2", "S", "passive"), ("3", "S", "passive"), ("5", "D", "passive"),
                                        ("6", "D", "passive"), ("7", "D", "passive"), ("8", "D", "passive"), ("9", "D", "passive")]),
    "TPS56637": ([("8", "VIN", "power_in"), ("1", "EN", "input"), ("10", "MODE", "input"), ("3", "AGND", "power_in"), ("9", "PGND", "power_in")],
                 [("6", "SW", "power_out"), ("7", "BOOT", "passive"), ("2", "FB", "input"), ("4", "PG", "open_collector"), ("5", "NC", "no_connect")]),
    "USB4105-GF-A": ([], [("A4", "VBUS", "passive"), ("A9", "VBUS", "passive"), ("B4", "VBUS", "passive"), ("B9", "VBUS", "passive"),
                          ("A5", "CC1", "bidirectional"), ("B5", "CC2", "bidirectional"), ("A6", "D+", "bidirectional"), ("B6", "D+", "bidirectional"),
                          ("A7", "D-", "bidirectional"), ("B7", "D-", "bidirectional"), ("A8", "SBU1", "bidirectional"), ("B8", "SBU2", "bidirectional"),
                          ("A1", "GND", "passive"), ("A12", "GND", "passive"), ("B1", "GND", "passive"), ("B12", "GND", "passive"), ("S1", "SHIELD", "passive")]),
}
F = '(effects (font (size 1.27 1.27)))'


def own_symbol(name, left, right):
    rows = max(len(left), len(right)); w = 12.7; top = 0.0; bot = -2.54 * (rows + 1)
    L = ['  (symbol "%s" (in_bom yes) (on_board yes)' % name,
         '    (property "Reference" "%s" (at 0 2.54 0) %s)' % ("J" if name.startswith("USB") else "Q" if name == "AON7403" else "U", F),
         '    (property "Value" "%s" (at 0 %.2f 0) %s)' % (name, bot - 2.54, F),
         '    (property "Footprint" "" (at 0 0 0) (effects (font (size 1.27 1.27)) hide))',
         '    (property "Datasheet" "" (at 0 0 0) (effects (font (size 1.27 1.27)) hide))',
         '    (symbol "%s_0_1" (rectangle (start %.2f %.2f) (end %.2f %.2f) (stroke (width 0.254) (type default)) (fill (type background))))' % (name, -w, top, w, bot),
         '    (symbol "%s_1_1"' % name]
    for side, pins in ((-1, left), (1, right)):
        for i, (num, pname, typ) in enumerate(pins):
            L.append('      (pin %s line (at %.2f %.2f %d) (length 5.08) (name "%s" %s) (number "%s" %s))'
                     % (typ, side * (w + 5.08), -2.54 * (i + 1), 0 if side < 0 else 180, pname, F, num, F))
    L += ['    )', '  )']
    return "\n".join(L)


def block(text, name):
    i = text.find('\n  (symbol "%s"' % name)
    assert i >= 0, name
    i += 1; depth = 0
    for j in range(i, len(text)):
        if text[j] == "(": depth += 1
        elif text[j] == ")":
            depth -= 1
            if depth == 0: return text[i:j + 1]


PIN = re.compile(r'\(pin\s+\w+\s+\w+\s+\(at\s+([-\d.]+)\s+([-\d.]+)\s+(\d+)\)\s+\(length\s+[-\d.]+\)(?:\s+hide)?\s+\(name\s+"(?:[^"\\]|\\.)*".*?\(number\s+"([^"]+)"', re.S)


def pins_of(blk, name):
    """-> {unit: [(number, x, y, angle)]}"""
    out = {}
    for m in re.finditer(r'\(symbol "%s_(\d+)_(\d+)"' % re.escape(name), blk):
        unit = int(m.group(1)); i = m.start(); depth = 0
        for j in range(i, len(blk)):
            if blk[j] == "(": depth += 1
            elif blk[j] == ")":
                depth -= 1
                if depth == 0: break
        for p in PIN.finditer(blk[i:j + 1]):
            out.setdefault(unit, []).append((p.group(4), float(p.group(1)), float(p.group(2)), int(p.group(3))))
    return out


# ---- which symbol each part uses: ref -> (library nickname, symbol name, footprint id)
def lib_of(ref, value):
    fp = bb.PARTS[ref]
    fpid = ("TokenStick" if fp[0] == bb.LIB else os.path.basename(fp[0])[:-7]) + ":" + fp[1]
    if ref[0] == "R": return "Device", "R", fpid
    if ref[0] == "C": return "Device", "C", fpid
    if ref[0] == "L" and ref != "LG1": return "Device", "L", fpid
    if ref == "D1": return "Device", "D_Zener", fpid
    table = {"J1": ("Connector", "USB_C_Receptacle"), "J2": ("TokenStick_Parts", "USB4105-GF-A"), "U1": ("TokenStick", "RK1828"),
             "U2": ("Interface_USB", "STUSB4500QTR"), "U3": ("TokenStick_Parts", "HD3SS3220"), "U4": ("TokenStick_Parts", "TPD4E05U06DQA"),
             "U5": ("TokenStick_Parts", "TPD4E05U06DQA"), "U6": ("TokenStick_Parts", "TPS56637"), "U7": ("TokenStick_Parts", "AP2112K-3.3"),
             "Q1": ("TokenStick_Parts", "AON7403"), "Q2": ("TokenStick_Parts", "AON7403")}
    return (*table[ref], fpid)


def main():
    pin_net = {}
    for name, pins in bb.NETS.items():
        for p in pins.split(): pin_net[p] = name
    with open(os.path.join(LIBDIR, "rk182x_pins.csv")) as f:
        for ball, pname in list(csv.reader(f))[1:]:
            if (pname.startswith("VSS_") and pname != "VSS_SENSE_N") or pname.startswith("AVSS_"): pin_net["U1." + ball] = "GND"

    own_lib = "(kicad_symbol_lib (version 20220914) (generator tokenstick_gen)\n" + "\n".join(own_symbol(n, *lr) for n, lr in OWN.items()) + "\n)\n"
    open(os.path.join(LIBDIR, "TokenStick_Parts.kicad_sym"), "w").write(own_lib)
    texts = {"TokenStick_Parts": own_lib, "TokenStick": open(os.path.join(LIBDIR, "TokenStick.kicad_sym")).read()}
    defs, pinmap = {}, {}

    def load(lib, name):
        key = lib + ":" + name
        if key not in defs:
            if lib not in texts: texts[lib] = open(os.path.join(SYMDIR, lib + ".kicad_sym")).read()
            blk = block(texts[lib], name)
            assert "(extends" not in blk, key
            pinmap[key] = pins_of(blk, name)
            defs[key] = "    " + blk.replace('(symbol "%s"' % name, '(symbol "%s"' % key, 1).replace("\n", "\n  ")
        return key

    out, x, y, rowh = [], 40.0, 40.0, 0.0
    order = ["J1", "U4", "U5", "U3", "C15", "C16", "C7", "C8", "R7", "R15", "U7", "C18", "C19", "R13", "U1",
             "J2", "U2", "Q1", "Q2", "D1", "R1", "R2", "R3", "R4", "R5", "R6", "C1", "C2", "C3", "C4", "C5", "C6",
             "U6", "L1", "C9", "C10", "C11", "C12", "C13", "C14", "C17", "R8", "R9", "R10", "R11", "R12", "R14"]
    assert set(order) == set(bb.PARTS) - {"LG1"}
    PAGE_W = 1100.0
    for ref in order:
        lib, name, fpid = lib_of(ref, bb.PARTS[ref][2])
        key = load(lib, name)
        for unit, pins in sorted(pinmap[key].items()):
            xs = [p[1] for p in pins]; ys = [p[2] for p in pins]
            w = max(xs) - min(xs) + 76.0; h = max(ys) - min(ys) + 30.0
            if x + w > PAGE_W: x, y, rowh = 40.0, y + rowh + 10.0, 0.0
            sx = round((x + 38.0 - min(xs)) / 2.54) * 2.54; sy = round((y + 15.0 + max(ys)) / 2.54) * 2.54
            x += w; rowh = max(rowh, h)
            out.append('  (symbol (lib_id "%s") (at %.2f %.2f 0) (unit %d) (in_bom yes) (on_board yes) (dnp no) (uuid %s)' % (key, sx, sy, unit, U()))
            out.append('    (property "Reference" "%s" (at %.2f %.2f 0) %s)' % (ref, sx, sy - max(ys) - 5.08, F))
            out.append('    (property "Value" "%s" (at %.2f %.2f 0) %s)' % (bb.PARTS[ref][2], sx, sy - max(ys) - 2.54, F))
            out.append('    (property "Footprint" "%s" (at %.2f %.2f 0) (effects (font (size 1.27 1.27)) hide))' % (fpid, sx, sy))
            out.append('    (property "Datasheet" "" (at %.2f %.2f 0) (effects (font (size 1.27 1.27)) hide))' % (sx, sy))
            for num in sorted({p[0] for p in pins}): out.append('    (pin "%s" (uuid %s))' % (num, U()))
            out.append('    (instances (project "%s" (path "/%s" (reference "%s") (unit %d))))\n  )' % (PROJECT, ROOT, ref, unit))
            seen = {}
            for num, px, py, ang in pins:
                net = pin_net.get(ref + "." + num)
                pos = (round(sx + px, 2), round(sy - py, 2))
                if net is None:
                    if ref != "U1" and pos not in seen:
                        out.append('  (no_connect (at %.2f %.2f) (uuid %s))' % (*pos, U()))
                    continue
                assert seen.get(pos, net) == net, (ref, num, net, seen[pos])
                if pos in seen: continue
                seen[pos] = net
                la = {0: 180, 180: 0, 90: 270, 270: 90}[ang]
                out.append('  (global_label "%s" (shape passive) (at %.2f %.2f %d) (effects (font (size 1.27 1.27)) (justify %s)) (uuid %s)\n'
                           '    (property "Intersheetrefs" "${INTERSHEET_REFS}" (at 0 0 0) (effects (font (size 1.27 1.27)) hide)))'
                           % (net, *pos, la, "right" if la in (180, 270) else "left", U()))
    sch = ['(kicad_sch (version 20230121) (generator tokenstick_gen)', '  (uuid %s)' % ROOT, '  (paper "User" %.0f %.0f)' % (PAGE_W + 40, y + rowh + 60),
           '  (title_block (title "TokenStick v1") (company "TokenStick") (comment 1 "Generated by build_schematic.py from the netlist in build_board.py"))',
           '  (lib_symbols', *defs.values(), '  )', *out, '  (sheet_instances (path "/" (page "1")))', ')']
    open(os.path.join(HERE, PROJECT + ".kicad_sch"), "w").write("\n".join(sch) + "\n")
    open(os.path.join(HERE, "sym-lib-table"), "w").write(
        '(sym_lib_table\n  (lib (name "TokenStick")(type "KiCad")(uri "${KIPRJMOD}/../lib/TokenStick.kicad_sym")(options "")(descr "RK182X"))\n'
        '  (lib (name "TokenStick_Parts")(type "KiCad")(uri "${KIPRJMOD}/../lib/TokenStick_Parts.kicad_sym")(options "")(descr "Project symbols"))\n)\n')
    return pin_net


if __name__ == "__main__":
    pin_net = main()
    print("wrote schematic,", len(pin_net), "connected pins expected")
