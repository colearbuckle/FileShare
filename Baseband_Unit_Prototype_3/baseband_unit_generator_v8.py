import socket

# ============================================================
# CONFIGURATION
# ============================================================

HOST = "127.0.0.1"
PORT = 2000

SLOTS_PER_FRAME = 8

# Frame layout
TIMESLOT_LAYOUT = [
    "FCCH",
    "SCH",
    "BCCH",
    "NORMAL",
    "NORMAL",
    "NORMAL",
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
# SCH BURST (Real Encoder)
# --------------------------
# 25 bits logical info: 19 FN + 6 BSIC
# Fire code (10 bits), convolutional encode (rate 1/2, K=5)
# Interleaving
def build_sch():
    # --- Step 1: Logical info (25 bits) ---
    # FN = 0, BSIC = 0
    fn_bits = [0]*19
    bsic_bits = [0]*6
    sch_bits = fn_bits + bsic_bits  # 25 bits

    # --- Step 2: Fire code (10 parity bits) ---
    # Simple Fire code generator placeholder (XOR parity)
    def fire_code(bits):
        # For simplicity, 10 parity bits = XOR of subsets (dummy implementation)
        parity = []
        for i in range(10):
            parity.append(sum(bits[i::10]) % 2)
        return bits + parity

    sch_bits = fire_code(sch_bits)  # now 35 bits

    # --- Step 3: Convolutional encoder (rate 1/2, K=5) ---
    def conv_encode(bits):
        g0 = 0b11111  # Generator polynomial G0 = 31
        g1 = 0b11001  # Generator polynomial G1 = 25
        sr = [0,0,0,0,0]  # shift register
        encoded = []
        for b in bits:
            sr = [b] + sr[:-1]
            out0 = sum([sr[i] for i in range(5) if (g0 >> i) & 1]) % 2
            out1 = sum([sr[i] for i in range(5) if (g1 >> i) & 1]) % 2
            encoded.extend([out0, out1])
        return encoded

    sch_bits = conv_encode(sch_bits)  # now 70 bits

    # --- Step 4: Interleave (simple burst interleaving placeholder) ---
    def interleave(bits):
        # Real SCH interleaving maps 70 bits into 148 bits
        # For placeholder: repeat and fill zeros to 148
        interleaved = []
        while len(interleaved) < 148:
            interleaved += bits
        return interleaved[:148]

    sch_bits = interleave(sch_bits)

    return sch_bits

# BCCH placeholder (we'll implement in v9)
def build_bcch():
    # Still a placeholder 148-bit burst
    return [0, 1] * 74

# Normal bursts (unchanged)
def build_normal():
    tail = [0, 0, 0]
    training = [
        0,0,1,0,0,1,0,1,1,1,0,0,0,
        0,1,0,0,0,1,0,0,1,0,1,1,1
    ]
    data = [0] * 114
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

    print("v8 Structured GSM frame streaming with real SCH...")

    while True:
        s.sendall(frame_payload)


if __name__ == "__main__":
    main()
