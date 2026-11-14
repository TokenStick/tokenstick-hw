#!/usr/bin/env python3
"""Compare a netlist exported from the schematic (kicad-cli sch export netlist) with the netlist in build_board.py.
The comparison is by connectivity, not by net name."""
import csv, os, re, sys
import build_board as bb
here = os.path.dirname(os.path.abspath(__file__))
exp = {}
for n, p in bb.NETS.items():
    for q in p.split(): exp[q] = n
for ball, pname in list(csv.reader(open(os.path.join(here, "..", "lib", "rk182x_pins.csv"))))[1:]:
    if (pname.startswith("VSS_") and pname != "VSS_SENSE_N") or pname.startswith("AVSS_"): exp["U1." + ball] = "GND"
t = open(sys.argv[1]).read(); got = {}
for m in re.finditer(r'\(net \(code "?\d+"?\) \(name "([^"]*)"\)(.*?)(?=\(net \(code|\Z)', t, re.S):
    for r, p in re.findall(r'\(node \(ref "([^"]+)"\) \(pin "([^"]+)"\)', m.group(2)): got[r + "." + p] = m.group(1)
a2b, b2a, bad = {}, {}, []
for k, n in exp.items():
    g = got.get(k)
    if g is None or a2b.setdefault(n, g) != g or b2a.setdefault(g, n) != n: bad.append((k, n, g))
extra = [k for k, g in got.items() if k not in exp and g in b2a]
print("pins expected %d, wrong %d %s, pins wrongly joined to a net %d %s" % (len(exp), len(bad), bad[:5], len(extra), extra[:5]))
sys.exit(1 if bad or extra else 0)
