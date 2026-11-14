#!/usr/bin/env python3
"""2D field solver (finite differences) for outer-layer tracks: single-ended and edge-coupled pairs,
with a trapezoidal track cross-section and solder mask, as JLCPCB's impedance calculator models them.

Parameters published by JLCPCB (impedance page and calculator guide):
  outer prepreg 3313: nominal 0.0994 mm, "use 3.5 mil" (0.0889 mm) for tracks on the outer layers, dielectric constant 4.05 to 4.1
  outer copper 1.6 mil, track top width = base width - 0.7 mil
  solder mask 1.2 mil on the laminate and between tracks, 0.6 mil on copper, dielectric constant 3.8

Run:  python3 impedance_fd.py      (needs numpy and scipy)
"""
import numpy as np
import scipy.sparse as sp
import scipy.sparse.linalg as spl

MIL = 0.0254
C0 = 299792458.0
EPS0 = 8.8541878128e-12
T_CU, ETCH = 1.6 * MIL, 0.7 * MIL
MASK_BASE, MASK_CU, MASK_ER = 1.2 * MIL, 0.6 * MIL, 3.8


def capacitance(w, s, h, er, mask, odd=True, d=0.0025, dielectric=True):
    """Capacitance per metre of one track to ground. s=None: single track (half of it is modelled).
    Pair: the plane x=0 is the middle of the gap; odd mode puts 0 V there, even mode a magnetic wall."""
    X, Y = max(1.6, 8 * h + w), max(1.2, 10 * h)
    nx, ny = int(round(X / d)), int(round(Y / d))
    xc = (np.arange(nx) + 0.5) * d; yc = (np.arange(ny) + 0.5) * d          # cell centres
    XX, YY = np.meshgrid(xc, yc)
    x0 = 0.0 if s is None else s / 2                                          # inner edge of the track base
    x1 = w / 2 if s is None else s / 2 + w
    inset = ETCH / 2 * np.clip((YY - h) / T_CU, 0, 1)                        # trapezoid: narrower towards the top
    left = x0 + (0 if s is None else inset); right = x1 - inset
    cu = (YY > h) & (YY < h + T_CU) & (XX > left) & (XX < right)
    eps = np.ones((ny, nx))
    if dielectric:
        eps[YY < h] = er
        if mask:
            m = (YY >= h) & (YY < h + MASK_BASE)                              # on the laminate and in the gap
            m |= (YY >= h) & (YY < h + T_CU + MASK_CU) & (XX > left - MASK_CU) & (XX < right + MASK_CU)   # on the copper
            eps[m & ~cu] = MASK_ER
    # nodes: (ny+1) x (nx+1); edge permittivity = mean of the two cells beside the edge
    N = (ny + 1) * (nx + 1); idx = lambda j, i: j * (nx + 1) + i
    ep = np.pad(eps, 1, mode="edge")
    ex = 0.5 * (ep[:-1, 1:-1] + ep[1:, 1:-1])            # horizontal edges, shape (ny+1, nx)
    ey = 0.5 * (ep[1:-1, :-1] + ep[1:-1, 1:])            # vertical edges, shape (ny, nx+1)
    J, I = np.meshgrid(np.arange(ny + 1), np.arange(nx), indexing="ij")
    a, b, v = idx(J, I).ravel(), idx(J, I + 1).ravel(), ex.ravel()
    J2, I2 = np.meshgrid(np.arange(ny), np.arange(nx + 1), indexing="ij")
    a = np.concatenate([a, idx(J2, I2).ravel()]); b = np.concatenate([b, idx(J2 + 1, I2).ravel()]); v = np.concatenate([v, ey.ravel()])
    A = sp.coo_matrix((np.concatenate([v, v, -v, -v]), (np.concatenate([a, b, a, b]), np.concatenate([a, b, b, a]))), shape=(N, N)).tocsr()
    # fixed potentials: ground plane, far walls, the copper; odd mode: the symmetry plane
    fixed = np.zeros((ny + 1, nx + 1), dtype=bool); val = np.zeros((ny + 1, nx + 1))
    fixed[0, :] = True; fixed[-1, :] = True; fixed[:, -1] = True
    if odd and s is not None: fixed[:, 0] = True
    cun = np.zeros((ny + 1, nx + 1), dtype=bool)          # a node is copper if any cell around it is
    cun[:-1, :-1] |= cu; cun[1:, :-1] |= cu; cun[:-1, 1:] |= cu; cun[1:, 1:] |= cu
    fixed |= cun; val[cun] = 1.0
    f = fixed.ravel(); u = val.ravel().copy()
    free = np.flatnonzero(~f); fx = np.flatnonzero(f)
    u[free] = spl.spsolve(A[free][:, free].tocsc(), -A[free][:, fx] @ u[fx])
    energy = 0.5 * EPS0 * float(u @ (A @ u))             # per metre, half structure
    c = 2 * energy                                        # V = 1
    return 2 * c if s is None else c                      # single track: both halves


def z_single(w, h, er, mask):
    return 1 / (C0 * np.sqrt(capacitance(w, None, h, er, mask) * capacitance(w, None, h, er, mask, dielectric=False)))


def z_diff(w, s, h, er, mask):
    return 2 / (C0 * np.sqrt(capacitance(w, s, h, er, mask) * capacitance(w, s, h, er, mask, dielectric=False)))


if __name__ == "__main__":
    for h, er in ((0.0889, 4.05), (0.0994, 4.1)):
        print("prepreg %.4f mm, er %.2f" % (h, er))
        for w, s in ((0.15, 0.15), (0.14, 0.15), (0.13, 0.15), (0.125, 0.15), (0.12, 0.15), (0.15, 0.20), (0.14, 0.20)):
            print("  pair w=%.3f s=%.3f: %.1f ohm under mask, %.1f ohm bare" % (w, s, z_diff(w, s, h, er, True), z_diff(w, s, h, er, False)))
        for w in (0.15, 0.10):
            print("  single w=%.3f: %.1f ohm under mask, %.1f ohm bare" % (w, z_single(w, h, er, True), z_single(w, h, er, False)))
