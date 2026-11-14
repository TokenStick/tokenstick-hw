#!/usr/bin/env python3
"""Run DRC on tokenstick.kicad_pcb and print a short summary."""
import collections, os, re, sys
import pcbnew
here = os.path.dirname(os.path.abspath(__file__))
b = pcbnew.LoadBoard(os.path.join(here, "tokenstick.kicad_pcb"))
rpt = os.path.join(here, "drc.rpt")
pcbnew.WriteDRCReport(b, rpt, pcbnew.EDA_UNITS_MILLIMETRES, True)
t = open(rpt).read()
print(collections.Counter(re.findall(r'^\[(\w+)\]', t, re.M)))
skip = set(sys.argv[1:])
n = 0
for bl in re.split(r'\n(?=\[)', t):
    k = re.match(r'\[(\w+)\]', bl)
    if k and k.group(1) not in skip:
        print(" | ".join(l.strip() for l in bl.strip().split("\n"))[:300]); n += 1
        if n > 30: break
