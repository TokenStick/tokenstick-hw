#!/usr/bin/env python3
"""First-order impedance estimate for the outer layers (IPC-2141 microstrip formulas).
Outer prepreg and dielectric constant are JLCPCB's published values for their 6-layer impedance stackup.
The fab's own calculator decides the final widths; this only checks that the drawn geometry is in range."""
import math
H, ER, T = 0.10, 4.1, 0.035          # prepreg 3313 thickness (mm), dielectric constant, outer copper (mm)

def z0(w): return 87.0 / math.sqrt(ER + 1.41) * math.log(5.98 * H / (0.8 * w + T))
def zdiff(w, s): return 2 * z0(w) * (1 - 0.48 * math.exp(-0.96 * s / H))

if __name__ == "__main__":
    print("single-ended: " + ", ".join("w=%.3f -> %.1f ohm" % (w, z0(w)) for w in (0.10, 0.125, 0.15, 0.175, 0.20)))
    for w, s in ((0.10, 0.10), (0.125, 0.15), (0.15, 0.15), (0.15, 0.20), (0.175, 0.15), (0.175, 0.20), (0.20, 0.20)):
        print("differential: w=%.3f s=%.3f -> %.1f ohm" % (w, s, zdiff(w, s)))
