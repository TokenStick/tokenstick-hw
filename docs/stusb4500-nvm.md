# STUSB4500 NVM configuration

Draft, 2026-11-14. Not tested on hardware. Parameter names are those of the ST datasheet (DS12499, section 5) and of the ST configuration GUI (STSW-STUSB002).

## Why the factory setting is not enough

A blank STUSB4500 asks for 5 V / 1.5 A, 15 V / 1.5 A and 20 V / 1 A, and it closes the VBUS switch as soon as any source is attached. For this board that means:

- With a 5 V-only source the FETs close and VIN sits at 5 V. The buck cannot regulate 5 V from 5 V. The EN divider (169k / 36.1k) should keep it off, but the board then looks powered while nothing runs
- The largest request is 22.5 W (15 V / 1.5 A). The buck can deliver 30 W, so the request does not cover what the board may draw

The chip compares voltages for an exact match and accepts a source profile only if the source offers at least the requested current. A request that is too high therefore excludes smaller chargers; a request that is too low lets the board overload a charger.

## Settings that do not depend on the RK1828

| Parameter | Value | Reason |
|---|---|---|
| SNK_PDO_NUMB | 3 | 5 V is mandatory; two profiles above it |
| V_SNK_PDO2 | 15 V | Fallback for chargers without 20 V |
| V_SNK_PDO3 | 20 V | Highest priority; lowest input current |
| POWER_ONLY_ABOVE_5V | 1 | VBUS switch closes only with a 15 V or 20 V contract, so VIN is never 5 V |
| REQ_SRC_CURRENT | 0 | Request the configured current, not everything the source offers |
| USB_COMM_CAPABLE | 0 | J2 has no data lines |
| VBUS discharge | enabled (factory setting) | R1 and R2 are fitted for it |
| POWER_OK and GPIO configuration | factory setting | Pins are not connected |

9 V is left out on purpose: at 3 A (the limit of a cable without e-marker) it gives 27 W, less than the buck can ask for.

## Settings that wait for the power budget

The PDO currents follow from the input power of the board, which is not known until the RK1828 supply currents are (Rockchip reply or a measurement on a module).

| Parameter | Provisional value | Basis |
|---|---|---|
| I_SNK_PDO1 (5 V) | 1.5 A | Factory value; unused because the switch stays open at 5 V |
| I_SNK_PDO2 (15 V) | 2.25 A | Upper bound: 6 A buck limit, 30 W out at about 90 % efficiency = 33 W in |
| I_SNK_PDO3 (20 V) | 1.75 A | Same bound |

With these values the board needs a charger of 45 W or more: 30 W chargers offer 15 V / 2 A and 20 V / 1.5 A and would be rejected. If the measured peak input power is below 30 W, lower both currents so that 30 W chargers work (15 V / 2 A, 20 V / 1.5 A). Do not program production units before this is settled.

## Programming

- Access: test points SCL, SDA and GND next to the PD controller. The pull-ups (10k to the chip's 2.7 V regulator) are on the board; switch off any pull-ups on the adapter
- Power: plug any USB-C source into the power connector. The chip is supplied from VBUS, the VBUS switch may stay open
- Address: 0x28 (ADDR0 and ADDR1 are tied to ground)
- Tools: ST GUI STSW-STUSB002 with a NUCLEO-F072RB as I2C bridge, or ST's reference code STSW-STUSB004 on any microcontroller
- The new values take effect after a power cycle or a reset of the chip
- Read the NVM back and check a contract with a 45 W charger and with a 5 V-only charger (VIN must stay at 0 V)

Once the I2C lines also go to the RK1828 (software requirement 1 in `design-notes.md`, section 18), the same lines allow the host to read the contract. The test points stay for production programming.
