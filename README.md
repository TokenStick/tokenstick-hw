<p align="center">
  <img src="./assets/banner.png" alt="TokenStick" width="100%">
</p>

# tokenstick-hw

Hardware design files for TokenStick, a USB-attached accelerator for running LLMs locally.

**Status: early design. Nothing here has been built or tested yet.** The schematic is partial, there is no PCB layout, and several values are placeholders. Do not fabricate from this repository.

## What the board is

- **Accelerator:** Rockchip RK1828 AI co-processor (20 TOPS, 5 GB in-package DRAM, FCBGA-746)
- **Data:** USB-C, USB 3.0 device (5 Gbps), with a SuperSpeed mux for cable flip
- **Power:** a second USB-C port with USB Power Delivery (9-20 V), stepped down on board
- **Form:** USB stick with an aluminum enclosure used as the heatsink

```
 USB-C DATA ──► ESD ──► HD3SS3220 (CC + SS mux) ──► RK1828
                                                      ▲
 USB-C PWR ──► STUSB4500 (PD sink) ──► P-FET ──► VIN ──► 5V buck ──► core / DRAM rails (not designed yet)
```

## Repository layout

| Path | Contents |
|---|---|
| `kicad/lib/` | KiCad symbol and footprint for RK1820/RK1828, the parsed pin list, and the generator script |
| `docs/design-notes.md` | Design decisions, datasheet findings, block descriptions and open questions |
| `docs/bom-draft.csv` | Parts placed in the schematic so far |
| `assets/` | Logo files |

## Design progress

- [x] Chip selection and architecture
- [x] RK1828 symbol and footprint (746 balls, generated from the datasheet pin list)
- [x] Schematic: USB-C data input, ESD, SuperSpeed mux
- [x] Schematic: USB PD power input
- [x] Schematic: 5 V buck
- [x] Schematic: RK1828 USB connections and boot strap
- [ ] Schematic: core (0.9 V), DRAM and analog power rails
- [ ] Schematic: clock, reset, power control, unused pins
- [ ] PCB layout
- [ ] Prototype and bring-up

The schematic is currently drawn in Cherry Blossom (a browser-based editor) and has not been exported to this repository yet.

## Known gaps

These are blocking items, not polish:

- **Power rails for the RK1828 are not designed.** The public datasheet gives voltages but no current figures and no power sequencing. This needs the Rockchip hardware design guide.
- **Power budget is unresolved.** A third-party RK1828 module lists 13.6 W average and 29.4 W peak. The 5 V buck (6 A) and the stick-sized enclosure have not been validated against that.
- **Peripheral circuits were drawn from memory.** The STUSB4500, HD3SS3220 and TPS56637 circuits have correct pinouts (from supplier data) but have not been checked against the manufacturers' reference designs.
- **Placeholders:** TPS56637 MODE resistor value, the inductor part and footprint, the 24 MHz crystal, and the VBUS detect divider.
- **The RK1828 land pattern is unverified.** Pad diameter (0.30 mm) is a starting value, not a fab-validated pattern.
- **Chip availability.** It is not confirmed that Rockchip sells the RK1828 as a bare chip rather than only as a module.

See `docs/design-notes.md` for details.

## License

Not chosen yet. Until a license is added, all rights are reserved.

Rockchip, RK1820 and RK1828 are trademarks of their owner. This project is not affiliated with Rockchip.
