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
- 16-pin USB-C receptacle (power only), STUSB4500 standalone PD sink, AON7403 P-channel FET (30 V) as the VBUS switch, 24 V TVS
- Output net VIN, 9-20 V after negotiation
- The STUSB4500 NVM must be programmed with the wanted profiles. I2C is pulled up but no programming header exists yet

### 5V BUCK
- TPS56637 (6 A), 2.2 uH, feedback 100k / 13.7k for about 4.98 V, power-good on 5V_PG
- MODE resistor value is a placeholder

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
