# TokenStick v1 design notes

Draft, 2026-11-14. Nothing in this document has been validated on hardware.

## 1. Product

- External USB-C accelerator for local LLM and VLM inference, home and office use
- USB stick form factor
- Out of scope for v1: M.2 variant, camera or sensor inputs, secure element, rugged design

## 2. Chip selection

| Candidate | Outcome | Reason |
|---|---|---|
| Hailo-10H | Dropped | Was the first choice (native USB, 2.5 W). Dropped by project decision |
| DEEPX DX-M1 | Not suitable | PCIe only; a USB-only design cannot use it |
| Rockchip RK1828 | Selected | Native USB 3.0, in-package DRAM, LLM-oriented |

RK1820 (2.5 GB DRAM) uses the same package and is a possible lower-cost variant. RK1860 is the announced successor; availability is not confirmed.

## 3. RK1828 facts from the datasheet (Rev 1.4)

- Package: FCBGA-746, 19 x 19 mm, 28 x 28 grid, 0.65 mm pitch, 0.36 mm ball
- Ball groups: 343 VSS, 171 VDD_LOGIC, 15 VDD_TOP, 84 DRAM supply, 22 AVSS, about 110 signal and analog
- All signal balls sit in columns 1-8 on one side of the package; the rest is power and ground
- Supplies: 0.9 V core (VDD_LOGIC, VDD_TOP, VDD_PMU), DRAM rails at 1.4 V, 1.1 V, 2.5 V and 1.2 V, 0.9 V and 1.8 V analog, 3.3 V USB, VCCIO at 1.8 V or 3.3 V
- USB: one USB 3.0 controller, assignable to either of two combo PHYs shared with PCIe 2.1; one separate USB 2.0 port. 5 Gbps only
- Boot ROM: boots from SPI flash, eMMC or SD; code download over USB 2.0, UART or PCIe. Boot source strap on SARADC_IN0_BOOT
- Clock: 24 MHz
- Thermal: Tj max 125 C; theta-JC 0.06 C/W (simulated)
- Not in the datasheet: supply currents, power sequencing, min/max for the 0.9 V core rails, pin function and reset-state table

## 4. Blocks drawn so far

### USB-C DATA
- 24-pin USB-C receptacle, two TPD4E05U06 ESD arrays on the SuperSpeed pairs
- HD3SS3220 as UFP: handles CC and selects the SuperSpeed lane for cable orientation. Needs 5 V and 3.3 V
- Why a mux: the receptacle has two SuperSpeed lane sets and the RK1828 has one USB 3.0 controller
- Nets to the chip: USB_SSTX_P/N, USB_SSRX_P/N, USB_DP, USB_DM, VBUS_DATA

### PD POWER INPUT
- 16-pin USB-C receptacle (power only), STUSB4500 standalone PD sink, two AON7403 P-channel FETs (30 V) back to back as the VBUS switch, 24 V TVS
- Output net VIN, 9-20 V after negotiation
- The STUSB4500 NVM must be programmed with the wanted profiles. I2C is pulled up but no programming header exists yet

### 5V BUCK
- TPS56637 (6 A), 3.3 uH, 4 x 22 uF output, feedback 73.2k / 10k for 5 V, power-good on 5V_PG
- EN from a 169k / 36.1k divider on VIN (EN is a 5.5 V pin and must not be pulled up to VIN directly)
- MODE to GND through 10k for Eco-mode; leave open for FCCM

### RK1828
- USB 3.0 on combo PHY 0 (M0), 100 nF AC coupling on TX
- USB 2.0 D+/D- connected (required for boot ROM download)
- SARADC_IN0_BOOT to GND through 0 ohm, intended to select USB boot per the module datasheet
- Grounds connected; all supply pins still open

## 5. Open questions

1. Is the RK1828 sold as a bare chip, or only as a module?
2. Supply currents per rail, power sequencing, recommended PMIC
3. Power per performance mode. Can a lower-power mode keep the stick form factor fanless?
4. Does the RKNN3 runtime work over USB with x86 Linux hosts? Windows?
5. Boot: the module datasheet mentions USB 3.0 boot, the chip datasheet lists USB 2.0 download only
6. Correct handling of USB0_DRD_VBUSDET and USB0_DRD_ID (levels, divider)
7. Purpose and connection of VDD_LOGIC_PDN_0/1, DRAM_VMONI and the sense pins
8. May a design using this chip be published under an open license?

## 6. Decisions still to make

- Feed the core regulators from VIN directly or from the 5 V rail
- PCB layer count (6 layers looks feasible because signals escape from one side; not confirmed)
- Enclosure and cooling concept against the measured power draw

## 7. Datasheet review (2026-11-14)

The three peripheral circuits were first drawn from memory, then checked against the manufacturers' datasheets.

| Part | Finding | Action |
|---|---|---|
| TPS56637 | EN is rated 5.5 V; the first draft pulled it up to VIN (up to 20 V) | Replaced with the 169k / 36.1k divider from the TI reference design |
| TPS56637 | 5 V reference design uses 73.2k / 10k, 3.3 uH and 4 x 22 uF | Values updated, fourth output capacitor added |
| TPS56637 | MODE: open selects FCCM, 10k or less to GND selects Eco-mode | Placeholder replaced with 10k to GND |
| STUSB4500 | ST reference uses two back-to-back P-FETs; the first draft had one, which lets VIN feed back to VBUS through the body diode | Second FET added, gate network moved to the common source |
| STUSB4500 | Pin connections and the 470 / 22k / 100k / 100nF / 1k values match the ST schematic | None |
| HD3SS3220 | DIR is open drain and needs a pull-up (200k) for proper operation; the first draft left it open | 200k pull-up to 3V3 added |
| HD3SS3220 | PORT low for UFP, ADDR open for GPIO mode, 900k on VBUS_DET, ENn low | Matches, none |

Not covered by this review: the ST reference also shows a 100 ohm resistor and ESD parts on VBUS and CC whose exact placement was not readable from the extracted schematic text, and no layout guidance was checked.

## 8. First PCB placement (2026-11-14)

A first placement pass in Cherry Blossom to test the stick form factor. Nothing is routed yet.

- Board: 85 x 35 mm, 6 copper layers, 1.2 mm, ENIG finish, black solder mask, white silkscreen
- J1 (data USB-C) on the left edge, J2 (power USB-C) on the right edge
- RK1828 left of centre with its USB balls (bottom-left corner of the package) facing the HD3SS3220 and J1
- 5 V buck above the centre, PD sink and the back-to-back FETs next to J2
- All 44 parts drawn so far fit on the top side with room to spare; the bottom side is empty

What this does not show:

- The RK1828 supply stage is not drawn (rail currents and sequencing unknown). It will be the largest block after the chip itself and will most likely need the bottom side
- L1 uses a placeholder 1206 footprint; a real 3.3 uH inductor at this current is larger
- No RK1828 decoupling, crystal or reset parts
- Cooling: the module vendor lists 13.6 W average, which cannot be dissipated passively in this size. The enclosure has to act as the heatsink and may need a fan

Conclusion so far: the board outline looks feasible with double-sided assembly, but it cannot be confirmed before the supply figures arrive from Rockchip.

### First autoroute attempt

Design rules set to a 4 mil class (0.1 mm trace and clearance) because of the 0.65 mm BGA pitch. An exploratory autoroute connected 117 of 134 connections. The 17 left open are mostly at fine-pitch pads: J1 to the ESD parts and the mux, the SuperSpeed RX pair into the RK1828, and USB 2.0 D+/D-. These need the parts near J1 re-placed and the differential pairs routed by hand; the autorouter result is not usable as a final layout.

A second attempt with the mux turned towards J1 connected 112 of 134. The limiting factor is the dual-row 24-pin USB-C receptacle (J1): its two SMD pad rows cannot be fanned out by the autorouter. Routing was cleared again. Options: route the J1 fan-out by hand with vias, or change J1 to a receptacle with one SMD row and one through-hole row.

### Logo

"tokenstick" wordmark on the top side above the RK1828, 2.8 mm tall, as copper with a matching solder mask opening so it shows in ENIG gold on the black board. It uses the editor's stock font; the real logotype (with the USB-C glyph) has to be imported as a graphic in KiCad.
