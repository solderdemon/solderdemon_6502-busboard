"""Busboard laid out like the m68k busboard: board part.

Run once after tools/standard_sch.py, with KiCad's python, on the board as tools/direct_mount_pcb.py
left it:

    "C:/Program Files/KiCad/10.0/bin/python.exe" tools/standard_pcb.py

then tools/brand/apply_identity.py solderdemon_6502-busboard for the silkscreen. The bus stays as
routed; what follows the m68k busboard (solderdemon_m68k-busboard/tools/standard_pcb.py):

1. One rhythm across the board: every slot is a column, and the line halfway between two slot
   centres carries that gap's 100 nF capacitor (C2..C5), standing vertically with pad 1 level with
   the slots' pin 1 and pad 2 two rows below; C6 continues the rhythm half a pitch past SLOT 4.
   Pads on pin rows sit between the bus lanes (which run half a row off), so nothing moves aside.
2. Each capacitor's pad 1 takes a straight F.Cu feed along the pin-1 row from its slot's pin 2
   (C2 is on VCC_HOST); pad 2 drops straight onto the F.Cu GND lane under it (C6: the pours).
3. PWR LINK: JP1 lies across C2's line under C2, pads on pin row LINK_ROW, as on the m68k board.
   C2's pad 1 feeds its pad 1 down the left of C2; its pad 2 runs up the right of C2 into the VCC
   lane to SLOT 1's pin 2. Here the bus runs on both layers, so the F.Cu lanes these feeds
   cross (CLK, GND, R/W) step onto B.Cu over that stretch: a via either side, the B.Cu run on the free
   pin-row line above the lane. GND's run passes through C2's pad 2.
4. M3 holes: three along each long edge, 5 mm in: the corners plus H5 (top) and H6 (bottom)
   halfway between the corner holes, in the middle of the board.
5. C2..C6 take the 3D model of the shared SolderDemonCaps footprint (they were placed from a
   copy without one).
6. R2 (the ~RESET pull-up) moves R2_DX away from C7, its track ends with it.
   C7 is aligned on C6's vertical centre line; its reset track follows its pad.
Coordinates are in mm from the board's top-left corner.
"""
from pathlib import Path
import sys
import pcbnew as pcb

ROOT = Path(__file__).resolve().parent.parent
NAME = 'solderdemon_6502-busboard'
BOARD = ROOT / 'design' / f'{NAME}.kicad_pcb'
PROJECT = [ROOT / 'design' / f'{NAME}.kicad_pro', ROOT / 'design' / f'{NAME}.kicad_prl']
STOCK = Path('C:/Program Files/KiCad/10.0/share/kicad/footprints')
CAP_LIB = ROOT / 'design/SolderDemonCaps.pretty'
sys.path.insert(0, str(ROOT.parent / 'tools/capacitors'))
from replace import replace_100nf

SLOTS = ('BUS1', 'BUS2', 'BUS3', 'BUS4', 'BUS5')
CAPS = ('C2', 'C3', 'C4', 'C5', 'C6')   # right of their own slot
OLD_CAP_Y = 7.0                     # direct_mount_pcb.py: decouplers lay over the slots on this row
FEED = 0.5                          # decoupler feeds
GND_W = 0.4                         # power class
LANE = 1.27                         # the bus lanes run half a row under each pin row
LINK_ROW = 5                        # JP1's pin row; rows 1-3 are C2's, row 4 keeps it off C2
HOP = 2.6                           # the stepping lanes' vias, either side of C2's line
VIA = (0.6, 0.3)
R2_DX = -1.27                       # R2 one half-pitch further from C7, towards SLOT 4
HOLES = {'H5': 'top', 'H6': 'bottom'}
mm, MM = pcb.FromMM, pcb.ToMM


class Board:
    def __init__(self, b):
        self.b = b
        box = b.GetBoardEdgesBoundingBox()
        self.ox, self.oy = MM(box.GetX()), MM(box.GetY())
        self.w, self.h = MM(box.GetWidth()), MM(box.GetHeight())
        self.gone = []              # keep removed items referenced: KiCad 10's swig loses types otherwise

    def remove(self, item):
        self.gone.append(item)
        self.b.Remove(item)

    def pt(self, x, y):
        return pcb.VECTOR2I(mm(self.ox + x), mm(self.oy + y))

    def rel(self, p):
        return round(MM(p.x) - self.ox, 3), round(MM(p.y) - self.oy, 3)

    def pad(self, ref, number):
        fp = self.b.FindFootprintByReference(ref)
        return self.rel(next(q for q in fp.Pads() if q.GetNumber() == number).GetPosition())

    def put(self, fp, pad, xy, rot):
        fp.SetOrientationDegrees(rot)
        p = next(q for q in fp.Pads() if q.GetNumber() == pad).GetPosition()
        fp.Move(self.pt(*xy) - p)

    def track(self, net, width, *points, layer=pcb.F_Cu):
        for a, c in zip(points, points[1:]):
            t = pcb.PCB_TRACK(self.b)
            t.SetStart(self.pt(*a)); t.SetEnd(self.pt(*c))
            t.SetWidth(mm(width)); t.SetLayer(layer); t.SetNet(self.b.FindNet(net))
            self.b.Add(t)

    def via(self, net, xy):
        v = pcb.PCB_VIA(self.b)
        v.SetPosition(self.pt(*xy)); v.SetWidth(mm(VIA[0])); v.SetDrill(mm(VIA[1]))
        v.SetNet(self.b.FindNet(net))
        self.b.Add(v)

    def tracks(self, net, layer=pcb.F_Cu):
        return [t for t in self.b.GetTracks() if t.Type() == pcb.PCB_TRACE_T and t.GetLayer() == layer
                and t.GetNetname() == net]


def same(p, q):
    return abs(p[0] - q[0]) < 0.02 and abs(p[1] - q[1]) < 0.02


def lines(B):
    """x of the half-pitch line right of each slot, and y of pin rows 1..LINK_ROW."""
    centre = [(B.pad(s, '1')[0] + B.pad(s, '2')[0]) / 2 for s in SLOTS]
    pitch = centre[1] - centre[0]
    rows = [B.pad('BUS1', str(2 * n - 1))[1] for n in range(1, LINK_ROW + 1)]
    return [c + pitch / 2 for c in centre], rows


def decouplers(B, gap, rows):
    b = B.b
    # The old feeds: up from pin 2 to the row the caps lay on, then along it; and HOST's
    # VCC_HOST row into JP1 with JP1's VCC side up into the lane.
    old = []
    for net in ('VCC', 'VCC_HOST'):
        for t in B.tracks(net):
            ys = (B.rel(t.GetStart())[1], B.rel(t.GetEnd())[1])
            if min(ys) < OLD_CAP_Y + 0.1:
                old.append(t)
    jp1 = [B.pad('JP1', '1'), B.pad('JP1', '2')]
    lane = rows[0] + LANE
    for t in B.tracks('VCC_HOST') + B.tracks('VCC'):
        ends = [B.rel(t.GetStart()), B.rel(t.GetEnd())]
        if any(same(e, p) for e in ends for p in jp1):
            old.append(t)
            if t.GetNetname() == 'VCC':                         # JP1 pad 2 -> lane; the lane follows
                far = next(e for e in ends if not same(e, jp1[1]))
                old += [u for u in B.tracks('VCC') if u is not t and abs(B.rel(u.GetStart())[1] - lane) < 0.02
                        and abs(B.rel(u.GetEnd())[1] - lane) < 0.02
                        and any(same(B.rel(e), far) for e in (u.GetStart(), u.GetEnd()))]
    assert len(old) == 2 * len(CAPS) + 3, f'unexpected feeds ({len(old)}): already applied?'
    for t in old:
        B.remove(t)

    for cap, slot, x in zip(CAPS, SLOTS, gap):
        fp = b.FindFootprintByReference(cap)
        B.put(fp, '1', (x, rows[0]), -90.0)
        assert same(B.pad(cap, '2'), (x, rows[2])), (cap, B.pad(cap, '2'))
        vcc = fp.Pads()[0].GetNetname() if fp.Pads()[0].GetNumber() == '1' else fp.Pads()[1].GetNetname()
        B.track(vcc, FEED, B.pad(slot, '2'), (x, rows[0]))
        # Pad 2 onto the GND lane under it, where the bus has one (not right of SLOT 4; C2's
        # pad 2 takes the GND lane's step in link()).
        y = rows[2] + LANE
        if cap != 'C2' and any(abs(B.rel(t.GetStart())[1] - y) < 0.02 and abs(B.rel(t.GetEnd())[1] - y) < 0.02
               and min(B.rel(t.GetStart())[0], B.rel(t.GetEnd())[0]) < x < max(B.rel(t.GetStart())[0], B.rel(t.GetEnd())[0])
               for t in B.tracks('GND')):
            B.track('GND', GND_W, (x, rows[2]), (x, y))


def step(B, net, lane, line, x0, x1, via=None):
    """Take the F.Cu lane of `net` at y=lane onto B.Cu between x0 and x1: 45 degrees up to the
    pin-row line y=line (free on both layers), a via, B.Cu along the line, a via, back down.
    `via`: a through-hole pad of the net on that line, which the B.Cu run passes through."""
    t = next(t for t in B.tracks(net) if abs(B.rel(t.GetStart())[1] - lane) < 0.02
             and abs(B.rel(t.GetEnd())[1] - lane) < 0.02
             and min(B.rel(t.GetStart())[0], B.rel(t.GetEnd())[0]) < x0
             and x1 < max(B.rel(t.GetStart())[0], B.rel(t.GetEnd())[0]))
    w = MM(t.GetWidth())
    a, c = sorted([B.rel(t.GetStart())[0], B.rel(t.GetEnd())[0]])
    B.remove(t)
    d = lane - line
    B.track(net, w, (a, lane), (x0 - d, lane), (x0, line))
    B.track(net, w, (x1, line), (x1 + d, lane), (c, lane))
    for x in (x0, x1):
        B.via(net, (x, line))
    run = [(x0, line)] + ([via] if via else []) + [(x1, line)]
    B.track(net, w, *run, layer=pcb.B_Cu)


def link(B, gap, rows):
    """JP1 under C2 across its line (as on the m68k board), fed down the left, out up the right."""
    g, lane = gap[0], rows[0] + LANE
    y = rows[LINK_ROW - 1]
    B.put(B.b.FindFootprintByReference('JP1'), '1', (g - LANE, y), 90.0)
    assert same(B.pad('JP1', '2'), (g + LANE, y)), 'JP1: pad 2 must be right of pad 1'
    x2, _ = B.pad('BUS2', '2')
    B.track('VCC_HOST', FEED, (g, rows[0]), (g - LANE, lane), (g - LANE, y))
    B.track('VCC', GND_W, (g + LANE, y), (g + LANE, rows[1]), (g + LANE + rows[1] - lane, lane), (x2 - LANE, lane))
    for n in range(1, LINK_ROW - 1):                     # the lanes under rows 2..LINK_ROW-1
        lane_n = rows[n] + LANE
        net = next(str(t.GetNetname()) for t in B.b.GetTracks() if t.Type() == pcb.PCB_TRACE_T
                 and t.GetLayer() == pcb.F_Cu and abs(B.rel(t.GetStart())[1] - lane_n) < 0.02
                 and abs(B.rel(t.GetEnd())[1] - lane_n) < 0.02
                 and min(B.rel(t.GetStart())[0], B.rel(t.GetEnd())[0]) < g < max(B.rel(t.GetStart())[0], B.rel(t.GetEnd())[0]))
        step(B, net, lane_n, rows[n], g - HOP, g + HOP, via=(g, rows[2]) if n == 2 else None)   # GND: through C2's pad 2


def nudge(B, ref, dx):
    """Move a part sideways; the tracks that end on its pads move their ends along."""
    fp = B.b.FindFootprintByReference(ref)
    pads = [p.GetPosition() for p in fp.Pads()]
    d = pcb.VECTOR2I(mm(dx), 0)
    for t in B.b.GetTracks():
        if t.Type() != pcb.PCB_TRACE_T:
            continue
        for get, put in ((t.GetStart, t.SetStart), (t.GetEnd, t.SetEnd)):
            if any((get() - p).EuclideanNorm() < mm(0.02) for p in pads):
                put(get() + d)
    fp.Move(d)


def align_reset_cap(B):
    """Align C7's centre with C6 without changing its height or pad spacing."""
    c6 = B.b.FindFootprintByReference('C6')
    c7 = B.b.FindFootprintByReference('C7')
    target = c6.GetPosition().x
    pads = list(c7.Pads())
    current = (pads[0].GetPosition().x + pads[1].GetPosition().x) // 2
    dx = MM(target - current)
    if abs(dx) > 0.001:
        nudge(B, 'C7', dx)
    return dx


def holes(B):
    lib = STOCK / 'MountingHole.pretty'
    corner = {r: B.b.FindFootprintByReference(r).GetPosition() for r in ('H1', 'H2', 'H4')}
    x = (corner['H1'].x + corner['H2'].x) // 2                 # halfway between the corner holes,
    for ref, edge in HOLES.items():                            # level with them
        assert B.b.FindFootprintByReference(ref) is None, f'{ref} already placed'
        f = pcb.FootprintLoad(str(lib), 'MountingHole_3.2mm_M3_Pad')
        f.SetFPID(pcb.LIB_ID('MountingHole', 'MountingHole_3.2mm_M3_Pad'))
        f.SetReference(ref)
        f.SetValue('MountingHole_Pad')
        B.b.Add(f)
        f.SetPosition(pcb.VECTOR2I(x, corner['H1' if edge == 'top' else 'H4'].y))
        f.Reference().SetVisible(False)
        f.Value().SetVisible(False)
        for p in f.Pads():
            p.SetNet(B.b.FindNet('GND'))


def cap_models(B):
    for cap in CAPS:
        fp = B.b.FindFootprintByReference(cap)
        lib = pcb.FootprintLoad(str(CAP_LIB), str(fp.GetFPID().GetLibItemName()))
        B.gone.append(lib)
        fp.Models().clear()
        for m in lib.Models():
            fp.Models().push_back(m)


def main():
    kept = {f: f.read_bytes() for f in PROJECT if f.exists()}   # SaveBoard rewrites them
    b = pcb.LoadBoard(str(BOARD))
    if '--align-reset-cap' in sys.argv:
        dx = align_reset_cap(Board(b))
        pcb.SaveBoard(str(BOARD), b)
        b = pcb.LoadBoard(str(BOARD))
        pcb.ZONE_FILLER(b).Fill(b.Zones())
        pcb.SaveBoard(str(BOARD), b)
        for f, data in kept.items():
            f.write_bytes(data)
        print(f'C7 aligned with C6: {dx:+.3f} mm')
        return
    replaced, old_caps = replace_100nf(b)
    assert not replaced or set(replaced) == set(CAPS), replaced
    B = Board(b)
    gap, rows = lines(B)
    assert b.FindFootprintByReference('H5') is None, 'already applied'
    decouplers(B, gap, rows)
    link(B, gap, rows)
    holes(B)
    cap_models(B)
    nudge(B, 'R2', R2_DX)
    align_reset_cap(B)
    pcb.SaveBoard(str(BOARD), b)
    b = pcb.LoadBoard(str(BOARD))                    # the filler keeps the outline it loaded with: reload, then fill
    pcb.ZONE_FILLER(b).Fill(b.Zones())
    pcb.SaveBoard(str(BOARD), b)
    for f, data in kept.items():
        f.write_bytes(data)
    b.BuildConnectivity()
    print('caps on x =', ', '.join(f'{x:.2f}' for x in gap), '| unconnected:',
          b.GetConnectivity().GetUnconnectedCount(True))


if __name__ == '__main__':
    main()
