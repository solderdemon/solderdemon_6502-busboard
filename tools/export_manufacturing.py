"""Export the branded SolderDemon 6502 busboard fabrication set."""
from pathlib import Path
import os
import subprocess
import zipfile

ROOT = Path(__file__).resolve().parent.parent
CLI = Path(os.environ.get('KICAD_CLI', r'C:\Program Files\KiCad\10.0\bin\kicad-cli.exe'))
BOARD = ROOT / 'design' / 'solderdemon_6502-busboard.kicad_pcb'
SCHEMATIC = ROOT / 'design' / 'solderdemon_6502-busboard.kicad_sch'
OUTPUT = ROOT / 'manufacturing'
GERBER = OUTPUT / 'gerber'
NAME = 'solderdemon_6502-busboard'


def run(*args):
    subprocess.run([str(CLI), *map(str, args)], cwd=ROOT, check=True)


def main():
    GERBER.mkdir(parents=True, exist_ok=True)
    for old in GERBER.iterdir():
        if old.is_file():
            old.unlink()
    run('pcb', 'export', 'gerbers', '--layers',
        'F.Cu,B.Cu,F.Mask,B.Mask,F.SilkS,B.SilkS,Edge.Cuts',
        '-o', GERBER, BOARD)
    run('pcb', 'export', 'drill', '--excellon-separate-th', '-o', GERBER, BOARD)
    run('sch', 'export', 'pdf', '-o', OUTPUT / f'{NAME}-schematic.pdf', SCHEMATIC)
    archive = OUTPUT / f'{NAME}-gerbers.zip'
    with zipfile.ZipFile(archive, 'w', zipfile.ZIP_DEFLATED) as z:
        for path in sorted(GERBER.iterdir()):
            if path.is_file() and path.suffix.lower() in {
                '.gtl', '.gbl', '.gto', '.gbo', '.gts', '.gbs', '.gm1', '.drl', '.gbrjob'
            }:
                name = path.name.replace('rosco_6502-busboard', NAME)
                if path.suffix.lower() == '.gbrjob':
                    data = path.read_text(encoding='utf-8').replace('rosco_6502-busboard', NAME)
                    z.writestr(name, data)
                else:
                    z.write(path, name)
    print(archive, archive.stat().st_size, 'bytes')


if __name__ == '__main__':
    main()
