# TokenStick KiCad board

Both files of the KiCad 7 project are generated:

- `build_board.py` holds the netlist, the placement and the hand-defined USB routes and writes `tokenstick.kicad_pcb`
- `build_schematic.py` reads the same netlist and writes `tokenstick.kicad_sch` and `../lib/TokenStick_Parts.kicad_sym`

```
python3 build_board.py       # needs the pcbnew module and the KiCad footprint libraries
python3 build_schematic.py   # needs the KiCad symbol libraries
python3 drc.py unconnected_items lib_footprint_issues silk_overlap silk_over_copper solder_mask_bridge
```

State:

- 6 layers: F.Cu signal, In1 GND, In2 signal, In3 unused, In4 GND, B.Cu signal
- Routed: USB-C data connector to the ESD arrays, the HD3SS3220 mux, the AC coupling capacitors and the RK1828 SuperSpeed balls; USB 2.0 D+/D- on In2; CC1/CC2 on the bottom layer
- Not routed: power, ground connections of SMD pads, PD input, 5 V buck, everything else on the RK1828
- The schematic is a label-style netlist view: every connected pin carries a global label, there are no drawn wires. Its exported netlist matches the board netlist pin for pin
- Board footprints are not linked to the schematic symbols by UUID. If you use "Update PCB from Schematic", tick "Re-link footprints to schematic symbols based on their reference designators"

See `docs/design-notes.md`, section 9, for the routing decisions and the open review items.
