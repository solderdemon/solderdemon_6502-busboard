"""Busboard laid out like the m68k busboard: schematic part.

Like the m68k busboard, the board is held down between the slots too: besides the four corners,
one M3 hole in the middle of the top and of the bottom edge, H5 and H6, copies of H4
(MountingHole_Pad on GND) one row lower on the sheet. Run once, then tools/standard_pcb.py with KiCad's python.
"""
from pathlib import Path
import re
import uuid

ROOT = Path(__file__).resolve().parent.parent
SCH = ROOT / 'design' / 'solderdemon_6502-busboard.kicad_sch'
NS = uuid.UUID('6502b05b-0000-4000-8000-000000000003')
TEMPLATE_X = '381'                  # H4's column; its symbol, pin wire and GND label are copied
NEW = [('H5', 304.8), ('H6', 330.2)]
DY = 30.48                          # one row under H1..H4


def block(t, start):
    """The balanced (...) starting at t[start]."""
    depth = 0
    for i in range(start, len(t)):
        depth += {'(': 1, ')': -1}.get(t[i], 0)
        if depth == 0:
            return t[start:i + 1]
    raise ValueError('unbalanced')


def top_level(t, head):
    """Every top-level block of the sheet that starts with `head`."""
    return [block(t, m.start() + 2) for m in re.finditer(r'\n\t\(' + re.escape(head) + r'\b', t)]


def num(v):
    return f'{v:.2f}'.rstrip('0').rstrip('.')


def update_caps(t):
    """Use the common 5.08 mm footprint for the five 100 nF slot capacitors."""
    old = 'Capacitor_THT:C_Disc_D5.0mm_W2.5mm_P2.50mm'
    new = 'SolderDemonCaps:C_Radial_5.08mm'
    for ref in ('C2', 'C3', 'C4', 'C5', 'C6'):
        sym = next(s for s in top_level(t, 'symbol') if f'"Reference" "{ref}"' in s)
        assert '"Value" "100nF"' in sym, ref
        assert old in sym or new in sym, ref
        t = t.replace(sym, sym.replace(old, new), 1)
    return t


def moved(b, x, ref, key):
    """Copy of an H4-column block at column x, DY lower, with fresh uuids (stable: uuid5)."""
    b = re.sub(r'\((at|xy) ' + TEMPLATE_X + r' ([0-9.]+)',
               lambda m: f'({m.group(1)} {num(x)} {num(float(m.group(2)) + DY)}', b)
    n = iter(range(100))
    b = re.sub(r'\(uuid "[^"]+"\)', lambda m: f'(uuid "{uuid.uuid5(NS, f"{ref}/{key}/{next(n)}")}")', b)
    return b.replace('"H4"', f'"{ref}"')


def main():
    t = SCH.read_bytes().decode('utf-8').replace('\r\n', '\n')      # KiCad wrote it with CRLF
    t = update_caps(t)
    assert '"Reference" "H5"' not in t, 'already applied'
    sym = next(s for s in top_level(t, 'symbol') if '"Reference" "H4"' in s)
    wire = next(w for w in top_level(t, 'wire') if f'(xy {TEMPLATE_X} 58.42) (xy {TEMPLATE_X} 63.5)' in w)
    label = next(g for g in top_level(t, 'global_label') if f'(at {TEMPLATE_X} 63.5 270)' in g)
    add = ''.join(f'\n\t{moved(b, x, ref, key)}' for ref, x in NEW
                  for key, b in (('symbol', sym), ('wire', wire), ('label', label)))
    i = t.index(f'\n\t{sym}') + len(sym) + 2                         # right after H4's symbol
    t = t[:i] + add + t[i:]
    SCH.write_bytes(t.replace('\n', '\r\n').encode('utf-8'))
    print('added', ', '.join(r for r, _ in NEW), 'to', SCH.name)


if __name__ == '__main__':
    main()
