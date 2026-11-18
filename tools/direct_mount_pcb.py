"""Busboard for a directly mounted host: board part.

Run after tools/direct_mount_sch.py, with KiCad's python, on the board as committed before it:

    "C:/Program Files/KiCad/10.0/bin/python.exe" tools/direct_mount_pcb.py

The SolderDemon 6502 host carries a right-angle 2x18 socket on its J5 pads and stands upright in
HOST, component side toward the left edge; expansion cards carry the same socket in the same place
and stand in SLOT 1-4 facing the same way. A standing board's plane lies 1.3 mm to the right of its
slot's even pin row (the socket's lower contact row sits 1.27 mm over the board), and its lower edge
hangs ~9 mm over the busboard, so only the socket body (over the header, y 13-59) and low parts
under the edge matter. What changes:
1. The slot decouplers C2-C6 leave the board plane: each moves 9.5 mm right of its slot's pin 1,
   between the slot's board and the next socket, as on the m68k busboard. Their VCC pad runs
   straight back along y = 7 to the existing stub over the slot's VCC pin.
2. GND is poured on B.Cu as well: half the bus runs on that side.
3. C7 becomes 1 nF (see direct_mount_sch.py).
4. A pin 1 mark on the silkscreen, because a plain 2x18 header takes the socket either way round:
   a filled triangle pointing at pin 1 of every slot from the left.
Each step checks for itself whether it has been applied, so the script can be re-run.
Coordinates are in mm from the board's top-left corner.
"""
from pathlib import Path

import pcbnew as pcb

ROOT = Path(__file__).resolve().parent.parent
NAME = 'solderdemon_6502-busboard'
BOARD = ROOT / 'design' / f'{NAME}.kicad_pcb'
PROJECT = [ROOT / 'design' / f'{NAME}.kicad_pro', ROOT / 'design' / f'{NAME}.kicad_prl']

CAPS = {'C2': 'BUS1', 'C3': 'BUS2', 'C4': 'BUS3', 'C5': 'BUS4', 'C6': 'BUS5'}
CAP_DX, CAP_Y = 9.5, 7.0            # VCC pad: this far right of the slot's pin 1, on the stub's row
C7_VALUE = '1nF'
SLOTS = ('BUS1', 'BUS2', 'BUS3', 'BUS4', 'BUS5')
PIN1_MARK_DX = 1.7                  # apex of the pin 1 triangle, left of the pad and of the header's silk outline
LEGEND_X, LEGEND_DX = 48.51, 1.6    # left column of the pinout legend, and how far it moves left
FACE_Y = 63.0                       # row of the "COMPONENTS" arrows of an earlier draft, removed again
NOTE = 'PIN 1 UP - COMPONENT SIDE AS ARROWED'


class Board:
    def __init__(self, b):
        self.b = b
        box = b.GetBoardEdgesBoundingBox()
        self.ox, self.oy = box.GetX(), box.GetY()
        self.gone = []              # keep removed items referenced: KiCad 10's swig loses types otherwise

    def remove(self, item):
        self.gone.append(item)
        self.b.Remove(item)

    def pt(self, x, y):
        return pcb.VECTOR2I(self.ox + pcb.FromMM(x), self.oy + pcb.FromMM(y))

    def mm(self, p):
        return round(pcb.ToMM(p.x - self.ox), 2), round(pcb.ToMM(p.y - self.oy), 2)

    def pad(self, ref, number):
        fp = self.b.FindFootprintByReference(ref)
        return self.mm(next(q for q in fp.Pads() if q.GetNumber() == number).GetPosition())

    def put(self, fp, pad, xy, rot=0):
        fp.SetOrientationDegrees(rot)
        p = next(q for q in fp.Pads() if q.GetNumber() == pad).GetPosition()
        fp.Move(self.pt(*xy) - p)

    def text(self, s, x, y, size=0.8):
        t = pcb.PCB_TEXT(self.b)
        t.SetText(s); t.SetLayer(pcb.F_SilkS)
        t.SetTextSize(pcb.VECTOR2I(pcb.FromMM(size), pcb.FromMM(size)))
        t.SetTextThickness(pcb.FromMM(size * 0.15))
        t.SetPosition(self.pt(x, y))
        self.b.Add(t)
        return t

    def silk_line(self, a, c, width=0.15):
        s = pcb.PCB_SHAPE(self.b, pcb.SHAPE_T_SEGMENT)
        s.SetStart(self.pt(*a)); s.SetEnd(self.pt(*c))
        s.SetWidth(pcb.FromMM(width)); s.SetLayer(pcb.F_SilkS)
        self.b.Add(s)

    def silk_triangle(self, *xy):
        s = pcb.PCB_SHAPE(self.b, pcb.SHAPE_T_POLY)
        pts = pcb.VECTOR_VECTOR2I([self.pt(*p) for p in xy])
        s.SetPolyPoints(pts)
        s.SetFilled(True); s.SetWidth(0); s.SetLayer(pcb.F_SilkS)
        self.b.Add(s)

    def track(self, net, layer, width, *points):
        for a, c in zip(points, points[1:]):
            t = pcb.PCB_TRACK(self.b)
            t.SetStart(self.pt(*a)); t.SetEnd(self.pt(*c))
            t.SetWidth(pcb.FromMM(width)); t.SetLayer(layer); t.SetNet(self.b.FindNet(net))
            self.b.Add(t)


def near(p, q):
    return (p - q).EuclideanNorm() < pcb.FromMM(0.02)   # pad centres on a 0.005 mm grid


def move_decouplers(B):
    b = B.b
    for cap, bus in CAPS.items():
        fp = b.FindFootprintByReference(cap)
        x1, _ = B.pad(bus, '1')
        x2, y2 = B.pad(bus, '2')
        vcc = next(p for p in fp.Pads() if p.GetNumber() == '1')
        stub = [t for t in b.GetTracks() if t.Type() == pcb.PCB_TRACE_T and t.GetLayer() == pcb.F_Cu
                and near(t.GetStart(), vcc.GetPosition()) and near(t.GetEnd(), B.pt(x2, y2))]
        assert len(stub) == 1, (cap, stub)                 # the straight VCC stub of power_r2_pcb.py
        assert near(vcc.GetPosition(), B.pt(x2, CAP_Y)), cap   # ...so the cap still stands over the pin
        B.put(fp, '1', (x1 + CAP_DX, CAP_Y), 0)             # VCC pad left, GND pad right
        B.track(vcc.GetNetname(), pcb.F_Cu, pcb.ToMM(stub[0].GetWidth()), (x2, CAP_Y), (x1 + CAP_DX, CAP_Y))


def pour_bottom(B):
    b = B.b
    front = [z for z in b.Zones() if z.GetNetname() == 'GND' and z.GetLayer() == pcb.F_Cu]
    assert len(front) == 1 and not any(z.GetLayer() == pcb.B_Cu for z in b.Zones()), 'already applied'
    back = front[0].Duplicate()
    back.SetLayer(pcb.B_Cu)
    b.Add(back)


def mark_slots(B):
    """A filled triangle pointing at pin 1 of every slot from the left. Earlier marks (triangles
    wherever they stood, the "COMPONENTS" arrows and their note) go first, so this can be re-run."""
    b = B.b
    pin1 = {bus: B.pad(bus, '1') for bus in SLOTS}
    stale = []
    for d in b.GetDrawings():
        if d.GetLayer() != pcb.F_SilkS:
            continue
        if isinstance(d, pcb.PCB_TEXT) and d.GetText() in ('COMPONENTS', NOTE):
            stale.append(d)
        elif isinstance(d, pcb.PCB_SHAPE) and d.GetShape() == pcb.SHAPE_T_POLY and                 any((d.GetCenter() - B.pt(*p)).EuclideanNorm() < pcb.FromMM(4) for p in pin1.values()):
            stale.append(d)
        elif isinstance(d, pcb.PCB_SHAPE) and d.GetShape() == pcb.SHAPE_T_SEGMENT and                 FACE_Y < B.mm(d.GetStart())[1] < FACE_Y + 3 and B.mm(d.GetStart())[0] < 100:
            stale.append(d)
    for d in stale:
        B.remove(d)
    for bus in SLOTS:
        x1, y1 = pin1[bus]
        apex = x1 - PIN1_MARK_DX
        B.silk_triangle((apex, y1), (apex - 1.2, y1 - 0.7), (apex - 1.2, y1 + 0.7))
    for d in b.GetDrawings():                                # the pinout legend's left column (A0..
        x, y = B.mm(d.GetPosition())                         # /ML, right-aligned at x 48.51) ends
        if isinstance(d, pcb.PCB_TEXT) and x == LEGEND_X and 14 < y < 58:   # under SLOT 2's triangle
            d.Move(pcb.VECTOR2I(-pcb.FromMM(LEGEND_DX), 0))


def applied(b, what):
    print(what, 'already applied, skipped')


def main():
    kept = {f: f.read_bytes() for f in PROJECT if f.exists()}   # SaveBoard rewrites them
    b = pcb.LoadBoard(str(BOARD))
    B = Board(b)
    if any(z.GetLayer() == pcb.B_Cu for z in b.Zones()):
        applied(b, 'decouplers, B.Cu pour and C7')
    else:
        pour_bottom(B)
        move_decouplers(B)
        b.FindFootprintByReference('C7').SetValue(C7_VALUE)
    mark_slots(B)                                        # re-draws the pin 1 triangles each time
    pcb.SaveBoard(str(BOARD), b)
    b = pcb.LoadBoard(str(BOARD))                    # the filler keeps the outline it loaded with: reload, then fill
    pcb.ZONE_FILLER(b).Fill(b.Zones())
    pcb.SaveBoard(str(BOARD), b)
    for f, data in kept.items():
        f.write_bytes(data)
    b.BuildConnectivity()
    print('unconnected:', b.GetConnectivity().GetUnconnectedCount(True))


if __name__ == '__main__':
    main()
