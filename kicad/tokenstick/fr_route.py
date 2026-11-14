#!/usr/bin/env python3
"""Route the board with fastroute (https://github.com/parisxmas/fastroute, a Rust port of Freerouting).

  python3 fr_route.py full   <fastroute binary> [seconds]   # nothing pre-routed
  python3 fr_route.py rest   <fastroute binary> [seconds]   # hand-defined USB routes kept, fastroute does the rest

Writes fr_<mode>.kicad_pcb next to this script and prints a DRC summary. Used to compare with autoroute.py.
"""
import collections, os, re, subprocess, sys
import pcbnew
import build_board as bb

HERE = os.path.dirname(os.path.abspath(__file__))
mode, binary = sys.argv[1], sys.argv[2]
seconds = sys.argv[3] if len(sys.argv) > 3 else "240"
work = "/tmp/fr_" + mode; os.makedirs(work, exist_ok=True)
src = os.path.join(work, "in.kicad_pcb"); dsn = os.path.join(work, "board.dsn"); ses = os.path.join(work, "board.ses")
out = os.path.join(HERE, "fr_%s.kicad_pcb" % mode)

pcbnew.SaveBoard(src, bb.build(hand=(mode == "rest"), auto=False))
board = pcbnew.LoadBoard(src)
assert pcbnew.ExportSpecctraDSN(board, dsn)
pairs = [("C_TX1_P", "C_TX1_N"), ("C_RX1_P", "C_RX1_N"), ("C_TX2_P", "C_TX2_N"), ("C_RX2_P", "C_RX2_N"), ("USB_SSTX_P", "USB_SSTX_N"),
         ("Net-(C15-1)", "Net-(C16-1)"), ("USB_SSRX_P", "USB_SSRX_N"), ("USB_DP", "USB_DM")]
pf = os.path.join(work, "pairs.txt")
open(pf, "w").write("".join("pair %s %s gap=0.15\n" % p for p in pairs))
cmd = [binary, "-de", dsn, "-do", ses, "--max-time=" + seconds, "--report=" + os.path.join(work, "report.json"),
       "--router.neck_width_um=100", "--router.min_trace_width_um=100"] + (["--pairs=" + pf] if mode == "full" else [])
if not (os.path.exists(ses) and "--reuse" in sys.argv):
    print(" ".join(cmd)); r = subprocess.run(cmd, capture_output=True, text=True)
    print("\n".join((r.stdout + r.stderr).strip().split("\n")[-4:]))
assert os.path.exists(ses), "no session file"
# KiCad 7 can import a session only from the GUI, so the wires and vias are read here
text = open(ses).read()
res = float(re.search(r'\(resolution um (\d+)\)', text).group(1)) * 1000.0     # units per mm
nets = {n.GetNetname(): n for n in board.GetNetInfo().NetsByName().values()}
start = text.index("(network_out")
for m in re.finditer(r'\(net\s+("([^"]+)"|\S+)(.*?)(?=\n\s*\(net\s|\Z)', text[start:], re.S):
    name = m.group(2) or m.group(1); net = nets[name]; body = m.group(3)
    for w in re.finditer(r'\(path\s+(\S+)\s+(\d+)\s+([-\d\s]+)\)', body):
        c = [int(v) for v in w.group(3).split()]
        pts = list(zip(c[0::2], c[1::2]))
        for a_, b_ in zip(pts, pts[1:]):
            t = pcbnew.PCB_TRACK(board); t.SetStart(pcbnew.VECTOR2I(pcbnew.FromMM(a_[0] / res), pcbnew.FromMM(-a_[1] / res)))
            t.SetEnd(pcbnew.VECTOR2I(pcbnew.FromMM(b_[0] / res), pcbnew.FromMM(-b_[1] / res))); t.SetWidth(pcbnew.FromMM(int(w.group(2)) / res))
            t.SetLayer(board.GetLayerID(w.group(1))); t.SetNet(net); board.Add(t)
    for v in re.finditer(r'\(via\s+("[^"]+"|\S+)\s+(-?\d+)\s+(-?\d+)', body):
        via = pcbnew.PCB_VIA(board); via.SetPosition(pcbnew.VECTOR2I(pcbnew.FromMM(int(v.group(2)) / res), pcbnew.FromMM(-int(v.group(3)) / res)))
        via.SetWidth(pcbnew.FromMM(bb.VIA_D)); via.SetDrill(pcbnew.FromMM(bb.VIA_DRILL)); via.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu); via.SetNet(net); board.Add(via)
pcbnew.ZONE_FILLER(board).Fill(board.Zones())
pcbnew.SaveBoard(out, board)
rpt = os.path.join(work, "drc.rpt")
pcbnew.WriteDRCReport(pcbnew.LoadBoard(out), rpt, pcbnew.EDA_UNITS_MILLIMETRES, True)
t = open(rpt).read()
kinds = collections.Counter(re.findall(r'^\[(\w+)\]', t, re.M))
un = collections.Counter()
for bl in re.split(r'\n(?=\[)', t):
    if bl.startswith("[unconnected_items]"):
        for n in set(re.findall(r'\[([^\]]+)\]', "\n".join(bl.split("\n")[2:]))): un[n] += 1
show = {k: v for k, v in kinds.items() if k in ("clearance", "shorting_items", "tracks_crossing", "hole_clearance", "unconnected_items", "courtyards_overlap", "track_dangling", "via_dangling")}
print("tracks+vias:", len(board.GetTracks()), "| DRC:", show)
print("unconnected by net:", un.most_common(12))
