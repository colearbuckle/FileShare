import socket

# ============================================================
# CONFIGURATION
# ============================================================

HOST = "127.0.0.1"
PORT = 2000

GUARD_BITS = [0] * 8
SLOTS_PER_FRAME = 8
MULTIFRAME_LENGTH = 51
REPEAT_MULTIFRAMES = 20  # pre-generate this many for continuous streaming

# Timeslot layout for one frame
TIMESLOT_LAYOUT = [
    "FCCH",
    "SCH",
    "BCCH_0",  # BCCH bursts (4-burst sequence)
    "BCCH_1",
    "BCCH_2",
    "BCCH_3",
    "NORMAL",
    "NORMAL"
]

# ============================================================
# CONVOLUTIONAL ENCODER
# ============================================================

def gsm_conv_encode(bits):
    G0 = 0o133
    G1 = 0o171
    shift = [0]*5
    encoded = []
    bits = bits + [0,0,0,0]
    for bit in bits:
        shift = [bit] + shift[:-1]
        def parity(poly):
            p = 0
            for i in range(5):
                if (poly >> i) & 1:
                    p ^= shift[i]
            return p
        encoded.append(parity(G0))
        encoded.append(parity(G1))
    return encoded

# ============================================================
# FIRE CODE
# ============================================================

def fire_code(bits):
    g = [1,0,1,0,0,1,1,0,1,0,1]
    reg = bits + [0]*10
    for i in range(len(bits)):
        if reg[i] == 1:
            for j in range(len(g)):
                reg[i+j] ^= g[j]
    return bits + reg[-10:]

# ============================================================
# BURST BUILDERS
# ============================================================

def build_fcch():
    return [0]*148

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
# SCH BUILDER
# ============================================================

def build_sch(FN, BSIC=0):
    T1 = FN // (26 * 51)
    T2 = FN % 26
    T3 = FN % 51
    T3p = T3 // 10

    fn_bits = (
        [(T1 >> i) & 1 for i in reversed(range(11))] +
        [(T2 >> i) & 1 for i in reversed(range(5))] +
        [(T3p >> i) & 1 for i in reversed(range(3))]
    )

    bsic_bits = [(BSIC >> i) & 1 for i in reversed(range(6))]

    info = fn_bits + bsic_bits  # 25 bits
    fire = fire_code(info)      # 35 bits
    encoded = gsm_conv_encode(fire)  # 78 bits

    tail = [0,0,0]
    burst = tail + encoded[:39] + encoded[39:39+64] + tail
    if len(burst) < 148:
        burst += [0]*(148 - len(burst))
    return burst

# ============================================================
# BCCH BUILDER (FULL SI3 SPEC)
# ============================================================

def build_bcch_burst(burst_index):
    """
    Build 1 of the 4 BCCH bursts for interleaving.
    burst_index: 0..3
    """

    # ---- SI3 payload (realistic) ----
    si3_bits = []

    # Protocol discriminator (3 bits) + message type (5 bits)
    si3_bits += [0,0,0, 0,0,0,0,1]  # example values

    # PLMN: 00101 (encoded in 8 bits for simplicity)
    si3_bits += [0,0,0,0,0,0,1,0,1]

    # LAC: 1, Cell ID: 1 (each 8 bits)
    si3_bits += [0,0,0,0,0,0,0,1]  # LAC
    si3_bits += [0,0,0,0,0,0,0,1]  # Cell ID

    # Pad to 184 bits
    while len(si3_bits) < 184:
        si3_bits.append(0)

    # Fire code
    fire_bits = fire_code(si3_bits)

    # Convolutional encoding
    encoded = gsm_conv_encode(fire_bits)

    # Interleaving: split 4 bursts
    n = len(encoded) // 4
    tail = [0,0,0]
    burst_bits = encoded[burst_index*n : (burst_index+1)*n]
    burst = tail + burst_bits
    if len(burst) < 148:
        burst += [0]*(148-len(burst))
    return burst

# ============================================================
# FRAME BUILDER
# ============================================================

def build_frame(frame_number):
    mod = frame_number % MULTIFRAME_LENGTH
    if mod == 0:
        return build_fcch() + GUARD_BITS
    elif mod == 1:
        return build_sch(frame_number) + GUARD_BITS
    elif mod in [2,3,4,5]:  # BCCH bursts
        return build_bcch_burst(mod-2) + GUARD_BITS
    else:
        return build_normal() + GUARD_BITS

def build_multiframe(FN):
    mf_bits = []
    for i in range(MULTIFRAME_LENGTH):
        mf_bits += build_frame(FN+i)
    return mf_bits

def build_repeating_multiframes(FN, repeat=REPEAT_MULTIFRAMES):
    buffer = []
    for _ in range(repeat):
        buffer += build_multiframe(FN)
    return buffer

# ============================================================
# BIT PACKING
# ============================================================

def bits_to_bytes(bits):
    out = []
    for i in range(0,len(bits),8):
        b=0
        for j in range(8):
            if i+j < len(bits):
                b |= bits[i+j] << (7-j)
        out.append(b)
    return bytes(out)

# ============================================================
# MAIN LOOP
# ============================================================

def main():
    print("v14 running — FULL SPEC BCCH + SCH, repeating multiframes")
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((HOST, PORT))

    FN = 0

    while True:
        bits = build_repeating_multiframes(FN, REPEAT_MULTIFRAMES)
        payload = bits_to_bytes(bits)
        s.sendall(payload)
        FN += MULTIFRAME_LENGTH * REPEAT_MULTIFRAMES

if __name__ == "__main__":
    main()
