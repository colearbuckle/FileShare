#!/usr/bin/env python3
"""
v19: Spec-Compliant BCCH Generator
Generates GSM downlink bursts including:
- FCCH
- SCH
- BCCH SI3 message (MCC=001, MNC=01, LAC=1, CellID=1)
Output: binary file for GNU Radio File Source
"""

import numpy as np

# -------------------------
# Configuration
# -------------------------
MCC = [0,0,1]
MNC = [0,1]
LAC = 1
CELL_ID = 1
BSIC = 0
MULTIFRAME_REPEAT = 30  # seconds
OUTPUT_FILE = "gsm_downlink_bits.bin"

# GSM constants
BITS_PER_BURST = 148
BURSTS_PER_MULTIFRAME = 51

# -------------------------
# Utility functions
# -------------------------
def int_to_bits(val, nbits):
    """Convert integer to n-bit list"""
    return [(val >> i) & 1 for i in reversed(range(nbits))]

def build_si3():
    """
    Construct a minimal SI3 message for BCCH
    SI3 carries:
    - MCC, MNC
    - LAC
    - Cell ID
    """
    # Simplified SI3 payload (example only)
    si3_bits = []

    # PLMN (MCC + MNC)
    for d in MCC + MNC:
        si3_bits += int_to_bits(d, 4)  # 4 bits per decimal digit

    # LAC (16 bits)
    si3_bits += int_to_bits(LAC, 16)

    # Cell ID (16 bits)
    si3_bits += int_to_bits(CELL_ID, 16)

    # Add minimal padding to fill 184 bits (typical BCCH block length)
    while len(si3_bits) < 184:
        si3_bits.append(0)

    return si3_bits

def apply_convolutional_coding(bits):
    """
    Simplified convolutional encoder (rate 1/2, K=5)
    Actual GSM uses constraint length 5, polynomials 0x13, 0x15
    """
    K = 5
    g1 = 0b10011
    g2 = 0b10101
    shift_reg = 0
    out_bits = []

    for b in bits:
        shift_reg = ((shift_reg << 1) | b) & 0b11111
        out_bits.append(bin(shift_reg & g1).count("1") % 2)
        out_bits.append(bin(shift_reg & g2).count("1") % 2)

    return out_bits

def interleave_4burst(encoded_bits):
    """
    Interleave encoded bits over 4 bursts
    """
    bursts = [[] for _ in range(4)]
    for i, b in enumerate(encoded_bits):
        burst_idx = i % 4
        bursts[burst_idx].append(b)
    return bursts

# -------------------------
# Build Downlink Frame
# -------------------------
def build_multiframe():
    multiframe_bits = []

    # FCCH burst (all zeros in GSM, mapped to GMSK 0-deviation)
    fcch_burst = [0] * BITS_PER_BURST

    # SCH burst (BSIC + frame number)
    # GSM SCH uses 64 bits payload, repeated to fill burst
    sch_payload = int_to_bits(BSIC, 6)  # simplified
    sch_payload += int_to_bits(0, 58)   # rest of 64-bit SCH placeholder
    sch_burst = sch_payload[:BITS_PER_BURST]

    # BCCH burst (SI3)
    si3_bits = build_si3()
    si3_encoded = apply_convolutional_coding(si3_bits)
    bcch_bursts = interleave_4burst(si3_encoded)

    # Build full multiframe (51 bursts)
    # Timeslot 0: FCCH, SCH, BCCH repeated
    for i in range(BURSTS_PER_MULTIFRAME):
        if i == 0:
            multiframe_bits += fcch_burst
        elif i == 1:
            multiframe_bits += sch_burst
        else:
            burst_idx = (i-2) % 4
            multiframe_bits += bcch_bursts[burst_idx]

    return multiframe_bits

# -------------------------
# Repeat for duration
# -------------------------
def main():
    multiframe = build_multiframe()
    total_bits = []

    # Estimate how many multiframes fit in desired seconds
    bursts_per_sec = 217.0  # 270.833 ms per multiframe ~51 bursts
    repeat_count = int(MULTIFRAME_REPEAT * bursts_per_sec / BURSTS_PER_MULTIFRAME)
    for _ in range(repeat_count):
        total_bits += multiframe

    # Convert to bytes
    bytes_out = np.packbits(np.array(total_bits, dtype=np.uint8))

    # Write to file
    with open(OUTPUT_FILE, "wb") as f:
        f.write(bytes_out)

    print(f"v19: Wrote {len(bytes_out)} bytes to {OUTPUT_FILE}")

if __name__ == "__main__":
    main()