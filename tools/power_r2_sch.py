"""Busboard power input without diodes: schematic part.

Replaces the 1N5819 OR-ing diodes D1-D3 and the 100 mA slide switch:
  - JP2, a 2x3 source header: one jumper cap across a row joins that source (odd pins: 1 terminal,
    3 DC jack, 5 USB-C) to VIN_DC (even pins);
  - SW1, the NKK M2021SS1W01 DPST toggle used on the m68k busboard, both poles in parallel, feeds VCC;
  - D1, a 1.5KE6.8A unidirectional TVS from VCC to GND (clamps a wrong adapter and reverse polarity
    while the adapter's own current limit holds).
The new symbols stand in a free area of the sheet; each pin gets its global label at the pin end,
like the rest of this schematic. Run once, then tools/power_r2_pcb.py with KiCad's python.
"""
from pathlib import Path
import re
import uuid

ROOT = Path(__file__).resolve().parent.parent
SCH = ROOT / 'design' / 'solderdemon_6502-busboard.kicad_sch'
STOCK = Path('C:/Program Files/KiCad/10.0/share/kicad/symbols')
PROJECT = 'solderdemon_6502-busboard'

GONE_REFS = {'D1', 'D2', 'D3', 'SW1'}
GONE_LABELS = {('VIN_DC', 92.71, 96.52), ('VIN_DC', 105.41, 96.52), ('VIN_DC', 118.11, 96.52),
               ('VBUS', 92.71, 104.14), ('VIN_JACK', 105.41, 104.14), ('VIN_TERM', 118.11, 104.14),
               ('VCC', 76.2, 50.8), ('VIN_DC', 86.36, 53.34)}
GONE_NC = {(86.36, 48.26)}                                   # the slide switch's unused throw
GONE_LIBS = {'Device:D_Schottky', 'Switch:SW_SPDT'}
NEW_LIBS = [('Connector_Generic', 'Conn_02x03_Odd_Even'), ('Switch', 'SW_DPST'), ('Diode', '1.5KExxA')]

# ref, lib_id, value, footprint, datasheet, (x, y, rot), {pin: net}
PARTS = [
    ('JP2', 'Connector_Generic:Conn_02x03_Odd_Even', 'SOURCE', 'Connector_PinHeader_2.54mm:PinHeader_2x03_P2.54mm_Vertical', '',
     (139.7, 95.25, 0), {'1': 'VIN_TERM', '3': 'VIN_JACK', '5': 'VBUS', '2': 'VIN_DC', '4': 'VIN_DC', '6': 'VIN_DC'}),
    ('SW1', 'Switch:SW_DPST', 'POWER', 'SolderDemon:NKK-M2021SS1W01', '',
     (185.42, 90.17, 0), {'1': 'VIN_DC', '2': 'VCC', '3': 'VIN_DC', '4': 'VCC'}),
    ('D1', 'Diode:1.5KExxA', '1.5KE6.8A', 'Diode_THT:D_DO-201AE_P15.24mm_Horizontal',
     'https://www.vishay.com/docs/88301/15ke.pdf', (205.74, 96.52, 270), {'1': 'VCC', '2': 'GND'}),
]
NS = uuid.UUID('6502b05b-0000-4000-8000-000000000002')


def uid(*key):
    return str(uuid.uuid5(NS, '/'.join(map(str, key))))


def stock_symbol(lib, name):
    text = (STOCK / f'{lib}.kicad_sym').read_text(encoding='utf-8')
    start = text.index(f'\n\t(symbol "{name}"')
    nxt = text.find('\n\t(symbol "', start + 1)
    block = text[start + 1:nxt if nxt > 0 else text.rindex('\n)')]
    block = block.replace(f'(symbol "{name}"', f'(symbol "{lib}:{name}"', 1)
    return '\n'.join('\t' + line for line in block.split('\n'))


def pins(lib_text):
    return {n: (float(x), float(y)) for x, y, n in
            re.findall(r'\(pin \w+ \w+\s*\(at ([\-\d\.]+) ([\-\d\.]+) \d+\).*?\(number "(\w+)"', lib_text, re.S)}


def place(at, p):
    """Pin end of a library pin p for a symbol at (x, y, rot): y flips, rot turns counter-clockwise."""
    x, y, rot = at
    px, py = p[0], -p[1]
    c, s = {0: (1, 0), 90: (0, 1), 180: (-1, 0), 270: (0, -1)}[rot]
    return round(x + px * c + py * s, 2), round(y - px * s + py * c, 2)


def label(net, x, y, angle):
    justify = 'left' if angle in (0, 90) else 'right'
    return f'''	(global_label "{net}"
		(shape passive)
		(at {x:g} {y:g} {angle})
		(effects
			(font
				(size 1.27 1.27)
			)
			(justify {justify})
		)
		(uuid "{uid('label', net, x, y)}")
		(property "Intersheetrefs" "${{INTERSHEET_REFS}}"
			(at {x:g} {y:g} 0)
			(hide yes)
			(show_name no)
			(do_not_autoplace no)
			(effects
				(font
					(size 1.27 1.27)
				)
			)
		)
	)
'''


def prop(name, value, x, y, hide=False):
    return f'''		(property "{name}" "{value}"
			(at {x:g} {y:g} 0)
{'			(hide yes)' + chr(10) if hide else ''}			(show_name no)
			(do_not_autoplace no)
			(effects
				(font
					(size 1.27 1.27)
				)
			)
		)
'''


def symbol(root, ref, lib_id, value, fp, ds, at, nets):
    x, y, rot = at
    out = f'''	(symbol
		(lib_id "{lib_id}")
		(at {x:g} {y:g} {rot})
		(unit 1)
		(body_style 1)
		(exclude_from_sim no)
		(in_bom yes)
		(on_board yes)
		(in_pos_files yes)
		(dnp no)
		(uuid "{uid('symbol', ref)}")
'''
    out += prop('Reference', ref, x, y - 6.35) + prop('Value', value, x, y + 6.35)
    out += prop('Footprint', fp, x, y, True) + prop('Datasheet', ds, x, y, True) + prop('Description', '', x, y, True)
    for n in sorted(nets):
        out += f'\t\t(pin "{n}"\n\t\t\t(uuid "{uid("pin", ref, n)}")\n\t\t)\n'
    out += f'''		(instances
			(project "{PROJECT}"
				(path "/{root}"
					(reference "{ref}")
					(unit 1)
				)
			)
		)
	)
'''
    return out


def main():
    t = SCH.read_bytes().decode('utf-8').replace('\r\n', '\n')      # KiCad wrote it with CRLF
    assert '"Diode:1.5KExxA"' not in t, 'already applied'
    root = re.search(r'^\t\(uuid "([^"]+)"\)', t, re.M).group(1)

    def drop(pattern, keep):
        nonlocal t
        n = 0
        for m in reversed(list(re.finditer(pattern, t, re.S))):
            if not keep(m):
                t = t[:m.start()] + t[m.end():]
                n += 1
        return n

    n = drop(r'\n\t\(symbol\n\t\t\(lib_id "[^"]+"\).*?\n\t\)(?=\n)',
             lambda m: re.search(r'\(property "Reference" "([^"]+)"', m.group(0)).group(1) not in GONE_REFS)
    assert n == len(GONE_REFS), n
    n = drop(r'\n\t\(global_label "([^"]+)"\n\t\t\(shape \w+\)\n\t\t\(at ([\d\.]+) ([\d\.]+) \d+\).*?\n\t\)(?=\n)',
             lambda m: (m.group(1), float(m.group(2)), float(m.group(3))) not in GONE_LABELS)
    assert n == len(GONE_LABELS), n
    n = drop(r'\n\t\(no_connect\n\t\t\(at ([\d\.]+) ([\d\.]+)\).*?\n\t\)(?=\n)',
             lambda m: (float(m.group(1)), float(m.group(2))) not in GONE_NC)
    assert n == len(GONE_NC), n
    n = drop(r'\n\t\t\(symbol "([^"]+)".*?\n\t\t\)(?=\n)', lambda m: m.group(1) not in GONE_LIBS)
    assert n == len(GONE_LIBS), n

    libs = {name: stock_symbol(lib, name) for lib, name in NEW_LIBS}
    end = t.index('\n\t)', t.index('(lib_symbols'))
    t = t[:end] + ''.join('\n' + s for s in libs.values()) + t[end:]

    add = ''
    for ref, lib_id, value, fp, ds, at, nets in PARTS:
        add += symbol(root, ref, lib_id, value, fp, ds, at, nets)
        lib_pins = pins(libs[lib_id.split(':')[1]])
        for n, net in nets.items():
            px, py = place(at, lib_pins[n])
            dx, dy = px - at[0], py - at[1]
            angle = (0 if dx > 0 else 180) if abs(dx) > abs(dy) else (270 if dy > 0 else 90)
            add += label(net, px, py, angle)
    tail = t.rindex('\n\t(sheet_instances')
    t = t[:tail + 1] + add + t[tail + 1:]
    SCH.write_bytes(t.replace('\n', '\r\n').encode('utf-8'))
    print('power input replaced in', SCH.name)


if __name__ == '__main__':
    main()
