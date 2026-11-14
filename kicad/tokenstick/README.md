# TokenStick KiCad board

Both files of the KiCad 7 project are generated:

- `build_board.py` holds the netlist, the placement and the hand-defined USB routes and writes `tokenstick.kicad_pcb`
- `build_schematic.py` reads the same netlist and writes `tokenstick.kicad_sch` and `../lib/TokenStick_Parts.kicad_sym`

```
python3 build_board.py       # needs the pcbnew module and the KiCad footprint libraries
python3 build_schematic.py   # needs the KiCad symbol libraries
kicad-cli sch export netlist tokenstick.kicad_sch -o /tmp/ts.net && python3 check_netlist.py /tmp/ts.net
python3 drc.py unconnected_items lib_footprint_issues
python3 impedance_fd.py      # field solver for the USB pair geometry, takes a few minutes
```

State:

- 6 layers: F.Cu signal, In1 GND, In2 signal, In3 one VBUS link at J1, In4 GND, B.Cu signal
- Routed by hand (in `build_board.py`): USB-C data connector to the ESD arrays, the HD3SS3220 mux, the AC coupling capacitors and the RK1828 SuperSpeed balls; USB 2.0 D+/D- on In2; CC1/CC2 on the bottom layer
- Routed by `autoroute.py`, a small grid maze router: USB PD input, FET switch, 5 V buck, 3.3 V regulator, mux support parts and a ground via for every SMD ground pad. Copper areas for VBUS, VIN, the switch node and 5 V are defined as rectangles in `build_board.py`
- Not routed: everything on the RK1828 except USB (365 ground balls, all supply rails)
- The schematic is drawn in five framed blocks (USB data path, PD input, 5 V buck, RK1828, test points). Passives sit next to the IC pin they belong to and are wired to it; other connections use net labels. `check_netlist.py` compares the netlist exported from the schematic with the board netlist by connectivity
- Board footprints are not linked to the schematic symbols by UUID. If you use "Update PCB from Schematic", tick "Re-link footprints to schematic symbols based on their reference designators"

See `docs/design-notes.md`, section 9, for the routing decisions and the open review items.
