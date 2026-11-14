#!/usr/bin/env python3
"""Generate tokenstick.kicad_sch (KiCad 7) from the netlist in build_board.py.

Parts are grouped in framed blocks. Resistors, capacitors and the inductor sit next to the IC pin they
belong to and are wired to it; everything else is connected by net labels.
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
    if ref.startswith("TP"): return "Connector", "TestPoint", fpid
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

    out = []
    FS = '(effects (font (size 1.0 1.0)))'
    TWO = lambda r: r[0] in "RCLD" and r != "LG1"

    def emit(ref, key, unit, sx, sy, rot, pins):
        """Place one symbol unit; returns {pin number: (x, y, label angle)}."""
        fpid = lib_of(ref, None)[2]
        out.append('  (symbol (lib_id "%s") (at %.2f %.2f %d) (unit %d) (in_bom yes) (on_board yes) (dnp no) (uuid %s)' % (key, sx, sy, rot, unit, U()))
        ys = [p[2] for p in pins]
        if rot == 0 and not TWO(ref):
            rp, vp = (sx, sy - max(ys) - 5.08), (sx, sy - max(ys) - 2.54)
        elif max(abs(p[1]) for p in pins) < 0.01:
            rp, vp = (sx + 2.54, sy - 1.27), (sx + 2.54, sy + 1.27)
        else:
            rp, vp = (sx - 2.0, sy - 1.9), (sx + 2.2, sy - 1.9)
        just = ' (justify left)' if TWO(ref) and max(abs(p[1]) for p in pins) < 0.01 and rot == 0 else ''
        out.append('    (property "Reference" "%s" (at %.2f %.2f 0) (effects (font (size 1.0 1.0))%s))' % (ref, *rp, just))
        out.append('    (property "Value" "%s" (at %.2f %.2f 0) (effects (font (size 1.0 1.0))%s))' % (bb.PARTS[ref][2], *vp, just))
        out.append('    (property "Footprint" "%s" (at %.2f %.2f 0) (effects (font (size 1.27 1.27)) hide))' % (fpid, sx, sy))
        out.append('    (property "Datasheet" "" (at %.2f %.2f 0) (effects (font (size 1.27 1.27)) hide))' % (sx, sy))
        for num in sorted({p[0] for p in pins}): out.append('    (pin "%s" (uuid %s))' % (num, U()))
        out.append('    (instances (project "%s" (path "/%s" (reference "%s") (unit %d))))\n  )' % (PROJECT, ROOT, ref, unit))
        res = {}
        T = {0: lambda px, py: (px, -py), 90: lambda px, py: (-py, -px), 180: lambda px, py: (-px, py), 270: lambda px, py: (py, px)}[rot]
        for num, px, py, ang in pins:
            dx, dy = T(px, py)
            la = {0: 180, 180: 0, 90: 270, 270: 90}[ang] if rot == 0 else (0 if dx > 0 else 180)
            res[num] = (round(sx + dx, 2), round(sy + dy, 2), la)
        return res

    def label(net, x, y, la, size=1.27):
        out.append('  (label "%s" (at %.2f %.2f %d) (effects (font (size %.2f %.2f)) (justify %s bottom)) (uuid %s))'
                   % (net, x, y, la, size, size, "right" if la in (180, 270) else "left", U()))

    def wire(x1, y1, x2, y2):
        out.append('  (wire (pts (xy %.2f %.2f) (xy %.2f %.2f)) (stroke (width 0) (type default)) (uuid %s))' % (x1, y1, x2, y2, U()))

    BLOCKS = [
        ("USB-C DATA, ESD, MUX, 3.3 V", ["J1", "U4", "U5", "U3", "U7"], ["C15", "C16", "C7", "C8", "R7", "R15", "C18", "C19"]),
        ("USB PD INPUT AND LOAD SWITCH", ["J2", "U2", "Q2", "Q1"], ["D1", "R1", "R2", "R3", "R4", "R5", "R6", "C1", "C2", "C3", "C4"]),
        ("5 V BUCK", ["U6"], ["L1", "C11", "R8", "R9", "R10", "R11", "R12", "R14", "C5", "C6", "C9", "C10", "C12", "C13", "C14", "C17"]),
        ("RK1828 (USB and ground only, rest not designed)", ["U1"], ["R13"]),
        ("TEST POINTS", ["TP1", "TP2", "TP3", "TP4", "TP5", "TP6"], []),
    ]
    assert {r for b_ in BLOCKS for r in b_[1] + b_[2]} == set(bb.PARTS) - bb.NO_SCHEMATIC
    SUPPLY = {"GND"}
    y0, page_w = 30.0, 0.0
    for title, mains, small in BLOCKS:
        free = list(small); x = 30.0; bottom = y0
        for ref in mains:
            lib, name, _ = lib_of(ref, None); key = load(lib, name)
            for unit, pins in sorted(pinmap[key].items()):
                xs = [p[1] for p in pins]; ys = [p[2] for p in pins]
                sx = round((x + 44.0 - min(xs)) / 2.54) * 2.54; sy = round((y0 + 22.0 + max(ys)) / 2.54) * 2.54
                pos = emit(ref, key, unit, sx, sy, 0, pins)
                seen = {}
                for num, (px, py, la) in sorted(pos.items(), key=lambda kv: (kv[1][1], kv[1][0])):
                    net = pin_net.get(ref + "." + num)
                    if net is None:
                        if ref != "U1" and (px, py) not in seen: out.append('  (no_connect (at %.2f %.2f) (uuid %s))' % (px, py, U()))
                        seen.setdefault((px, py), None); continue
                    assert seen.get((px, py), net) == net, (ref, num)
                    if (px, py) in seen: continue
                    seen[(px, py)] = net
                    sat = None
                    if la in (0, 180) and net not in SUPPLY:
                        sat = next((r for r in free if any(pin_net.get(r + "." + q) == net for q in "12")), None)
                    if sat is None: label(net, px, py, la); continue
                    free.remove(sat)
                    slib, sname, _ = lib_of(sat, None); skey = load(slib, sname)
                    near = "1" if pin_net.get(sat + ".1") == net else "2"
                    d = 1 if la == 0 else -1                      # direction away from the IC
                    cx_ = px + d * 12.7
                    far_ = "2" if near == "1" else "1"
                    geo = {q[0]: (q[1], q[2]) for q in pinmap[skey][1]}
                    TT = {0: lambda px_, py_: (px_, -py_), 90: lambda px_, py_: (-py_, -px_), 180: lambda px_, py_: (-px_, py_), 270: lambda px_, py_: (py_, px_)}
                    rot = next(r_ for r_ in (0, 90, 180, 270) if abs(TT[r_](*geo[near])[1]) < 0.01 and d * (TT[r_](*geo[far_])[0] - TT[r_](*geo[near])[0]) > 0)
                    sp = emit(sat, skey, 1, cx_, py, rot, pinmap[skey][1])
                    far = "2" if near == "1" else "1"
                    assert abs(sp[near][0] - px) < abs(sp[far][0] - px), (sat, rot)
                    wire(px, py, sp[near][0], sp[near][1])
                    if sum(1 for v in pin_net.values() if v == net) > len([1 for k_, v in pin_net.items() if v == net and (round(pos.get(k_.split(".")[1], (None, None, 0))[0] or 1e9, 2), round(pos.get(k_.split(".")[1], (None, None, 0))[1] or 1e9, 2)) == (px, py) and k_.startswith(ref + ".")]) + 1:
                        label(net, min(px, sp[near][0]) + 0.6, py, 0, 1.0)       # net continues elsewhere: name the wire
                    label(pin_net[sat + "." + far], sp[far][0], sp[far][1], la)
                x = sx + max(xs) + 44.0
                bottom = max(bottom, sy - min(ys) + 12.0)
        # parts that did not attach to an IC pin: one row below, labels on both pins
        if free:
            xx = 45.0; yy = bottom + 12.0
            for r in free:
                slib, sname, _ = lib_of(r, None); skey = load(slib, sname)
                sp = emit(r, skey, 1, round(xx / 2.54) * 2.54, round(yy / 2.54) * 2.54, 0, pinmap[skey][1])
                for q in "12": label(pin_net[r + "." + q], *sp[q])
                xx += 30.48
            bottom = yy + 22.0; x = max(x, xx + 20.0)
        out.append('  (rectangle (start 20 %.2f) (end %.2f %.2f) (stroke (width 0.3) (type dash)) (fill (type none)) (uuid %s))' % (y0 - 8, x, bottom, U()))
        out.append('  (text "%s" (at 23 %.2f 0) (effects (font (size 3 3) (thickness 0.5) bold) (justify left bottom)) (uuid %s))' % (title, y0 - 1.5, U()))
        page_w = max(page_w, x); y0 = bottom + 22.0
    PAGE_W = page_w; y = y0 - 60; rowh = 0
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
