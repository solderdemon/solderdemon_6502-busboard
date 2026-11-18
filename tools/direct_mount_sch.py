"""Busboard for a directly mounted host: schematic part.

The host and every expansion card stand upright in their slot on a right-angle 2x18 socket, so
the bus /RESET line is driven by the host's open-drain CPLD pin (R7 3k3 on the host). The 100 nF
C7 of the first draft made every reset dump its charge into that pin and stretched the release to
~250 us through plain CMOS inputs; 1 nF with R2 || R7 = 2.5 kOhm gives a 2.5 us edge and still
swallows bus noise. Run once, then tools/direct_mount_pcb.py with KiCad's python.
"""
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parent.parent
SCH = ROOT / 'design' / 'solderdemon_6502-busboard.kicad_sch'
C7_VALUE = ('100nF', '1nF')


def main():
    t = SCH.read_bytes().decode('utf-8').replace('\r\n', '\n')      # KiCad wrote it with CRLF
    m = re.search(r'\(property "Reference" "C7"\n.*?\(property "Value" "([^"]+)"', t, re.S)
    assert m and m.group(1) == C7_VALUE[0], 'already applied' if m else 'C7 not found'
    t = t[:m.start(1)] + C7_VALUE[1] + t[m.end(1):]
    SCH.write_bytes(t.replace('\n', '\r\n').encode('utf-8'))
    print('C7', C7_VALUE[0], '->', C7_VALUE[1], 'in', SCH.name)


if __name__ == '__main__':
    main()
