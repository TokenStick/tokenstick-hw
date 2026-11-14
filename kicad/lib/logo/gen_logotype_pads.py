import json, sys, importlib.util, io, contextlib
from shapely.geometry import LineString, box
from shapely.ops import unary_union
from shapely import affinity
src = open("gen_logotype.py").read().split("# fade as a horizontal line screen")[0]
ns = {}; exec(src.replace('sys.argv[1]','"x"'), ns)
parts, W, mid, px = ns["parts"], ns["W"], ns["mid"], ns["px"]
ROW = 0.07; PER = 10; TOL = 0.03
H = 64*px; top = mid + H/2
# include ascender overshoot: use bounds of all parts
allg = unary_union([g for g,_ in parts]); miny, maxy = allg.bounds[1], allg.bounds[3]
import math
r0 = math.floor((miny-mid)/ROW)-1; r1 = math.ceil((maxy-mid)/ROW)+1
rects = []   # per part: list of [x0,x1,rowstart,rowend]
for g,op in parts:
    on = PER if op>=0.99 else max(2, round(op*PER))
    open_ = {}
    for r in range(r0, r1):
        if (r % PER) >= on: 
            for k in list(open_): rects.append(open_.pop(k))
            continue
        yc = mid + (r+0.5)*ROW
        inter = g.intersection(LineString([(-5,yc),(W+5,yc)]))
        segs = [s for s in (inter.geoms if hasattr(inter,"geoms") else [inter]) if s.geom_type=="LineString" and s.length>0.06]
        runs = [(min(s.coords[0][0],s.coords[-1][0]), max(s.coords[0][0],s.coords[-1][0])) for s in segs]
        new = {}
        for a,b in runs:
            hit=None
            for k,v in open_.items():
                if abs(v[0]-a)<TOL and abs(v[1]-b)<TOL and v[3]==r-1: hit=k;break
            if hit is not None:
                v=open_.pop(hit); v[3]=r; new[hit]=v
            else: new[(a,b,r)]=[a,b,r,r]
        for k in open_: rects.append(open_[k])
        open_=new
    rects += list(open_.values())
pads=[]
for a,b,ra,rb in rects:
    x=(a+b)/2 - W/2; y=((ra+rb+1)/2)*ROW
    pads.append({"x":round(x,2),"y":round(y,2),"w":round(b-a,2),"h":round((rb-ra+1)*ROW,2),"shape":"rect","paste":False})
[p.update(number="1") for p in pads]
print(len(pads), "pads; min w", min(p["w"] for p in pads), "min h", min(p["h"] for p in pads))
json.dump(pads, open("pads.json","w"), separators=(",",":"))
svg=['<svg xmlns="http://www.w3.org/2000/svg" viewBox="-14 -3.2 28 6.4" width="1400"><rect x="-50" y="-50" width="100" height="100" fill="#111"/>']
for p in pads: svg.append('<rect fill="#d4af37" x="%.3f" y="%.3f" width="%.3f" height="%.3f"/>'%(p["x"]-p["w"]/2,-p["y"]-p["h"]/2,p["w"],p["h"]))
svg.append("</svg>"); open("pads.svg","w").write("\n".join(svg))
