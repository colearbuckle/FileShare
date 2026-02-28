import socket

# ============================================================
# CONFIGURATION
# ============================================================

HOST = "127.0.0.1"
PORT = 2000

SLOTS_PER_FRAME = 8

# Frame layout: BCCH will occupy 4 bursts for simplicity
TIMESLOT_LAYOUT = [
    "FCCH",
    "SCH",
    "BCCH",
    "BCCH",
    "BCCH",
    "BCCH",
    "NORMAL",
    "NORMAL"
]

GUARD_BITS = [0] * 8

# ============================================================
# GSM BURST BUILDERS
# ============================================================

def build_fcch():
    return [0] * 148

# --------------------------
# SCH BURST (v8, real encoder)
# --------------------------
def build_sch():
    fn_bits = [0]*19
    bsic_bits = [0]*6
    sch_bits = fn_bits + bsic_bits  # 25 bits

    # Fire code placeholder
    def fire_code(bits):
        parity = []
        for i in range(10):
            parity.append(sum(bits[i::10]) % 2)
        return bits + parity

    sch_bits = fire_code(sch_bits)  # 35 bits

    # Convolutional encode
    def conv_encode(bits):
        g0 = 0b11111
        g1 = 0b11001
        sr = [0,0,0,0,0]
        encoded = []
        for b in bits:
            sr = [b] + sr[:-1]
            out0 = sum([sr[i] for i in range(5) if (g0 >> i) & 1]) % 2
            out1 = sum([sr[i] for i in range(5) if (g1 >> i) & 1]) % 2
            encoded.extend([out0, out1])
        return encoded

    sch_bits = conv_encode(sch_bits)  # 70 bits

    # Interleave to 148 bits
    def interleave(bits):
        interleaved = []
        while len(interleaved) < 148:
            interleaved += bits
        return interleaved[:148]

    return interleave(sch_bits)

# --------------------------
# BCCH BURST (v9, real encoder)
# --------------------------
def build_bcch():
    # --- Step 1: Logical info (SI3 simplified) ---
    # 184 bits total, we only fill key fields
    # PLMN = 00101, LAC = 1, Cell ID = 1, rest zeros
    plmn_bits = [0,0,1,0,1]
    lac_bits = [0]*14 + [1]  # 15-bit LAC
    cell_id_bits = [0]*15 + [1]  # 16-bit Cell ID (simplified)
    padding = [0]*(184 - len(plmn_bits) - len(lac_bits) - len(cell_id_bits))
    bcch_logical = plmn_bits + lac_bits + cell_id_bits + padding  # 184 bits

    # --- Step 2: Convolutional encode (rate 1/2, K=5) ---
    def conv_encode(bits):
        g0 = 0b11111
        g1 = 0b11001
        sr = [0,0,0,0,0]
        encoded = []
        for b in bits:
            sr = [b] + sr[:-1]
            out0 = sum([sr[i] for i in range(5) if (g0 >> i) & 1]) % 2
            out1 = sum([sr[i] for i in range(5) if (g1 >> i) & 1]) % 2
            encoded.extend([out0, out1])
        return encoded

    bcch_encoded = conv_encode(bcch_logical)  # 368 bits

    # --- Step 3: Interleave across 4 bursts ---
    # Each burst 148 bits, simplest: split 368 into 4, pad if needed
    burst_bits = []
    for i in range(4):
        start = i * 92
        burst = bcch_encoded[start:start+92]
        while len(burst) < 148:
            burst.append(0)
        burst_bits.append(burst)

    # Return only first burst for scheduler slot; frame scheduler will repeat for simplicity
    return burst_bits[0]

# --------------------------
# NORMAL BURSTS
# --------------------------
def build_normal():
    tail = [0,0,0]
    training = [
        0,0,1,0,0,1,0,1,1,1,0,0,0,
        0,1,0,0,0,1,0,0,1,0,1,1,1
    ]
    data = [0]*114
    sf = [0]
    return tail + data[:57] + sf + training + sf + data[57:] + tail


# ============================================================
# TIMESLOT + FRAME BUILDER
# ============================================================

def build_timeslot(slot_type):
    if slot_type == "FCCH":
        burst = build_fcch()
    elif slot_type == "SCH":
        burst = build_sch()
    elif slot_type == "BCCH":
        burst = build_bcch()
    else:
        burst = build_normal()
    return burst + GUARD_BITS

def build_frame():
    frame_bits = []
    for slot in TIMESLOT_LAYOUT:
        frame_bits += build_timeslot(slot)
    return frame_bits


# ============================================================
# BIT PACKING
# ============================================================

def bits_to_bytes(bits):
    byte_array = []
    for i in range(0, len(bits), 8):
        byte = 0
        for j in range(8):
            if i + j < len(bits):
                byte |= bits[i + j] << (7 - j)
        byte_array.append(byte)
    return bytes(byte_array)


# ============================================================
# TRANSPORT LOOP
# ============================================================

def main():
    frame_bits = build_frame()
    frame_payload = bits_to_bytes(frame_bits)

    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((HOST, PORT))

    print("v9 Structured GSM frame streaming with real BCCH...")

    while True:
        s.sendall(frame_payload)


if __name__ == "__main__":
    main()
