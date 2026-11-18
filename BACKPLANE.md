# SolderDemon 6502 Busboard Interface

Mechanical and electrical notes for the SolderDemon 6502 expansion busboard. The pin order follows the [rosco_6502](https://github.com/rosco-m68k/rosco_6502) bus.

---

## 1. Interconnect Architecture & Mating Concept

- **Busboard (Backplane):** HOST and expansion slots (SLOT 1–4) utilize straight male pin headers (2×18, 2.54 mm / 0.1" pitch) mounted on the top side of the board.
- **Host and full-size expansion cards:** carry a right-angle female 2×18 socket, KiCad `Connector_PinSocket_2.54mm:PinSocket_2x18_P2.54mm_Horizontal`, on the **component side at the left edge**, pin 1 5.775 mm from the edge and 14.425 mm from the top, pin 2 nearer the edge: exactly the host's J5 (its pads are the stock header mirrored). The compact SolderDemon 6502 RAM card instead mirrors this connector onto B.Cu at its **right edge**, with its component side facing the next slot. Its pin 1 still aligns with the triangle at the top of the slot. A ribbon cable is not an alternative for the host: between the mirrored J5 and the straight HOST header a plain 36-way ribbon swaps every odd/even pair (`VCC` onto `A0`).
- **Orientation & Insertion:** 
  - The host and full-size cards insert with their left edge downwards. The compact RAM card inserts with its right edge downwards. Pin 1 is always at the busboard's top edge.
  - The host component side faces the busboard's left edge (lower slot numbers); the compact RAM card component side faces the next slot.
- **Socket geometry** (measured in KiCad's STEP model of the stock socket): the contact row nearer the body, pin 2, lies 1.27 mm over the board; the far row, pin 1, 3.81 mm. So pin 1 is the upper row and a standing board's plane lies 1.27 mm beyond its slot's *even* pin row, 3.8 mm from pin 1. The 8.5 mm housing begins 1.27 mm beyond the pin 2 row and overhangs the board edge by about 6.7 mm; seated on the header's 2.54 mm base, the board's edge stands about 9 mm over the busboard.
- **Clearances:** with 20 mm pitch, a card's component side looks at the solder side of the board in the slot before it: 20 − 1.6 (board) − 5.1 (its own socket) − ~2 (solder tails) ≈ 11 mm over the header rows (y 13–59 mm), ~13 mm elsewhere. The host has 16 mm to the left edge; the M3 hardware at `H1`/`H4` (x ≈ 5 mm, under 3 mm high) stays about 2 mm under its CPU socket. Under a standing board's edge only parts lower than ~8 mm fit; the slot decouplers (6 mm) are nonetheless kept out of every board plane, on the half-pitch line 11.27 mm right of each slot's pin 1 (pin rows 1–3), under the next card's component side but well below its lower edge. Confirm the heights on the first assembled prototype.
- **Orientation marks:** a plain 2×18 header takes the socket either way round, and turned 180° the board gets `VCC` on `~ML` and the data bus on the address lines. So every slot carries a filled triangle pointing at its pin 1 from the left (the top end: pin 1 of a standing board is at the busboard's top edge), and the host has `PIN 1` and a triangle over J5, because the socket hides the square pad. Side view from the top edge, boards standing in their slots:

  ```
  busboard edge  HOST          SLOT 1        SLOT 2        SLOT 3        SLOT 4
                 #|            #|            #|            #|            #|
    components   #|            #|            #|            #|            #|
    toward the ◄ #|          ◄ #|          ◄ #|          ◄ #|          ◄ #|
    left edge    #|            #|            #|            #|            #|
              ═══╧══════════════╧══════════════╧══════════════╧══════════════╧═══
                 x=11           x=31           x=51           x=71           x=91
  ```
  `|` is the board, `#` its component side. This sketch depicts the host-style left-edge mounting; the compact RAM card is mirrored as described above.
- **Hot-Plugging:** Always power down the system before inserting or removing cards.

---

## 2. Shared Daughterboard Form Factor

The SolderDemon 6502 r1 host is **100 × 100 mm** and has four corner holes. The table below is the host and full-size card pattern. The compact RAM card uses a **58 × 90 mm** mirrored pattern documented in its form factor.

> **Design Rationale:** The bus connector is deliberately **not** centered along the 100 mm edge. It preserves the inherited `J5` connector offset on the host board. By using identical connector offsets across all boards, daughterboards share the exact same mating height, flush aligned edges, and consistent spacing.

### Coordinate reference for a 100 × 100 mm direct-mount card (socket on the component side, left edge)

*Origin (0, 0) is located at the top-left corner of the board contour, viewed from the front / component side.*

| Element | X (mm) | Y (mm) | Description |
|:---|---:|---:|:---|
| **Pin 1** | 5.775 | 14.425 | Square pad (A0), inner row |
| **Pin 2** | 3.235 | 14.425 | VCC / VCC_HOST, row nearer the edge |
| **Pin 35** | 5.775 | 57.605 | ~ML |
| **Pin 36** | 3.235 | 57.605 | D0 |
| **Top-Left Hole** | 4.450 | 4.450 | M3 mounting hole (Ø3.2 mm / Ø3.5 mm) |
| **Top-Right Hole** | 95.550 | 4.450 | M3 mounting hole |
| **Bottom-Left Hole** | 4.450 | 95.550 | M3 mounting hole |
| **Bottom-Right Hole** | 95.550 | 95.550 | M3 mounting hole |

- **Y-Axis Center & Offset:** The centerline of the 2×18 connector field along the Y-axis is located at `Y = 36.015 mm`, representing an offset of `13.985 mm` from the board centerline (`Y = 50.000 mm`).
- **Mounting Holes:** M3 mounting holes are placed 4.45 mm from board edges on all four corners.

---

## 3. Busboard Dimensions & Slot Pitch

The busboard measures **137 × 100 mm** with a uniform slot pitch of **20 mm**. It grew 5 mm to the left of the first draft (132 mm), which gives the host, facing left, 16 mm to the edge. As on the SolderDemon m68k busboard, the slot decouplers `C2`–`C6` stand vertically on the half-pitch line right of their slot (x = pin 1 + 11.27 mm), pad 1 (VCC) level with pin 1 and fed straight from pin 2, pad 2 (GND) two rows below, out of every board plane. `JP1` (PWR LINK) lies across `C2`'s line under it, pads on pin row 5, a free row under `C2`; the `CLK`, `GND` and `R/W` lanes step onto B.Cu (a via either side) where its two feeds cross them:

- **HOST Slot:** Pin 1 is located at `(X = 11.000 mm, Y = 14.425 mm)`
- **SLOT 1:** Pin 1 is located at `(X = 31.000 mm, Y = 14.425 mm)`; references follow the slots: SLOT n is `BUSn+1` with decoupler `Cn+2`
- **SLOT 2:** Pin 1 is located at `(X = 51.000 mm, Y = 14.425 mm)`
- **SLOT 3:** Pin 1 is located at `(X = 71.000 mm, Y = 14.425 mm)`
- **SLOT 4:** Pin 1 is located at `(X = 91.000 mm, Y = 14.425 mm)`
- **Mounting Holes:** 6× M3 mounting holes (3.2 mm diameter with grounding annular rings), 5 mm in from the edges, three along each long edge: the four corners (`H1`–`H4`) and the middle of the top (`H5`) and bottom (`H6`) edge, halfway between the corner holes at X = 68.5 mm.

---

## 4. Power Delivery & Isolation (JP1 PWR LINK)

- **Power Inputs:** 5V DC supplied through:
  - USB Type-C receptacle (`J3`, with 5.1 kΩ CC pull-downs)
  - DC Barrel Jack (`J1`, 5.5 / 2.1 mm center-positive)
  - 2-pin screw terminal / header (`J2`, 5V IN)
- **Source Selection:** one jumper cap on the 2×3 header `JP2`, across the USB, DC or TERM row (odd pins: 1 terminal, 3 DC jack, 5 USB-C; even pins: the common input). The rows follow the inputs down the right edge: USB-C, DC jack, terminal `J2`. The header replaces the 1N5819 OR-ing diodes of the first draft, which dropped up to ~0.6 V at 1 A. Two caps at once tie two supplies together.
- **Protection:** `D1` (1.5KE6.8A TVS) clamps `VCC` against transients and shorts a reversed adapter. There is no fuse, so a sustained fault ends only at the adapter's current limit.
- **Power Switch:** `SW1`, an NKK M2021SS1W01 DPST toggle (as on the m68k busboard) with both poles in parallel, connects the selected input to `VCC`. Its lever stands at x = 122.5 mm, clear of a card in SLOT 4.
- **Back-feeding:** without diodes, a host powered from its own jack with `JP1` fitted drives the selected busboard input. Remove `JP1` when the host has its own supply.
- **Power Link (`JP1`):**
  - **Jumper Installed (Default):** The host slot (`VCC_HOST`) and peripheral slots (`VCC`) are tied together, powering the entire system from the busboard.
  - **Jumper Removed:** The host slot (`BUS1`) power rail is isolated, allowing the SolderDemon 6502 host to be powered via its own supply while peripheral cards are powered from the busboard.

---

## 5. Design Verification & Status

- **Busboard:** KiCad 10.0.8 reports 0 ERC violations, 4 hole-clearance errors at J3, 0 unrouted pads and 35 schematic-parity warnings.
- **Signal Integrity:** Direct straight bus lines across all five slots, GND poured on both sides, 470 µF bulk decoupling and individual 100 nF bypass capacitors at each slot. `R2`/`C7` (10 kΩ, 1 nF) on `~RESET` only catch noise: the host drives the line open-drain with its own 3.3 kΩ pull-up and a 2^18-cycle debounce in its CPLD.
