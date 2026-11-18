"""Busboard power input without diodes, a tidy power corner, and slot references in slot order.

Run after tools/power_r2_sch.py, with KiCad's python, on the board as committed before it:

    "C:/Program Files/KiCad/10.0/bin/python.exe" tools/power_r2_pcb.py

1. The four expansion slots are electrically identical, so their footprints are re-linked to the
   schematic symbols in slot order: SLOT n is BUSn+1 with its decoupler Cn+2 (HOST stays BUS1, C2).
   Before, SLOT 1 was BUS3/C4 and SLOT 4 BUS2/C3.
2. D1-D3 (1N5819 OR-ing) and the C&K OS102011MS2Q slide switch (100 mA) go. The power corner uses
   the full height of the board, top to bottom:
       C1 (470 uF) over LED1, its + pad straight above LED1's anode; LED1 over R1, R1 stacked
       with the USB-C CC resistors R4 and R3
       inputs on the right edge: USB-C J3, DC jack J1, and the terminal J2 moved under the jack
       JP2  2x3 source header under the jack, rows USB / DC / TERM in the order of the inputs; each
            input runs straight into its row; one jumper cap
       SW1  the m68k busboard's NKK M2021SS1W01 DPST toggle at the bottom, lever clear of SLOT 4;
            on its VCC row to the left the 1.5KE6.8A TVS D1 (upright, cathode on the row)
   VCC leaves SW1 on B.Cu along that row and climbs the VCC trunk to SLOT 4, LED1 and C1. The SolderDemon title moves beside the
   logo, out of the corner.
   Each slot decoupler is turned round so its VCC pad stands over the slot's VCC pin.
3. The /RESET pull-up R2 stands beside its capacitor C7, both on the /RESET line from SLOT 4.
4. Last, the board grows 5 mm to the left (137 x 100 mm), so HOST's decoupler C2 stands over
   BUS1 like every slot's, clear of the corner hole H1.
Coordinates are in mm from the board's top-left corner before it grows (BACKPLANE.md: +5 in x).
"""
from pathlib import Path
import uuid

import pcbnew as pcb

ROOT = Path(__file__).resolve().parent.parent
NAME = 'solderdemon_6502-busboard'
BOARD = ROOT / 'design' / f'{NAME}.kicad_pcb'
PROJECT = [ROOT / 'design' / f'{NAME}.kicad_pro', ROOT / 'design' / f'{NAME}.kicad_prl']
STOCK = Path('C:/Program Files/KiCad/10.0/share/kicad/footprints')
NS = uuid.UUID('6502b05b-0000-4000-8000-000000000002')     # as in power_r2_sch.py

SLOT_X = {26.0: 'BUS2', 46.0: 'BUS3', 66.0: 'BUS4', 86.0: 'BUS5'}  # pin 1 x -> reference
CAP_X = {17.0: 'C2', 26.0: 'C3', 46.0: 'C4', 66.0: 'C5', 86.0: 'C6'}

TRUNK_X = 100.58                    # the B.Cu VCC trunk from C1 down the corner
SRC_X, COM_X = 115.0, 112.46        # JP2: source column (odd pins), common VIN_DC column (even pins)
ROW = {'USB': 67.0, 'DC': 69.54, 'TERM': 72.08}
J2_PAD1 = (126.08, ROW['TERM'])     # the terminal's +5V pin, level with its row
SW1_AT = (116.0, 85.0)              # rotated 180: VIN_DC pads on top, VCC pads below
TVS_X, TVS_K_Y = 104.0, 89.12       # upright, cathode on the VCC row
LED_K = (113.08, 16.9)              # LED1, its cathode straight over R1's right pad
R1_Y = 27.9                         # stacked over R4 (32.9) and R3 (37.9), same columns
C1_Y = 9.5                          # C1 over LED1, + pad above the anode
TITLE_LEFT, TITLE_Y = 61.0, (81.5, 87.0)   # SolderDemon title beside the logo
RESET_Y, R2_X = 25.9, 94.92         # C7 stays at x 98.08; R2 beside it
WIDEN = 5.0                         # the board grows this much to the left, last of all

STALE_TRACKS = {                    # (net, start, end) of tracks the new corner replaces
    ('VBUS', (121.58, 38.9), (118.58, 41.9)), ('VBUS', (118.58, 41.9), (115.03, 41.9)),
    ('VBUS', (115.03, 41.9), (115.03, 54.9)), ('VBUS', (115.03, 54.9), (113.08, 54.9)),
    ('VIN_TERM', (117.08, 40.9), (113.08, 44.9)),
    ('VCC', (100.58, 59.4), (100.58, 71.88)), ('VCC', (100.58, 71.88), (114.59, 71.88)),
    ('VCC', (114.59, 71.88), (119.39, 71.88)), ('VCC', (100.58, 33.9), (98.08, 33.9)),
    ('VCC', (100.58, 16.9), (106.31, 16.9)),
    ('VCC', (100.58, 6.9), (106.33, 6.9)), ('VCC', (100.58, 59.4), (100.58, 6.9)),   # trunk from C1's old place
    ('VCC', (106.08, 63.9), (106.08, 60.9)), ('VCC', (106.08, 60.9), (104.58, 59.4)),
    ('VCC', (104.58, 59.4), (100.58, 59.4)),
    ('~{RESET}', (88.61, 24.66), (89.89, 25.93)), ('~{RESET}', (89.89, 25.93), (98.08, 25.9)),   # SLOT 4 to C7 and R2
    ('~{RESET}', (98.08, 44.06), (95.58, 41.56)), ('~{RESET}', (95.58, 41.56), (95.58, 28.4)),
    ('~{RESET}', (95.58, 28.4), (98.08, 25.9)),
}
STALE_NETS = {'VIN_DC', 'VIN_FUSED', 'VIN_JACK', 'VIN_TERM', 'Net-(LED1-K)'}   # every track of these
STALE_TEXT = {'ON', 'OFF', 'POWER', 'SOURCE: ONE JUMPER', 'USB', 'DC', 'TERM'}


class Board:
    def __init__(self, b):
        self.b = b
        box = b.GetBoardEdgesBoundingBox()
        self.ox, self.oy = box.GetX(), box.GetY()
        self.gone = []              # keep removed items referenced: KiCad 10's swig loses types otherwise

    def pt(self, x, y):
        return pcb.VECTOR2I(self.ox + pcb.FromMM(x), self.oy + pcb.FromMM(y))

    def mm(self, p):
        return round(pcb.ToMM(p.x - self.ox), 2), round(pcb.ToMM(p.y - self.oy), 2)

    def remove(self, item):
        self.gone.append(item)
        self.b.Remove(item)

    def net(self, name):
        n = self.b.FindNet(name)
        if n is None:
            n = pcb.NETINFO_ITEM(self.b, name)
            self.b.Add(n)
        return n

    def track(self, net, layer, width, *points):
        for a, c in zip(points, points[1:]):
            t = pcb.PCB_TRACK(self.b)
            t.SetStart(self.pt(*a)); t.SetEnd(self.pt(*c))
            t.SetWidth(pcb.FromMM(width)); t.SetLayer(layer); t.SetNet(self.net(net))
            self.b.Add(t)

    def text(self, s, x, y, size=0.9):
        t = pcb.PCB_TEXT(self.b)
        t.SetText(s); t.SetLayer(pcb.F_SilkS)
        t.SetTextSize(pcb.VECTOR2I(pcb.FromMM(size), pcb.FromMM(size)))
        t.SetTextThickness(pcb.FromMM(size * 0.15))
        t.SetPosition(self.pt(x, y))
        self.b.Add(t)

    def footprint(self, lib, name, ref, value, nets, sheet, datasheet=''):
        fp = pcb.FootprintLoad(str(lib), name)
        fp.SetFPID(pcb.LIB_ID(lib.stem, name))         # nickname = library folder name, as in fp-lib-table
        fp.SetField('Datasheet', datasheet)
        fp.SetReference(ref); fp.SetValue(value)
        fp.SetPath(pcb.KIID_PATH(f'/{uuid.uuid5(NS, "symbol/" + ref)}'))
        fp.SetSheetfile(sheet[0]); fp.SetSheetname(sheet[1])
        fp.Reference().SetVisible(False)              # the busboard names parts by function, not reference
        self.b.Add(fp)
        for p in fp.Pads():
            if p.GetNumber() in nets:
                p.SetNet(self.net(nets[p.GetNumber()]))
        return fp

    def put(self, fp, pad, xy, rot=0):
        """Rotate, then move fp so that its pad `pad` lands on xy."""
        fp.SetOrientationDegrees(rot)
        p = next(q for q in fp.Pads() if q.GetNumber() == pad).GetPosition()
        fp.Move(self.pt(*xy) - p)

    def pad(self, ref, number):
        fp = self.b.FindFootprintByReference(ref)
        return self.mm(next(q for q in fp.Pads() if q.GetNumber() == number).GetPosition())


def relink_slots(B):
    by_ref = {f.GetReference(): f for f in B.b.GetFootprints()}
    paths = {r: by_ref[r].GetPath() for r in list(SLOT_X.values()) + list(CAP_X.values())}
    for table in (SLOT_X, CAP_X):
        moves = []
        for f in B.b.GetFootprints():
            if f.GetReference() not in table.values():
                continue
            x = B.mm(f.GetPosition())[0] if table is CAP_X else B.mm(next(q for q in f.Pads() if q.GetNumber() == '1').GetPosition())[0]
            moves.append((f, table[min(table, key=lambda k: abs(k - x))]))
        for f, new in moves:
            f.SetReference(new)
            f.SetPath(paths[new])


def straight_decouplers(B):
    """Turn each slot decoupler round so its VCC pad stands right over the slot's VCC pin (pin 2):
    one straight track instead of a dog-leg. HOST's C2 too: widen_left moves the corner hole H1
    out of its way."""
    b = B.b
    for t in list(b.GetTracks()):
        if t.Type() != pcb.PCB_TRACE_T or t.GetLayer() != pcb.F_Cu or t.GetNetname() not in ('VCC', 'VCC_HOST'):
            continue
        (x1, y1), (x2, y2) = B.mm(t.GetStart()), B.mm(t.GetEnd())
        if max(x1, x2) < 92 and min(y1, y2) >= 6.9 and max(y1, y2) <= 14.51 and not (y1 == y2 == 14.5):
            B.remove(t)
    targets = [('C2', 'BUS1', '2', 'VCC_HOST')] + [(c, bus, '2', 'VCC') for c, bus in
                                                   (('C3', 'BUS2'), ('C4', 'BUS3'), ('C5', 'BUS4'), ('C6', 'BUS5'))]
    for cap, part, pin, net in targets:
        x, y = B.pad(part, pin)
        fp = b.FindFootprintByReference(cap)
        cy = B.pad(cap, '1')[1]
        B.put(fp, '1', (x, cy), 180)
        B.track(net, pcb.F_Cu, 0.5, (x, cy), (x, y))


def widen_left(B, dx):
    """Grow the board dx mm to the left: the left edge, the GND fill and the two left mounting holes
    move out, everything else stays. Runs last, because every coordinate above is measured from the
    old top-left corner."""
    b = B.b
    shift = pcb.VECTOR2I(-pcb.FromMM(dx), 0)
    for s in b.GetDrawings():
        if not isinstance(s, pcb.PCB_SHAPE) or s.GetLayer() != pcb.Edge_Cuts:
            continue
        if s.GetShape() == pcb.SHAPE_T_ARC:
            if max(B.mm(s.GetStart())[0], B.mm(s.GetEnd())[0]) < 10:
                s.Move(shift)
        else:
            for get, put in ((s.GetStart, s.SetStart), (s.GetEnd, s.SetEnd)):
                if B.mm(get())[0] < 10:
                    put(get() + shift)                 # exact: the ends must still meet the arcs
    for zone in b.Zones():
        outline = zone.Outline()
        for i in range(outline.VertexCount()):
            if B.mm(outline.CVertex(i))[0] < 10:
                outline.SetVertex(i, outline.CVertex(i) + shift)
    for ref in ('H1', 'H4'):
        b.FindFootprintByReference(ref).Move(shift)


def clear(B):
    b = B.b
    for ref in ('D1', 'D2', 'D3', 'SW1'):
        B.remove(b.FindFootprintByReference(ref))
    for t in list(b.GetTracks()):
        key = (t.GetNetname(), B.mm(t.GetStart()), B.mm(t.GetEnd()))
        if t.GetNetname() in STALE_NETS or key in STALE_TRACKS:
            B.remove(t)
    for d in list(b.GetDrawings()):
        if isinstance(d, pcb.PCB_TEXT) and d.GetText() in STALE_TEXT:
            B.remove(d)


def place_chain(B, sheet):
    b = B.b
    header = STOCK / 'Connector_PinHeader_2.54mm.pretty'
    jp2 = B.footprint(header, 'PinHeader_2x03_P2.54mm_Vertical', 'JP2', 'SOURCE',
                      {'1': 'VIN_TERM', '3': 'VIN_JACK', '5': 'VBUS', '2': 'VIN_DC', '4': 'VIN_DC', '6': 'VIN_DC'}, sheet)
    B.put(jp2, '1', (SRC_X, ROW['TERM']), 180)
    assert B.pad('JP2', '5') == (SRC_X, ROW['USB']) and B.pad('JP2', '6') == (COM_X, ROW['USB'])
    B.put(b.FindFootprintByReference('J2'), '1', J2_PAD1, 180)

    sw = B.footprint(ROOT / 'design' / 'SolderDemon.pretty', 'NKK-M2021SS1W01', 'SW1', 'POWER',
                     {'1': 'VIN_DC', '3': 'VIN_DC', '2': 'VCC', '4': 'VCC'}, sheet)
    sw.SetOrientationDegrees(180)
    sw.SetPosition(B.pt(*SW1_AT))
    tvs = B.footprint(STOCK / 'Diode_THT.pretty', 'D_DO-201AE_P15.24mm_Horizontal', 'D1', '1.5KE6.8A',
                      {'1': 'VCC', '2': 'GND'}, sheet, 'https://www.vishay.com/docs/88301/15ke.pdf')
    B.put(tvs, '1', (TVS_X, TVS_K_Y), 90)

    vin_l, vin_r = sorted((B.pad('SW1', '1'), B.pad('SW1', '3')))
    vcc_l, vcc_r = sorted((B.pad('SW1', '2'), B.pad('SW1', '4')))
    assert vin_l[1] == vin_r[1] and vcc_l[1] == vcc_r[1] == TVS_K_Y, (vin_l, vcc_l)
    F, Bk = pcb.F_Cu, pcb.B_Cu
    jog = vin_l[0] - COM_X
    B.track('VIN_DC', F, 0.8, (COM_X, ROW['USB']), (COM_X, vin_l[1] - jog), vin_l, vin_r)
    B.track('VCC', Bk, 0.8, (TRUNK_X, 16.9), (TRUNK_X, TVS_K_Y), vcc_l, vcc_r)
    # each input straight into its row of JP2
    B.track('VBUS', Bk, 0.6, (121.58, 38.9), (114.0, 46.48), (114.0, ROW['USB'] - 1.0), (SRC_X, ROW['USB']))
    jack = B.pad('J1', '1')
    B.track('VIN_JACK', F, 0.8, jack, (jack[0], ROW['DC'] - (jack[0] - SRC_X)), (SRC_X, ROW['DC']))
    B.track('VIN_TERM', F, 0.8, J2_PAD1, (SRC_X, ROW['TERM']))

    B.text('SOURCE', SRC_X - 1.27, ROW['USB'] - 2.6, 0.9)
    for name, y in ROW.items():
        B.text(name, COM_X - 3.2, y, 0.9)
    B.text('POWER', SW1_AT[0], SW1_AT[1] + 8.6, 1.0)
    for d in b.GetDrawings():                                # J2's labels follow it, right of the pins
        if isinstance(d, pcb.PCB_TEXT) and B.mm(d.GetPosition()) in ((121.58, 26.86), (121.58, 29.4)):
            d.SetPosition(B.pt(J2_PAD1[0] + 3.6, J2_PAD1[1] - (2.54 if d.GetText() == 'GND' else 0)))
        elif isinstance(d, pcb.PCB_TEXT) and d.GetText() in ('SOLDER DEMON', '6502 BUS BOARD  r1'):
            y = TITLE_Y[0] if d.GetText() == 'SOLDER DEMON' else TITLE_Y[1]
            d.SetPosition(B.pt(0, y))
            d.Move(B.pt(TITLE_LEFT, y) - pcb.VECTOR2I(d.GetBoundingBox().GetLeft(), B.pt(TITLE_LEFT, y).y))


def tidy_corner(B):
    b = B.b
    B.put(b.FindFootprintByReference('LED1'), '1', LED_K, 180)          # K right, A left
    B.put(b.FindFootprintByReference('R1'), '2', (LED_K[0], R1_Y), 0)    # GND left, LED-K right, over R4
    assert B.pad('R1', '1') == (102.92, R1_Y), B.pad('R1', '1')
    B.track('VCC', pcb.B_Cu, 0.5, (TRUNK_X, 16.9), B.pad('LED1', '2'))
    B.track('Net-(LED1-K)', pcb.F_Cu, 0.5, LED_K, (LED_K[0], R1_Y))
    anode = B.pad('LED1', '2')
    B.put(b.FindFootprintByReference('C1'), '1', (anode[0], C1_Y), 0)
    B.track('VCC', pcb.B_Cu, 0.8, anode, (anode[0], C1_Y))

    r2 = b.FindFootprintByReference('R2')                    # /RESET up, VCC down
    B.put(r2, '2', (R2_X, RESET_Y), 90)
    bus = B.pad('BUS5', '10')                                # RST of SLOT 4
    c7 = B.pad('C7', '1')
    assert c7[1] == RESET_Y
    B.track('~{RESET}', pcb.F_Cu, 0.4, bus, (bus[0] + (RESET_Y - bus[1]), RESET_Y), c7)
    B.track('VCC', pcb.B_Cu, 0.5, B.pad('R2', '1'), (TRUNK_X, B.pad('R2', '1')[1]))


def main():
    kept = {f: f.read_bytes() for f in PROJECT if f.exists()}   # SaveBoard rewrites them
    b = pcb.LoadBoard(str(BOARD))
    assert b.FindFootprintByReference('D2') is not None, 'already applied'      # the OR-ing diodes are still there
    B = Board(b)
    relink_slots(B)
    straight_decouplers(B)
    sheet = (b.FindFootprintByReference('SW1').GetSheetfile(), b.FindFootprintByReference('SW1').GetSheetname())
    clear(B)
    place_chain(B, sheet)
    tidy_corner(B)
    widen_left(B, WIDEN)
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
