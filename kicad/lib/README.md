# TokenStick KiCad library: RK1820 / RK1828

Generated from the Rockchip RK1820/RK1828 Datasheet Rev 1.4 (Table 2-1 pin list, Fig. 2-4 and 2-6 package data).

## Contents
- `TokenStick.kicad_sym`: symbol `RK1828`, 7 units, 746 pins
- `TokenStick.pretty/`: footprint `Rockchip_RK182X_FCBGA-746_19.0x19.0mm_Layout28x28_P0.65mm`
- `rk182x_pins.csv`: ball number to pin name, as parsed from the datasheet
- `gen_rk182x.py`: generator (`python3 gen_rk182x.py rk182x_pins.csv <out_dir>`)

## Symbol units
1. USB / PCIe / clock / system (24)
2. GPIO0 bank (32)
3. GPIO1 bank (32)
4. Core power 0.9V: VDD_LOGIC x171, VDD_TOP x15, VDD_PMU_0V9, sense and PDN pins
5. DRAM power: 1.4V x32, 1.1V x32, 2.5V x10, 1.2V x10, DRAM_VMONI
6. Analog and IO power (15)
7. Ground: VSS x343, AVSS x22, PLL_AVSS, TVSS

Balls that share a rail are stacked on one visible pin (the rest are hidden, passive).

## Footprint
- Body 19.0 x 19.0 mm, 28 x 28 grid, pitch 0.65 mm, A1 top-left (top view)
- Pad diameter 0.30 mm (ball 0.36 mm nominal). Adjust to your fab's BGA rules before layout.

## Install in KiCad
Preferences > Manage Symbol Libraries: add `TokenStick.kicad_sym` with nickname `TokenStick`.
Preferences > Manage Footprint Libraries: add `TokenStick.pretty` with nickname `TokenStick`.

## Not verified
- VDD_LOGIC_PDN_0/1, DRAM_VMONI, VDD_LOGIC_SENSE_P and VSS_SENSE_N are left as separate passive pins.
  Their intended connection is not described in the datasheet; check the Rockchip hardware design guide.
- Pin electrical types for signals are generic (bidirectional). The datasheet has no pin function table.
- Pad size and solder mask are a starting point, not a fab-validated land pattern.
