import sys, json
from fontTools.ttLib import TTFont
from fontTools.pens.recordingPen import DecomposingRecordingPen
from shapely.geometry import Polygon, box, Point, MultiPolygon
from shapely.ops import unary_union
from shapely import affinity

FONT = "inter-tight-latin-600-normal.woff"  # from @fontsource/inter-tight (SIL OFL)
f = TTFont(FONT); gs = f.getGlyphSet(); cmap = f.getBestCmap(); upm = f["head"].unitsPerEm

def flat(p0, pts, n=8):
    out=[]
    if len(pts)==2:  # quadratic
        for i in range(1,n+1):
            t=i/n; out.append(((1-t)**2*p0[0]+2*(1-t)*t*pts[0][0]+t*t*pts[1][0],(1-t)**2*p0[1]+2*(1-t)*t*pts[0][1]+t*t*pts[1][1]))
    else:
        a,b,c=pts
        for i in range(1,n+1):
            t=i/n; u=1-t
            out.append((u**3*p0[0]+3*u*u*t*a[0]+3*u*t*t*b[0]+t**3*c[0], u**3*p0[1]+3*u*u*t*a[1]+3*u*t*t*b[1]+t**3*c[1]))
    return out

def glyph(ch):
    pen = DecomposingRecordingPen(gs); g = gs[cmap[ord(ch)]]; g.draw(pen)
    contours=[]; cur=[]
    for op,args in pen.value:
        if op=="moveTo": cur=[args[0]]
        elif op=="lineTo": cur.append(args[0])
        elif op=="curveTo": cur += flat(cur[-1], args)
        elif op=="qCurveTo":
            pts=list(args); p0=cur[-1]
            # expand implied on-curve points
            for i in range(len(pts)-1):
                c=pts[i]; e = pts[i+1] if i==len(pts)-2 else ((pts[i][0]+pts[i+1][0])/2,(pts[i][1]+pts[i+1][1])/2)
                cur += flat(p0,[c,e]); p0=e
        elif op in("closePath","endPath"):
            if len(cur)>2: contours.append(cur)
            cur=[]
    shape=None
    for c in contours:
        p=Polygon(c).buffer(0)
        shape = p if shape is None else shape.symmetric_difference(p)
    return shape, g.width

H = 4.2            # port height in mm (64 px in the design)
px = H/64.0        # mm per design px
fs = 80*px         # font size in mm
sc = fs/upm
ls = -0.04*fs
def rr(x,y,w,h,r): return box(x+r,y,x+w-r,y+h).union(box(x,y+r,x+w,y+h-r)).union(unary_union([Point(cx,cy).buffer(r,32) for cx in(x+r,x+w-r) for cy in(y+r,y+h-r)]))

asc=f["hhea"].ascent; desc=f["hhea"].descent
# line box is fs tall (line-height 1); baseline position inside it
base = -(fs - (asc-desc)*sc)/2 - asc*sc      # y of baseline, with line box top at 0 (y down negative)
mid = -fs/2
parts=[]   # (geometry, opacity)
x=0
port = rr(x, mid-32*px, 22*px, 64*px, 11*px).difference(rr(x+4*px, mid-28*px, 14*px, 56*px, 7*px)).union(rr(x+9*px, mid-17*px, 4*px, 34*px, 2*px))
parts.append((port,1.0)); x += 22*px+14*px
for ch,op in zip("tokenstick",[1,1,1,1,1,.82,.66,.5,.36,.24]):
    g,w = glyph(ch)
    g = affinity.translate(affinity.scale(g, sc, sc, origin=(0,0)), x, base)
    parts.append((g,op)); x += w*sc + ls
x += 10*px
parts.append((rr(x, mid-32*px, 4*px, 64*px, 2*px), 0.35)); x += 4*px
W = x
# fade as a horizontal line screen: period P, copper duty = opacity
P = 0.70
def screen(g, op):
    if op>=0.99: return g
    minx,miny,maxx,maxy = g.bounds
    stripes=[]; y = mid - 40*P
    while y < maxy+P:
        if y+P > miny: stripes.append(box(minx-1, y, maxx+1, y+P*op))
        y += P
    return g.intersection(unary_union(stripes))
cu=[]; 
for g,op in parts: cu.append(screen(g,op))
cu = unary_union(cu)
cu = affinity.translate(cu, -W/2, -mid)     # centre on origin
def polys(g):
    gs_ = g.geoms if hasattr(g,"geoms") else [g]
    out=[]
    for p in gs_:
        if p.is_empty or p.geom_type!="Polygon": continue
        if p.interiors:
            # cut holes open: split along a vertical line through each hole
            xs=[i.centroid.x for i in p.interiors]; pieces=[p]
            for cx in xs:
                nxt=[]
                for q in pieces:
                    a=q.intersection(box(-1e3,-1e3,cx,1e3)); b=q.intersection(box(cx,-1e3,1e3,1e3))
                    for r in (a,b):
                        for s in (r.geoms if hasattr(r,"geoms") else [r]):
                            if s.geom_type=="Polygon" and not s.is_empty: nxt.append(s)
                pieces=nxt
            out += [q for q in pieces]
        else: out.append(p)
    return [q for q in out if q.area>0.002 and not q.interiors] 
ps = polys(cu)
minw = 1e9
lines=['(footprint "TokenStick_Logotype_%.1fmm" (version 20221018) (generator tokenstick_logo)'%W,'  (layer "F.Cu")','  (descr "TokenStick logotype, exposed copper (ENIG)")','  (attr board_only exclude_from_pos_files exclude_from_bom)',
 '  (fp_text reference "REF**" (at 0 %.2f) (layer "F.Fab") (effects (font (size 0.5 0.5) (thickness 0.08))))'%(-fs/2-0.5),
 '  (fp_text value "TokenStick_Logotype" (at 0 %.2f) (layer "F.Fab") (effects (font (size 0.5 0.5) (thickness 0.08))))'%(fs/2+0.5)]
for layer in ("F.Cu","F.Mask"):
    for p in ps:
        pts=" ".join("(xy %.3f %.3f)"%(a,-b) for a,b in list(p.exterior.coords)[:-1])
        lines.append('  (fp_poly (pts %s) (stroke (width 0) (type solid)) (fill solid) (layer "%s"))'%(pts,layer))
lines.append(")")
open(sys.argv[1],"w").write("\n".join(lines)+"\n")
print("width %.2f mm, font %.2f mm, polys %d, bounds %s"%(W, fs, len(ps), [round(v,2) for v in cu.bounds]))
# preview svg
b=cu.bounds
svg=['<svg xmlns="http://www.w3.org/2000/svg" viewBox="%.2f %.2f %.2f %.2f" width="1400"><rect x="-50" y="-50" width="100" height="100" fill="#111"/>'%(b[0]-1,-b[3]-1,b[2]-b[0]+2,b[3]-b[1]+2)]
for p in ps: svg.append('<polygon fill="#d4af37" points="%s"/>'%" ".join("%.3f,%.3f"%(a,-c) for a,c in p.exterior.coords))
svg.append("</svg>"); open(sys.argv[2],"w").write("\n".join(svg))
