"""Small grid maze router for the low-speed and power nets of the TokenStick board.

Works on a 0.1 mm grid, top and bottom layer, 45 degree moves, through vias.
It is called from build_board.py after the hand-defined USB routes are in place.
The result is checked with KiCad DRC; nets it cannot finish are printed.
"""
import heapq, math
import numpy as np
import pcbnew

G = 0.1
X0, Y0 = -42.5, -17.5
NX, NY = 851, 351
F, B, I = 0, 1, 2            # top, bottom, inner (inner is only an obstacle map for vias)
SQ2 = math.sqrt(2)


def run(board, net, cfg):
    OX, OY = cfg.OX, cfg.OY
    mm = pcbnew.FromMM
    own = np.zeros((3, NY, NX), dtype=np.int32)
    ids = {}
    nid = lambda name: ids.setdefault(name, len(ids) + 1)
    cx = lambda x: int(round((x - X0) / G))
    cy = lambda y: int(round((y - Y0) / G))

    def rect(layers, xa, xb, ya, yb, v, arr=None):
        arr = own if arr is None else arr
        xa, xb, ya, yb = xa - G / 2, xb + G / 2, ya - G / 2, yb + G / 2
        a, bq = max(0, int(math.ceil((xa - X0) / G - 1e-6))), min(NX - 1, int(math.floor((xb - X0) / G + 1e-6)))
        c, d = max(0, int(math.ceil((ya - Y0) / G - 1e-6))), min(NY - 1, int(math.floor((yb - Y0) / G + 1e-6)))
        if a <= bq and c <= d:
            for l in layers: arr[l, c:d + 1, a:bq + 1] = v

    def seg(layers, x1, y1, x2, y2, w, v, arr=None):
        arr = own if arr is None else arr
        r = w / 2 + G / 2
        a, bq = max(0, cx(min(x1, x2) - r) - 1), min(NX - 1, cx(max(x1, x2) + r) + 1)
        c, d = max(0, cy(min(y1, y2) - r) - 1), min(NY - 1, cy(max(y1, y2) + r) + 1)
        xs = X0 + G * np.arange(a, bq + 1)[None, :]; ys = Y0 + G * np.arange(c, d + 1)[:, None]
        dx, dy = x2 - x1, y2 - y1; L2 = dx * dx + dy * dy
        t = np.clip(((xs - x1) * dx + (ys - y1) * dy) / L2, 0, 1) if L2 > 0 else 0 * xs * ys
        m = (xs - x1 - t * dx) ** 2 + (ys - y1 - t * dy) ** 2 <= r * r + 1e-9
        for l in layers: arr[l, c:d + 1, a:bq + 1][m] = v

    # ---- obstacle map: board edge, zones, pads, existing tracks and vias
    own[:, :5, :] = -1; own[:, -5:, :] = -1; own[:, :, :5] = -1; own[:, :, -5:] = -1
    for name, xa, xb, ya, yb in cfg.ZONES: rect([F], xa, xb, ya, yb, nid(name))
    pads = {}      # net -> [(ref, number, x, y, bbox, through)]
    for fp in board.GetFootprints():
        ref = fp.GetReference()
        for pad in fp.Pads():
            bb = pad.GetBoundingBox()
            box = (pcbnew.ToMM(bb.GetLeft()) - OX, pcbnew.ToMM(bb.GetRight()) - OX, OY - pcbnew.ToMM(bb.GetBottom()), OY - pcbnew.ToMM(bb.GetTop()))
            th = pad.GetAttribute() in (pcbnew.PAD_ATTRIB_PTH, pcbnew.PAD_ATTRIB_NPTH)
            name = pad.GetNetname()
            v = nid(name) if name else -1
            if ref == "LG1": v = -1
            rect([F, B, I] if th else [F], *box, v)
            if name and pad.GetNumber():
                p = pad.GetPosition()
                pads.setdefault(name, []).append((ref, pad.GetNumber(), pcbnew.ToMM(p.x) - OX, OY - pcbnew.ToMM(p.y), box, th))
    lay = {"F.Cu": [F], "B.Cu": [B], "In2.Cu": [I]}
    for name, layer, w, pts in cfg.TRACKS:
        for a, c in zip(pts, pts[1:]): seg(lay[layer], *a, *c, w, nid(name))
    holes = np.zeros((1, NY, NX), dtype=bool)        # keep-out around every via hole, same net included
    for name, x, y in cfg.VIAS:
        seg([F, B, I], x, y, x, y, cfg.VIA_D, nid(name)); seg([0], x, y, x, y, 1.1, True, arr=holes)

    def blocked(layer, n, margin, win):
        c, d, a, bq = win
        pad = int(math.ceil(margin / G)) + 1
        c0, d0, a0, b0 = max(0, c - pad), min(NY, d + pad), max(0, a - pad), min(NX, bq + pad)
        f = (own[layer, c0:d0, a0:b0] != 0) & (own[layer, c0:d0, a0:b0] != n)
        out = f.copy()
        for j in range(-pad, pad + 1):
            for i in range(-pad, pad + 1):
                if (i or j) and math.hypot(i, j) * G <= margin + 1e-9:
                    sh = np.zeros_like(f)
                    ys = slice(max(0, j), f.shape[0] + min(0, j)); yd = slice(max(0, -j), f.shape[0] + min(0, -j))
                    xs = slice(max(0, i), f.shape[1] + min(0, i)); xd = slice(max(0, -i), f.shape[1] + min(0, -i))
                    sh[ys, xs] = f[yd, xd]; out |= sh
        return out[c - c0:c - c0 + (d - c), a - a0:a - a0 + (bq - a)]

    def add_track(name, layer, w, pts):
        for a, c in zip(pts, pts[1:]):
            if a == c: continue
            t = pcbnew.PCB_TRACK(board); t.SetStart(cfg.P(*a)); t.SetEnd(cfg.P(*c)); t.SetWidth(mm(w))
            t.SetLayer(pcbnew.F_Cu if layer == F else pcbnew.B_Cu); t.SetNet(net(name)); board.Add(t)
            seg([layer], *a, *c, w, nid(name))

    def add_via(name, x, y):
        v = pcbnew.PCB_VIA(board); v.SetPosition(cfg.P(x, y)); v.SetWidth(mm(cfg.VIA_D)); v.SetDrill(mm(cfg.VIA_DRILL))
        v.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu); v.SetNet(net(name)); board.Add(v)
        seg([F, B, I], x, y, x, y, cfg.VIA_D, nid(name)); seg([0], x, y, x, y, 1.1, True, arr=holes)

    def route(name, w, src, goal_fn, span, via_goal=False, hint=None):
        """A* from the cells of pad `src`. goal_fn(layer, iy, ix) says where to stop. Returns True if routed."""
        n = nid(name); sx, sy = src[2], src[3]
        hx, hy = hint if hint else (sx, sy)
        a, bq = max(1, cx(min(sx, hx) - span)), min(NX - 1, cx(max(sx, hx) + span))
        c, d = max(1, cy(min(sy, hy) - span)), min(NY - 1, cy(max(sy, hy) + span))
        win = (c, d, a, bq)
        m_t = w / 2 + 0.1 + G / 2; m_v = cfg.VIA_D / 2 + 0.1 + G / 2
        blk = [blocked(F, n, m_t, win), blocked(B, n, m_t, win)]
        vb = blocked(F, n, m_v, win) | blocked(B, n, m_v, win) | blocked(I, n, m_v, win) | holes[0, c:d, a:bq]
        padF = np.zeros_like(vb)          # no via inside any pad
        ownF = own[F, c:d, a:bq]
        H, W = vb.shape
        start_layers = [F, B] if src[5] else [F]
        box = src[4]; heap = []; best = {}; prev = {}
        for l in start_layers:
            k = (l, cy(sy) - c, cx(sx) - a)
            if 0 <= k[1] < H and 0 <= k[2] < W: best[k] = 0.0; heapq.heappush(heap, (0.0, k))
        tx, ty = cx(hx) - a, cy(hy) - c
        moves = [(0, 1, 1), (0, -1, 1), (1, 0, 1), (-1, 0, 1), (1, 1, SQ2), (1, -1, SQ2), (-1, 1, SQ2), (-1, -1, SQ2)]
        inside_src = lambda iy, ix: box[0] - 0.05 <= X0 + G * (ix + a) <= box[1] + 0.05 and box[2] - 0.05 <= Y0 + G * (iy + c) <= box[3] + 0.05
        end = None
        while heap:
            cost, k = heapq.heappop(heap)
            if cost > best.get(k, 1e18): continue
            l, iy, ix = k
            if goal_fn(l, iy + c, ix + a) and not (via_goal and (vb[iy, ix] or inside_src(iy, ix))):
                end = k; break
            for dy, dx, cst in moves:
                jy, jx = iy + dy, ix + dx
                if not (0 <= jy < H and 0 <= jx < W): continue
                if blk[l][jy, jx] and not inside_src(jy, jx): continue
                if dx and dy and (blk[l][iy, jx] or blk[l][jy, ix]) and not inside_src(iy, ix): continue
                nk = (l, jy, jx); nc = cost + cst + (0.3 if l == B else 0)
                if nc < best.get(nk, 1e18):
                    best[nk] = nc; prev[nk] = k
                    heapq.heappush(heap, (nc + 0.0 * (abs(jx - tx) + abs(jy - ty)), nk))
            if not via_goal and not vb[iy, ix] and ownF[iy, ix] in (0,) and own[B, iy + c, ix + a] == 0:
                nk = (1 - l, iy, ix); nc = cost + 25
                if nc < best.get(nk, 1e18):
                    best[nk] = nc; prev[nk] = k; heapq.heappush(heap, (nc, nk))
        if end is None: return False
        path = [end]
        while path[-1] in prev: path.append(prev[path[-1]])
        path.reverse()
        pt = lambda k: (round(X0 + G * (k[2] + a), 3), round(Y0 + G * (k[1] + c), 3))
        run_pts = [(sx, sy), pt(path[0])]; layer = path[0][0]
        for q, k in zip(path, path[1:]):
            if k[0] != q[0]:
                add_track(name, layer, w, simplify(run_pts)); add_via(name, *pt(q)); layer = k[0]; run_pts = [pt(k)]
            else: run_pts.append(pt(k))
        add_track(name, layer, w, simplify(run_pts))
        if via_goal: add_via(name, *pt(end))
        return pt(end)

    def simplify(pts):
        out = [pts[0]]
        for i in range(1, len(pts) - 1):
            ax, ay = pts[i][0] - out[-1][0], pts[i][1] - out[-1][1]; bx, by = pts[i + 1][0] - pts[i][0], pts[i + 1][1] - pts[i][1]
            if abs(ax * by - ay * bx) > 1e-9: out.append(pts[i])
        out.append(pts[-1]); return out

    failed = []
    # ---- signal and power nets: grow a tree pad by pad
    order = [n for n in cfg.NETS if n != "GND" and n not in cfg.HAND_ROUTED]
    order.sort(key=lambda n: (n not in cfg.ROUTE_FIRST, n not in cfg.POWER_NETS, len(pads.get(n, []))))
    for name in order:
        n = nid(name); wide = name in cfg.POWER_NETS
        todo = list(pads.get(name, []))
        if len(todo) < 2: continue
        # seed: copper of this net that already exists (zone, hand track) or the first pad
        tree = np.zeros((2, NY, NX), dtype=bool)
        def mark_pad(p):
            rect([F, B] if p[5] else [F], *p[4], True, arr=tree)
        for z in cfg.ZONES:
            if z[0] == name: rect([F], *z[1:], True, arr=tree)
        for tn, layer, tw, pts in cfg.TRACKS:
            if tn == name:
                for a, c in zip(pts, pts[1:]): seg(lay[layer][:1] if layer != "In2.Cu" else [], *a, *c, tw, True, arr=tree)
        for vn, vx, vy in cfg.VIAS:
            if vn == name: seg([F, B], vx, vy, vx, vy, cfg.VIA_D, True, arr=tree)
        if not tree.any():
            mark_pad(todo[0])
        done = [p for p in todo if tree[F, cy(p[3]), cx(p[2])]]
        for p in done: mark_pad(p)
        todo = [p for p in todo if p not in done]
        while todo:
            ty, tx = np.nonzero(tree[F] | tree[B])
            d2 = lambda p: np.hypot(X0 + G * tx - p[2], Y0 + G * ty - p[3])
            p = min(todo, key=lambda q: float(d2(q).min())); todo.remove(p)
            j = int(np.argmin(d2(p))); hint = (X0 + G * tx[j], Y0 + G * ty[j])
            before = own[:2] == n
            ok = False
            for span in (3.0, 8.0, 20.0):
                ok = route(name, cfg.PWR if wide and p[0] in cfg.POWER_REFS else 0.2, p, lambda l, iy, ix: tree[l, iy, ix], span, hint=hint)
                if ok: break
            if not ok: failed.append("%s: %s.%s" % (name, p[0], p[1]))
            else:
                tree |= (own[:2] == n) & ~before
                mark_pad(p)
    # ---- ground: pins next to an exposed ground pad go to that pad, every other SMD ground pad gets a via
    big = lambda p: (p[4][1] - p[4][0]) * (p[4][3] - p[4][2]) > 1.0
    gp = pads.get("GND", [])
    eps = {p[0]: p for p in gp if big(p) and not p[5]}
    gn = nid("GND")
    for p in eps.values():          # two vias inside each exposed pad, where the other layers are free
        xa, xb, ya, yb = p[4]; win = (cy(ya), cy(yb) + 1, cx(xa), cx(xb) + 1)
        m_v = cfg.VIA_D / 2 + 0.1 + G / 2
        bad = blocked(B, gn, m_v, win) | blocked(I, gn, m_v, win) | holes[0, win[0]:win[1], win[2]:win[3]]
        cand = [(X0 + G * (ix + win[2]), Y0 + G * (iy + win[0])) for iy in range(bad.shape[0]) for ix in range(bad.shape[1])
                if not bad[iy, ix] and xa + 0.3 <= X0 + G * (ix + win[2]) <= xb - 0.3 and ya + 0.3 <= Y0 + G * (iy + win[0]) <= yb - 0.3]
        chosen = []
        for q in sorted(cand, key=lambda q: -math.hypot(q[0] - p[2], q[1] - p[3])):
            if all(math.hypot(q[0] - r[0], q[1] - r[1]) >= 0.9 for r in chosen): chosen.append(q)
            if len(chosen) == 2: break
        for q in chosen: add_via("GND", round(q[0], 2), round(q[1], 2))
        if not chosen: failed.append("GND: no via in %s.%s" % (p[0], p[1]))
    seen_pos = set()
    for p in gp:
        if p[5] or p[0] == "U1" or big(p) or (round(p[2], 2), round(p[3], 2)) in seen_pos: continue
        seen_pos.add((round(p[2], 2), round(p[3], 2)))
        ok = False
        if p[0] in eps:
            ep = np.zeros((2, NY, NX), dtype=bool); rect([F], *eps[p[0]][4], True, arr=ep)
            ok = route("GND", 0.2, p, lambda l, iy, ix: ep[l, iy, ix], 3.0, hint=(eps[p[0]][2], eps[p[0]][3]))
        for span in (1.5, 4.0):
            if ok: break
            ok = route("GND", 0.2, p, lambda l, iy, ix: True, span, via_goal=True)
        if not ok: failed.append("GND: %s.%s" % (p[0], p[1]))
    print("autoroute: %d not routed%s" % (len(failed), (": " + ", ".join(failed)) if failed else ""))
