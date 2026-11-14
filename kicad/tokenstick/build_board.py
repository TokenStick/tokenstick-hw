#!/usr/bin/env python3
"""Generate tokenstick.kicad_pcb (KiCad 7) from the netlist below.

Placement and the hand-defined USB routes are written in board coordinates:
millimetres, origin at the board centre, x to the right, y up.
Run:  python3 build_board.py   (needs the pcbnew Python module and the KiCad footprint libraries)
"""
import csv, os, sys
import pcbnew

HERE = os.path.dirname(os.path.abspath(__file__))
LIB = os.path.join(HERE, "..", "lib", "TokenStick.pretty")
KLIB = os.environ.get("KICAD7_FOOTPRINT_DIR", "/usr/share/kicad/footprints")
OX, OY = 100.0, 80.0
W, H, R = 85.0, 35.0, 2.0


def mm(v):
    return pcbnew.FromMM(v)


def P(x, y):
    return pcbnew.VECTOR2I(mm(OX + x), mm(OY - y))


# ---------------------------------------------------------------- parts
# ref: (library dir, footprint, value, x, y, rotation in KiCad degrees)
K = lambda lib: os.path.join(KLIB, lib + ".pretty")
C0402, R0402 = (K("Capacitor_SMD"), "C_0402_1005Metric"), (K("Resistor_SMD"), "R_0402_1005Metric")
C0603, C0805 = (K("Capacitor_SMD"), "C_0603_1608Metric"), (K("Capacitor_SMD"), "C_0805_2012Metric")
DFN8 = (K("Package_DFN_QFN"), "DFN-8-1EP_3x3mm_P0.65mm_EP1.55x2.4mm")
PARTS = {
    # USB-C data side
    "J1": (K("Connector_USB"), "USB_C_Receptacle_Amphenol_12401610E4-2A", "12401610E4#2A", -37.5, 0, 270),
    "U4": (LIB, "USON-10_2.5x1.0mm_P0.5mm", "TPD4E05U06DQA", -29.5, 3.0, 0),
    "U5": (LIB, "USON-10_2.5x1.0mm_P0.5mm", "TPD4E05U06DQA", -29.5, -3.0, 0),
    "U3": (LIB, "Texas_RNH0030A_WQFN-30-1EP_2.5x4.5mm_P0.4mm_EP1.2x3.2mm", "HD3SS3220RNH", -26.0, -3.4, 180),
    "C15": (*C0402, "100nF", -23.4, -6.0, 90),
    "C16": (*C0402, "100nF", -22.4, -4.6, 90),
    "C7": (*C0402, "100nF", -24.2, 0.5, 90),
    "C8": (*C0402, "100nF", -27.7, -7.0, 0),
    "R7": (*R0402, "900k", -25.0, -6.9, 0),
    "R15": (*R0402, "200k", -25.2, 0.45, 90),
    "R13": (*R0402, "0R", -23.0, 0.6, 90),
    # 3.3 V for the mux
    "U7": (K("Package_TO_SOT_SMD"), "SOT-23-5", "AP2112K-3.3", -25.0, 7.6, 0),
    "C18": (*C0402, "1uF", -27.6, 7.6, 90),
    "C19": (*C0402, "1uF", -25.0, 10.0, 0),
    "U1": (LIB, "Rockchip_RK182X_FCBGA-746_19.0x19.0mm_Layout28x28_P0.65mm", "RK1828", -12.0, 0, 0),
    "LG1": (LIB, "TokenStick_Logotype", "logotype", -24.0, 13.8, 0),
    # 5 V buck
    "U6": (LIB, "Texas_RPA0010A_VQFN-HR-10_3x3mm", "TPS56637RPA", 13.6, -0.6, 0),
    "L1": (K("Inductor_SMD"), "L_Coilcraft_XAL5030-XXX", "3.3uH", 14.0, -5.7, 270),
    "C12": (*C0805, "22uF", 11.0, -10.5, 270), "C13": (*C0805, "22uF", 13.0, -10.5, 270),
    "C14": (*C0805, "22uF", 15.0, -10.5, 270), "C17": (*C0805, "22uF", 17.0, -10.5, 270),
    "C9": (*C0805, "10uF 35V", 16.6, 1.65, 90), "C10": (*C0805, "10uF 35V", 18.6, 1.65, 90),
    "C11": (*C0402, "100nF", 16.5, -2.0, 0),
    "R8": (*R0402, "73.2k", 9.8, 0.3, 0), "R9": (*R0402, "10k", 7.8, 0.3, 0),
    "R10": (*R0402, "100k", 9.8, -0.9, 0), "R11": (*R0402, "169k", 9.8, 1.5, 0),
    "R14": (*R0402, "36.1k", 7.8, 1.5, 0), "R12": (*R0402, "10k", 9.8, 2.7, 0),
    # USB PD input
    "J2": (K("Connector_USB"), "USB_C_Receptacle_GCT_USB4105-xx-A_16P_TopMnt_Horizontal", "USB4105-GF-A", 38.3, 0, 90),
    "U2": (K("Package_DFN_QFN"), "QFN-24-1EP_4x4mm_P0.5mm_EP2.6x2.6mm", "STUSB4500QTR", 28.0, -9.5, 180),
    "Q1": (*DFN8, "AON7403", 25.9, 0, 180), "Q2": (*DFN8, "AON7403", 30.4, 0, 0),
    "D1": (K("Diode_SMD"), "D_SOD-123F", "SMF24A", 32.15, -4.4, 270),
    "C5": (*C0805, "10uF 35V", 20.6, 1.65, 90), "C6": (*C0805, "10uF 35V", 22.6, 1.65, 90),
    "R1": (*R0402, "470", 24.3, -10.75, 0), "R2": (*R0402, "1k", 27.95, -5.6, 270),
    "R3": (*R0402, "22k", 24.3, -9.75, 0), "R4": (*R0402, "100k", 28.15, -2.6, 0),
    "R5": (*R0402, "10k", 29.05, -5.6, 270), "R6": (*R0402, "10k", 30.1, -5.6, 270),
    "C1": (*C0402, "100nF", 28.15, -3.8, 0), "C2": (*C0402, "1uF", 28.75, -13.2, 270),
    "C3": (*C0402, "1uF", 27.75, -13.2, 270), "C4": (*C0603, "1uF 50V", 32.2, -12.6, 0),
}

# ---------------------------------------------------------------- netlist
# Polarity note: lane 1 (J1 A2/A3 and B11/B10) is connected to the mux with P and N exchanged.
# With the mux on the top side this is the only way to route both lanes of one plug orientation
# without crossing the pair. USB 3.x receivers must detect and correct lane polarity inversion.
NETS = {
    "GND": "J1.A1 J1.A12 J1.B1 J1.B12 J1.S1 U3.4 U3.12 U3.13 U3.28 U3.29 U3.31 U4.3 U4.8 U5.3 U5.8 C7.2 C8.2 R13.2 U7.2 C18.2 C19.2 "
           "J2.A1 J2.A12 J2.B1 J2.B12 J2.S1 U2.6 U2.10 U2.12 U2.13 U2.22 U2.25 D1.2 C2.2 C3.2 C4.2 C5.2 C6.2 "
           "U6.3 U6.9 C9.2 C10.2 C12.2 C13.2 C14.2 C17.2 R9.2 R12.2 R14.2",
    "VBUS_DATA": "J1.A4 J1.A9 J1.B4 J1.B9 R7.1",
    "DATA_CC1": "J1.A5 U3.2", "DATA_CC2": "J1.B5 U3.1",
    "USB_DP": "J1.A6 J1.B6 U1.AG2", "USB_DM": "J1.A7 J1.B7 U1.AH2",
    "C_TX1_P": "J1.A2 U4.4 U4.7 U3.16", "C_TX1_N": "J1.A3 U4.5 U4.6 U3.17",
    "C_RX1_P": "J1.B11 U4.1 U4.10 U3.14", "C_RX1_N": "J1.B10 U4.2 U4.9 U3.15",
    "C_RX2_N": "J1.A10 U5.1 U5.10 U3.18", "C_RX2_P": "J1.A11 U5.2 U5.9 U3.19",
    "C_TX2_N": "J1.B3 U5.4 U5.7 U3.20", "C_TX2_P": "J1.B2 U5.5 U5.6 U3.21",
    "USB_SSTX_P": "U3.6 C15.2", "USB_SSTX_N": "U3.7 C16.2",
    "Net-(C15-1)": "C15.1 U1.AE1", "Net-(C16-1)": "C16.1 U1.AE2",
    "USB_SSRX_P": "U3.9 U1.AF2", "USB_SSRX_N": "U3.10 U1.AG1",
    "USB_DIR": "U3.11 R15.1", "Net-(R7-2)": "R7.2 U3.5", "Net-(R13-1)": "R13.1 U1.W1",
    "3V3": "U3.8 C7.1 R15.2 U7.5 C19.1",
    "5V": "U7.1 U7.3 C18.1 U3.30 C8.1 L1.2 C12.1 C13.1 C14.1 C17.1 R8.1 R10.1",
    "VIN": "Q1.5 Q1.6 Q1.7 Q1.8 Q1.9 R2.1 C5.1 C6.1 U6.8 C9.1 C10.1 R11.1",
    "VBUS_PD": "J2.A4 J2.A9 J2.B4 J2.B9 Q2.5 Q2.6 Q2.7 Q2.8 Q2.9 U2.24 D1.1 R1.1 C4.1",
    "PD_SRC": "Q1.1 Q1.2 Q1.3 Q2.1 Q2.2 Q2.3 R4.1 C1.1",
    "PD_GATE": "Q1.4 Q2.4 R3.1 R4.2 C1.2",
    "PD_CC1": "J2.A5 U2.1 U2.2", "PD_CC2": "J2.B5 U2.4 U2.5",
    "PD_SCL": "U2.7 R5.2", "PD_SDA": "U2.8 R6.2", "VREG_2V7": "U2.23 C2.1 R5.1 R6.1",
    "U2_VREG_1V2": "U2.21 C3.1", "Net-(R1-2)": "R1.2 U2.18", "Net-(R2-2)": "R2.2 U2.9", "Net-(R3-2)": "R3.2 U2.16",
    "BUCK_SW": "U6.6 L1.1 C11.2", "Net-(C11-1)": "C11.1 U6.7", "BUCK_FB": "U6.2 R8.2 R9.1",
    "BUCK_EN": "U6.1 R11.2 R14.1", "5V_PG": "U6.4 R10.2", "Net-(R12-1)": "U6.10 R12.1",
}

# ---------------------------------------------------------------- routes (x, y in board coordinates)
SS, BGA = 0.15, 0.10
TRACKS = [  # (net, layer, width, [points])
    # J1 A row to the ESD arrays, top layer
    ("C_TX1_P", "F.Cu", SS, [(-32.48, 2.25), (-31.75, 2.25), (-31.5, 2.5), (-29.115, 2.5)]),
    ("C_TX1_N", "F.Cu", SS, [(-32.48, 1.75), (-31.75, 1.75), (-31.5, 2.0), (-29.115, 2.0)]),
    ("C_RX2_N", "F.Cu", SS, [(-32.48, -1.75), (-31.75, -1.75), (-31.5, -2.0), (-29.115, -2.0)]),
    ("C_RX2_P", "F.Cu", SS, [(-32.48, -2.25), (-31.75, -2.25), (-31.5, -2.5), (-29.115, -2.5)]),
    # J1 B row: via, bottom layer under the A row, via up at the ESD arrays
    ("C_RX1_P", "F.Cu", SS, [(-34.18, 2.5), (-35.0, 2.5)]),
    ("C_RX1_P", "B.Cu", SS, [(-35.0, 2.5), (-32.9, 2.5), (-31.4, 4.0)]),
    ("C_RX1_P", "F.Cu", SS, [(-31.4, 4.0), (-29.115, 4.0)]),
    ("C_RX1_N", "F.Cu", SS, [(-34.18, 2.0), (-33.33, 2.0)]),
    ("C_RX1_N", "B.Cu", SS, [(-33.33, 2.0), (-32.2, 2.0), (-30.7, 3.5)]),
    ("C_RX1_N", "F.Cu", SS, [(-30.7, 3.5), (-29.115, 3.5)]),
    ("C_TX2_P", "F.Cu", SS, [(-34.18, -2.0), (-35.0, -2.0)]),
    ("C_TX2_P", "B.Cu", SS, [(-35.0, -2.0), (-33.6, -2.0), (-31.6, -4.0), (-31.4, -4.0)]),
    ("C_TX2_P", "F.Cu", SS, [(-31.4, -4.0), (-29.115, -4.0)]),
    ("C_TX2_N", "F.Cu", SS, [(-34.18, -1.5), (-33.33, -1.5)]),
    ("C_TX2_N", "B.Cu", SS, [(-33.33, -1.5), (-32.9, -1.5), (-30.9, -3.5), (-30.7, -3.5)]),
    ("C_TX2_N", "F.Cu", SS, [(-30.7, -3.5), (-29.115, -3.5)]),
    # ESD arrays to the mux, top layer
    ("C_TX1_P", "F.Cu", SS, [(-29.115, 2.5), (-28.35, 2.5), (-28.1, 2.25), (-28.1, -1.35), (-27.85, -1.6), (-27.35, -1.6)]),
    ("C_TX1_N", "F.Cu", SS, [(-29.115, 2.0), (-28.65, 2.0), (-28.4, 1.75), (-28.4, -1.75), (-28.15, -2.0), (-27.25, -2.0)]),
    ("C_RX1_P", "F.Cu", SS, [(-29.115, 4.0), (-26.8, 4.0), (-26.4, 3.6), (-26.4, -1.15)]),
    ("C_RX1_N", "F.Cu", SS, [(-29.115, 3.5), (-27.1, 3.5), (-26.8, 3.2), (-26.8, -1.05)]),
    ("C_RX2_N", "F.Cu", SS, [(-29.115, -2.0), (-28.9, -2.0), (-28.5, -2.4), (-27.25, -2.4)]),
    ("C_RX2_P", "F.Cu", SS, [(-29.115, -2.5), (-28.8, -2.5), (-28.5, -2.8), (-27.25, -2.8)]),
    ("C_TX2_N", "F.Cu", SS, [(-29.115, -3.5), (-28.7, -3.5), (-28.4, -3.2), (-27.25, -3.2)]),
    ("C_TX2_P", "F.Cu", SS, [(-29.115, -4.0), (-28.7, -4.0), (-28.3, -3.6), (-27.25, -3.6)]),
    # mux to the AC coupling capacitors and the RK1828 transmit balls, top layer
    ("USB_SSTX_N", "F.Cu", SS, [(-24.75, -2.8), (-22.7, -2.8), (-22.4, -3.1), (-22.4, -4.12)]),
    ("USB_SSTX_P", "F.Cu", SS, [(-24.75, -3.2), (-23.7, -3.2), (-23.4, -3.5), (-23.4, -5.52)]),
    ("Net-(C16-1)", "F.Cu", SS, [(-22.4, -5.08), (-22.4, -6.25), (-22.15, -6.5), (-21.6, -6.5)]),
    ("Net-(C16-1)", "F.Cu", BGA, [(-21.6, -6.5), (-20.45, -6.5), (-20.125, -6.825)]),
    ("Net-(C15-1)", "F.Cu", SS, [(-23.4, -6.48), (-23.4, -6.6), (-23.175, -6.825), (-21.6, -6.825)]),
    ("Net-(C15-1)", "F.Cu", BGA, [(-21.6, -6.825), (-20.775, -6.825)]),
    # mux receive pair: crosses under the transmit pair on the bottom layer
    ("USB_SSRX_N", "F.Cu", SS, [(-24.65, -1.6), (-23.9, -1.6), (-23.8, -1.5), (-22.7, -1.5), (-22.6, -1.6)]),
    ("USB_SSRX_N", "B.Cu", SS, [(-22.6, -1.6), (-22.5, -1.7), (-22.5, -7.125), (-21.9, -7.725)]),
    ("USB_SSRX_N", "F.Cu", BGA, [(-21.9, -7.725), (-21.7, -7.725), (-21.3, -8.125), (-20.775, -8.125)]),
    ("USB_SSRX_P", "F.Cu", SS, [(-24.75, -2.0), (-23.2, -2.0)]),
    ("USB_SSRX_P", "B.Cu", SS, [(-23.2, -2.0), (-23.2, -2.4), (-22.8, -2.8), (-22.8, -8.15), (-22.5, -8.45)]),
    ("USB_SSRX_P", "F.Cu", BGA, [(-22.5, -8.45), (-20.45, -8.45), (-20.45, -7.8), (-20.125, -7.475)]),
    # USB 2.0: both rows tied at J1, pair on inner layer 2 to the RK1828
    ("USB_DP", "F.Cu", SS, [(-34.18, 0), (-33.5, 0), (-33.25, 0.25), (-31.0, 0.25)]),
    ("USB_DM", "F.Cu", SS, [(-32.48, -0.25), (-31.6, -0.25)]),
    ("USB_DM", "F.Cu", SS, [(-34.18, 0.5), (-35.0, 0.5)]),
    ("USB_DM", "In2.Cu", SS, [(-35.0, 0.5), (-32.35, 0.5), (-31.6, -0.25), (-30.2, -0.25), (-29.9, -0.55),
                              (-29.9, -10.0), (-29.6, -10.3), (-21.05, -10.3), (-20.45, -10.9)]),
    ("USB_DP", "In2.Cu", SS, [(-31.0, 0.25), (-30.6, 0.25), (-30.4, 0.05), (-29.9, 0.05), (-29.6, -0.25),
                              (-29.6, -9.7), (-29.3, -10.0), (-19.8, -10.0)]),
    ("USB_DP", "F.Cu", BGA, [(-20.125, -8.125), (-19.8, -8.45), (-19.8, -10.0)]),
    ("USB_DM", "F.Cu", BGA, [(-20.125, -8.775), (-20.125, -9.2), (-20.45, -9.525), (-20.45, -10.9)]),
    # CC lines on the bottom layer
    ("DATA_CC1", "F.Cu", SS, [(-32.48, 0.75), (-31.6, 0.75)]),
    ("DATA_CC1", "B.Cu", SS, [(-31.6, 0.75), (-29.45, 0.75), (-23.9, -4.8)]),
    ("DATA_CC1", "F.Cu", BGA, [(-23.9, -4.8), (-24.75, -4.8)]),
    ("DATA_CC2", "F.Cu", SS, [(-34.18, -0.5), (-35.0, -0.5)]),
    ("DATA_CC2", "B.Cu", SS, [(-35.0, -0.5), (-34.75, -0.75), (-29.2, -0.75), (-24.2, -5.75)]),
    ("DATA_CC2", "F.Cu", BGA, [(-24.2, -5.75), (-24.2, -5.45), (-24.45, -5.2), (-24.65, -5.2)]),
]
VIAS = [  # (net, x, y)
    ("C_RX1_P", -35.0, 2.5), ("C_RX1_P", -31.4, 4.0), ("C_RX1_N", -33.33, 2.0), ("C_RX1_N", -30.7, 3.5),
    ("C_TX2_P", -35.0, -2.0), ("C_TX2_P", -31.4, -4.0), ("C_TX2_N", -33.33, -1.5), ("C_TX2_N", -30.7, -3.5),
    ("USB_SSRX_N", -22.6, -1.6), ("USB_SSRX_N", -21.9, -7.725), ("USB_SSRX_P", -23.2, -2.0), ("USB_SSRX_P", -22.5, -8.45),
    ("USB_DP", -31.0, 0.25), ("USB_DP", -19.8, -10.0), ("USB_DM", -31.6, -0.25), ("USB_DM", -35.0, 0.5), ("USB_DM", -20.45, -10.9),
    ("DATA_CC1", -31.6, 0.75), ("DATA_CC1", -23.9, -4.8), ("DATA_CC2", -35.0, -0.5), ("DATA_CC2", -24.2, -5.75),
]
VIA_D, VIA_DRILL = 0.45, 0.20
PWR = 0.35
TRACKS += [  # common source of the back-to-back FETs, switch node stub
    ("PD_SRC", "F.Cu", PWR, [(27.45, -0.975), (27.45, 0.325)]), ("PD_SRC", "F.Cu", PWR, [(28.85, -0.325), (28.85, 0.975)]),
    ("PD_SRC", "F.Cu", PWR, [(27.45, -0.325), (28.85, -0.325)]), ("PD_SRC", "F.Cu", PWR, [(27.45, 0.325), (28.85, 0.325)]),
    ("BUCK_SW", "F.Cu", 0.25, [(13.975, -3.0), (13.975, -1.6)]),
    # mux 3.3 V pin: the only way out is a via between the neighbouring pairs
    ("GND", "F.Cu", 0.2, [(28.25, -11.4375), (28.25, -10.5)]),      # STUSB4500 VSYS pin to its exposed pad
    ("3V3", "F.Cu", BGA, [(-24.75, -2.4), (-23.9, -2.4)]),
    ("Net-(R7-2)", "F.Cu", BGA, [(-24.75, -3.6), (-24.2, -3.6), (-23.95, -3.85), (-23.95, -4.1)]),
    # VBUS sense: the two VBUS pads of each connector half are tied; only the lower half reaches R7 (see design notes)
    ("VBUS_DATA", "F.Cu", SS, [(-32.48, -1.25), (-31.0, -1.25)]),
    ("VBUS_DATA", "F.Cu", SS, [(-34.18, -1.0), (-33.2, -1.0), (-32.95, -1.25), (-32.48, -1.25)]),
    ("VBUS_DATA", "F.Cu", SS, [(-34.18, 1.5), (-33.1, 1.5), (-32.85, 1.25), (-32.48, 1.25)]),
]
ZONES = [  # copper areas on the top layer: (net, xmin, xmax, ymin, ymax)
    ("VIN", 14.3, 26.68, -1.2, 1.2),
    ("VBUS_PD", 31.5, 33.4, -3.7, 2.7), ("VBUS_PD", 29.62, 33.4, -1.2, 1.2),
    ("BUCK_SW", 11.7, 16.3, -4.5, -2.75),
    ("5V", 10.2, 17.8, -9.9, -6.6),
]
POWER_NETS = {"VBUS_PD", "PD_SRC", "VIN", "BUCK_SW", "5V", "3V3"}
POWER_REFS = {"J2", "Q1", "Q2", "U6", "L1", "C5", "C6", "C9", "C10", "C12", "C13", "C14", "C17", "U7", "C18", "C19"}   # pads that carry load current
VIAS += [("3V3", -23.9, -2.4), ("VBUS_DATA", -31.0, -1.25), ("Net-(R7-2)", -23.95, -4.1)]
ROUTE_FIRST = ["VBUS_DATA", "Net-(R7-2)", "3V3"]      # short nets in the crowded USB corner
HAND_ROUTED = {t[0] for t in TRACKS} - {"PD_SRC", "BUCK_SW", "3V3", "VBUS_DATA", "Net-(R7-2)"}


def build():
    b = pcbnew.BOARD()
    b.SetCopperLayerCount(6)
    ds = b.GetDesignSettings()
    ds.m_MinClearance = mm(0.1); ds.m_TrackMinWidth = mm(0.1); ds.m_ViasMinSize = mm(0.45)
    ds.m_MinThroughDrill = mm(0.2); ds.m_ViasMinAnnularWidth = mm(0.1); ds.m_CopperEdgeClearance = mm(0.25)
    ds.m_HoleClearance = mm(0.15); ds.m_HoleToHoleMin = mm(0.25); ds.SetBoardThickness(mm(1.2))
    nc = ds.m_NetSettings.m_DefaultNetClass
    nc.SetClearance(mm(0.1)); nc.SetTrackWidth(mm(0.15)); nc.SetViaDiameter(mm(VIA_D)); nc.SetViaDrill(mm(VIA_DRILL))

    # outline with rounded corners
    def edge(shape, **kw):
        s = pcbnew.PCB_SHAPE(b); s.SetShape(shape); s.SetLayer(pcbnew.Edge_Cuts); s.SetWidth(mm(0.1))
        for k, v in kw.items(): getattr(s, k)(v)
        b.Add(s)
    x0, x1, y0, y1 = -W / 2, W / 2, -H / 2, H / 2
    for a, c in (((x0 + R, y1), (x1 - R, y1)), ((x1, y1 - R), (x1, y0 + R)), ((x1 - R, y0), (x0 + R, y0)), ((x0, y0 + R), (x0, y1 - R))):
        edge(pcbnew.SHAPE_T_SEGMENT, SetStart=P(*a), SetEnd=P(*c))
    for cx, cy, sx, sy, ex, ey in ((x0 + R, y1 - R, x0, y1 - R, x0 + R, y1), (x1 - R, y1 - R, x1 - R, y1, x1, y1 - R),
                                   (x1 - R, y0 + R, x1, y0 + R, x1 - R, y0), (x0 + R, y0 + R, x0 + R, y0, x0, y0 + R)):
        s = pcbnew.PCB_SHAPE(b); s.SetShape(pcbnew.SHAPE_T_ARC); s.SetLayer(pcbnew.Edge_Cuts); s.SetWidth(mm(0.1))
        s.SetCenter(P(cx, cy)); s.SetStart(P(sx, sy)); s.SetEnd(P(ex, ey)); b.Add(s)

    nets = {}
    def net(name):
        if name not in nets:
            n = pcbnew.NETINFO_ITEM(b, name); b.Add(n); nets[name] = n
        return nets[name]
    pin_net = {}
    for name, pins in NETS.items():
        for p in pins.split():
            assert p not in pin_net, p
            pin_net[p] = name
    # RK1828 ground balls from the pin table
    with open(os.path.join(HERE, "..", "lib", "rk182x_pins.csv")) as f:
        for ball, pname in list(csv.reader(f))[1:]:
            if (pname.startswith("VSS_") and pname != "VSS_SENSE_N") or pname.startswith("AVSS_"):
                pin_net["U1." + ball] = "GND"

    used = set()
    for ref, (lib, fpname, value, x, y, rot) in PARTS.items():
        fp = pcbnew.FootprintLoad(lib, fpname)
        assert fp is not None, (lib, fpname)
        fp.SetReference(ref); fp.SetValue(value); fp.SetPosition(P(x, y)); fp.SetOrientationDegrees(rot)
        if ref in ("U1", "LG1"): fp.Reference().SetVisible(False)
        for pad in fp.Pads():
            key = ref + "." + pad.GetNumber()
            if key in pin_net:
                pad.SetNet(net(pin_net[key])); used.add(key)
        b.Add(fp)
    missing = sorted(set(pin_net) - used)
    assert not missing, missing

    for name, layer, w, pts in TRACKS:
        for a, c in zip(pts, pts[1:]):
            t = pcbnew.PCB_TRACK(b); t.SetStart(P(*a)); t.SetEnd(P(*c)); t.SetWidth(mm(w))
            t.SetLayer(b.GetLayerID(layer)); t.SetNet(net(name)); b.Add(t)
    for name, x, y in VIAS:
        v = pcbnew.PCB_VIA(b); v.SetPosition(P(x, y)); v.SetWidth(mm(VIA_D)); v.SetDrill(mm(VIA_DRILL))
        v.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu); v.SetNet(net(name)); b.Add(v)

    for name, xa, xb, ya, yb in ZONES:
        z = pcbnew.ZONE(b); z.SetLayer(pcbnew.F_Cu); z.SetNet(net(name)); z.SetZoneName(name); z.SetAssignedPriority(1)
        o = z.Outline(); o.NewOutline()
        for x, y in ((xa, ya), (xb, ya), (xb, yb), (xa, yb)): o.Append(mm(OX + x), mm(OY - y))
        z.SetLocalClearance(mm(0.2)); z.SetMinThickness(mm(0.15)); z.SetPadConnection(pcbnew.ZONE_CONNECTION_FULL)
        b.Add(z)
    import autoroute
    autoroute.run(b, net, sys.modules[__name__])

    gold_traces(b)
    titles = (("USB DATA", -34.0, -9.2), ("RK1828", -12.0, -11.2), ("5V BUCK", 13.6, 5.2), ("LOAD SWITCH", 28.15, 3.4), ("USB PD", 27.0, -15.9), ("PWR IN", 38.0, 6.6), ("DATA", -38.0, 6.6))
    for txt, x, y in titles:
        t = pcbnew.PCB_TEXT(b); t.SetText(txt); t.SetLayer(pcbnew.F_SilkS); t.SetPosition(P(x, y))
        t.SetTextSize(pcbnew.VECTOR2I(mm(0.9), mm(0.9))); t.SetTextThickness(mm(0.15)); b.Add(t)
    tidy_silk(b, titles)
    r = pcbnew.PCB_SHAPE(b); r.SetShape(pcbnew.SHAPE_T_RECT); r.SetLayer(pcbnew.Dwgs_User); r.SetWidth(mm(0.15))
    r.SetStart(P(-1.0, 16.5)); r.SetEnd(P(6.6, -16.5)); b.Add(r)
    t = pcbnew.PCB_TEXT(b); t.SetText("reserved: RK1828 regulators"); t.SetLayer(pcbnew.Dwgs_User); t.SetPosition(P(2.9, 0)); t.SetTextAngleDegrees(90)
    t.SetTextSize(pcbnew.VECTOR2I(mm(1.2), mm(1.2))); t.SetTextThickness(mm(0.15)); b.Add(t)

    # ground planes on inner layers 1 and 4
    for layer in ("In1.Cu", "In4.Cu"):
        z = pcbnew.ZONE(b); z.SetLayer(b.GetLayerID(layer)); z.SetNet(net("GND")); z.SetZoneName("GND " + layer)
        o = z.Outline(); o.NewOutline()
        for x, y in ((x0, y0), (x1, y0), (x1, y1), (x0, y1)): o.Append(mm(OX + x), mm(OY - y))
        z.SetLocalClearance(mm(0.15)); z.SetMinThickness(mm(0.15)); z.SetPadConnection(pcbnew.ZONE_CONNECTION_FULL)
        b.Add(z)
    return b


SILK_H = 0.6


def tidy_silk(b, titles):
    """Put every reference designator next to its part where there is free room; hide it otherwise."""
    def box_of(bb_, grow=0.0):
        return (pcbnew.ToMM(bb_.GetLeft()) - grow, pcbnew.ToMM(bb_.GetRight()) + grow, pcbnew.ToMM(bb_.GetTop()) - grow, pcbnew.ToMM(bb_.GetBottom()) + grow)
    hit = lambda a, c: a[0] < c[1] and c[0] < a[1] and a[2] < c[3] and c[2] < a[3]
    fixed, court = [], {}
    for fp in b.GetFootprints():
        ref = fp.GetReference()
        xs, ys = [], []
        for pad in fp.Pads():
            bx = box_of(pad.GetBoundingBox(), 0.12); fixed.append(bx); xs += bx[:2]; ys += bx[2:]
        for g in fp.GraphicalItems():
            if g.GetLayer() in (pcbnew.F_CrtYd, pcbnew.F_Fab) and g.Type() == pcbnew.PCB_SHAPE_T:
                bx = box_of(g.GetBoundingBox()); xs += bx[:2]; ys += bx[2:]
        if not xs:
            bx = box_of(fp.GetBoundingBox(False, False)); xs, ys = list(bx[:2]), list(bx[2:])
        court[ref] = (min(xs), max(xs), min(ys), max(ys))
    for txt, x, y in titles:
        w = 0.9 * 0.95 * len(txt)
        fixed.append((OX + x - w / 2 - 0.2, OX + x + w / 2 + 0.2, OY - y - 0.65, OY - y + 0.65))
    edge = (OX - W / 2 + 0.6, OX + W / 2 - 0.6, OY - H / 2 + 0.6, OY + H / 2 - 0.6)
    placed, hidden = [], []
    for fp in sorted(b.GetFootprints(), key=lambda f: -(court[f.GetReference()][1] - court[f.GetReference()][0]) * (court[f.GetReference()][3] - court[f.GetReference()][2])):
        ref = fp.GetReference(); t = fp.Reference()
        if ref in ("LG1", "U1"): t.SetVisible(False); continue
        c = court[ref]; w = SILK_H * 0.95 * len(ref); h = SILK_H; g = 0.35
        cx_, cy_ = (c[0] + c[1]) / 2, (c[2] + c[3]) / 2
        cands = [(cx_, c[2] - g - h / 2), (cx_, c[3] + g + h / 2), (c[1] + g + w / 2, cy_), (c[0] - g - w / 2, cy_),
                 (c[1] + g + w / 2, c[2] + h / 2), (c[0] - g - w / 2, c[2] + h / 2), (c[1] + g + w / 2, c[3] - h / 2), (c[0] - g - w / 2, c[3] - h / 2)]
        for x, y in cands:
            bx = (x - w / 2 - 0.08, x + w / 2 + 0.08, y - h / 2 - 0.08, y + h / 2 + 0.08)
            if bx[0] < edge[0] or bx[1] > edge[1] or bx[2] < edge[2] or bx[3] > edge[3]: continue
            if any(hit(bx, f) for f in fixed) or any(hit(bx, f) for f in placed): continue
            if any(hit(bx, v) for k, v in court.items() if k != ref): continue
            t.SetPosition(pcbnew.VECTOR2I(mm(x), mm(y))); t.SetTextAngleDegrees(0); t.SetVisible(True); t.SetLayer(pcbnew.F_SilkS)
            t.SetTextSize(pcbnew.VECTOR2I(mm(SILK_H), mm(SILK_H))); t.SetTextThickness(mm(0.1)); t.SetKeepUpright(True)
            placed.append(bx); break
        else:
            t.SetVisible(False); hidden.append(ref)
    print("silkscreen: %d designators placed, hidden: %s" % (len(placed), " ".join(sorted(hidden)) or "none"))


GOLD_PAD_DISTANCE = 0.6     # solder mask stays closed this close to any pad, so solder cannot run along a bare track
GOLD_MIN_LENGTH = 0.8


def gold_traces(b):
    """Open the solder mask over outer-layer tracks so they are plated with the ENIG finish.
    The mask stays closed near pads; openings shorter than GOLD_MIN_LENGTH are dropped."""
    import numpy as np
    boxes = {pcbnew.F_Cu: [], pcbnew.B_Cu: []}
    for fp in b.GetFootprints():
        if fp.GetReference() == "LG1": continue
        for pad in fp.Pads():
            bb_ = pad.GetBoundingBox()
            box = (pcbnew.ToMM(bb_.GetLeft()), pcbnew.ToMM(bb_.GetRight()), pcbnew.ToMM(bb_.GetTop()), pcbnew.ToMM(bb_.GetBottom()))
            boxes[pcbnew.F_Cu].append(box)
            if pad.GetAttribute() in (pcbnew.PAD_ATTRIB_PTH, pcbnew.PAD_ATTRIB_NPTH): boxes[pcbnew.B_Cu].append(box)
    arr = {l: np.array(v) for l, v in boxes.items()}
    n_open = 0; length = 0.0
    for t in list(b.GetTracks()):
        if t.Type() != pcbnew.PCB_TRACE_T or t.GetLayer() not in arr: continue
        x1, y1, x2, y2 = (pcbnew.ToMM(v) for v in (t.GetStart().x, t.GetStart().y, t.GetEnd().x, t.GetEnd().y))
        L = ((x2 - x1) ** 2 + (y2 - y1) ** 2) ** 0.5
        if L < GOLD_MIN_LENGTH: continue
        k = int(L / 0.05) + 1
        ts = np.linspace(0, 1, k + 1)
        px = (x1 + ts * (x2 - x1))[:, None]; py = (y1 + ts * (y2 - y1))[:, None]
        a = arr[t.GetLayer()]
        dx = np.maximum(np.maximum(a[None, :, 0] - px, px - a[None, :, 1]), 0)
        dy = np.maximum(np.maximum(a[None, :, 2] - py, py - a[None, :, 3]), 0)
        ok = np.sqrt(dx * dx + dy * dy).min(axis=1) >= GOLD_PAD_DISTANCE + pcbnew.ToMM(t.GetWidth()) / 2
        i = 0
        while i <= k:
            if not ok[i]: i += 1; continue
            j = i
            while j + 1 <= k and ok[j + 1]: j += 1
            if (ts[j] - ts[i]) * L >= GOLD_MIN_LENGTH:
                s_ = pcbnew.PCB_SHAPE(b); s_.SetShape(pcbnew.SHAPE_T_SEGMENT)
                s_.SetLayer(pcbnew.F_Mask if t.GetLayer() == pcbnew.F_Cu else pcbnew.B_Mask)
                s_.SetStart(pcbnew.VECTOR2I(mm(float(x1 + ts[i] * (x2 - x1))), mm(float(y1 + ts[i] * (y2 - y1)))))
                s_.SetEnd(pcbnew.VECTOR2I(mm(float(x1 + ts[j] * (x2 - x1))), mm(float(y1 + ts[j] * (y2 - y1)))))
                s_.SetWidth(t.GetWidth() + mm(0.1)); b.Add(s_); n_open += 1; length += (ts[j] - ts[i]) * L
            i = j + 1
    print("gold tracks: %d mask openings, %.0f mm" % (n_open, length))


def dump(board, refs):
    for fp in board.GetFootprints():
        if fp.GetReference() in refs:
            for pad in fp.Pads():
                bb_ = pad.GetBoundingBox()
                print(fp.GetReference(), pad.GetNumber() or "-", pad.GetNetname(),
                      "x %.2f..%.2f y %.2f..%.2f" % (pcbnew.ToMM(bb_.GetLeft()) - OX, pcbnew.ToMM(bb_.GetRight()) - OX,
                                                     OY - pcbnew.ToMM(bb_.GetBottom()), OY - pcbnew.ToMM(bb_.GetTop())))


if __name__ == "__main__":
    out = os.path.join(HERE, "tokenstick.kicad_pcb")
    pcbnew.SaveBoard(out, build())
    board = pcbnew.LoadBoard(out)          # zones are filled on the reloaded board
    pcbnew.ZONE_FILLER(board).Fill(board.Zones())
    pcbnew.SaveBoard(out, board)
    # board finish: the Python API of KiCad 7 has no stackup access, so the block is written into the file
    text = open(out).read()
    assert "(stackup" not in text
    die = [("prepreg", 0.10), ("core", 0.33), ("prepreg", 0.11), ("core", 0.33), ("prepreg", 0.10)]   # placeholder, 1.2 mm total
    cu = ["F.Cu", "In1.Cu", "In2.Cu", "In3.Cu", "In4.Cu", "B.Cu"]
    L = ['    (stackup', '      (layer "F.SilkS" (type "Top Silk Screen") (color "White"))', '      (layer "F.Paste" (type "Top Solder Paste"))',
         '      (layer "F.Mask" (type "Top Solder Mask") (color "Black") (thickness 0.01))']
    for i, c in enumerate(cu):
        L.append('      (layer "%s" (type "copper") (thickness 0.035))' % c)
        if i < 5: L.append('      (layer "dielectric %d" (type "%s") (thickness %.2f) (material "FR4") (epsilon_r 4.5) (loss_tangent 0.02))' % (i + 1, *die[i]))
    L += ['      (layer "B.Mask" (type "Bottom Solder Mask") (color "Black") (thickness 0.01))', '      (layer "B.Paste" (type "Bottom Solder Paste"))',
          '      (layer "B.SilkS" (type "Bottom Silk Screen") (color "White"))', '      (copper_finish "ENIG")', '      (dielectric_constraints no)', '    )']
    i = text.index("(setup") + len("(setup")
    open(out, "w").write(text[:i] + "\n" + "\n".join(L) + text[i:])
    board = pcbnew.LoadBoard(out)           # make sure KiCad still reads it
    print("wrote", out, "footprints", len(board.GetFootprints()), "tracks+vias", len(board.GetTracks()))
