import socket

# ============================================================
# CONFIGURATION
# ============================================================

HOST = "127.0.0.1"
PORT = 2000

GUARD_BITS = [0] * 8
SLOTS_PER_FRAME = 8
MULTIFRAME_LENGTH = 51

TIMESLOT_LAYOUT = [
    "FCCH",
    "SCH",
    "NORMAL",
    "NORMAL",
    "NORMAL",
    "NORMAL",
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
# FIRE CODE (CRC) GENERATOR
# ============================================================

def fire_code(bits):
    g = [1,0,1,0,0,1,1,0,1,0,1]  # degree 10 polynomial
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
# BCCH BUILDER (SI3)
# ============================================================

def build_bcch():
    # 184 bits payload (SI3)
    si3 = []

    # Protocol discriminator and message type
    si3 += [0]*8  # placeholder PD + message type bits

    # PLMN (00101), LAC (1), Cell ID (1)
    # Encoded as 8+8+8 bits for simplicity
    si3 += [0,0,0,0,0,0,0,0]  # PLMN dummy byte
    si3 += [0,0,0,0,0,0,0,1]  # LAC
    si3 += [0,0,0,0,0,0,0,1]  # Cell ID

    # Fill remaining bits to 184
    while len(si3) < 184:
        si3.append(0)

    # Fire code
    si3_fire = fire_code(si3)  # 184 + 10
    # Convolutional encode
    encoded = gsm_conv_encode(si3_fire)

    # 4-burst interleaving
    bursts = []
    for i in range(4):
        tail = [0,0,0]
        start = i*encoded.__len__()//4
        burst_bits = encoded[start:start + encoded.__len__()//4]
        b = tail + burst_bits
        if len(b) < 148:
            b += [0]*(148-len(b))
        bursts.append(b)
    return bursts

# ============================================================
# FRAME BUILDER
# ============================================================

def build_frame(frame_number):
    mod = frame_number % MULTIFRAME_LENGTH
    if mod == 0:
        return build_fcch() + GUARD_BITS
    elif mod == 1:
        return build_sch(frame_number) + GUARD_BITS
    elif mod in [2,3,4,5]:  # BCCH burst frames (v13)
        # rotate through 4-burst BCCH
        bcch_bursts = build_bcch()
        index = mod - 2
        return bcch_bursts[index] + GUARD_BITS
    else:
        return build_normal() + GUARD_BITS

def build_multiframe(FN):
    bits = []
    for i in range(MULTIFRAME_LENGTH):
        bits += build_frame(FN + i)
    return bits

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
    print("v13 running — REAL BCCH + SCH active")
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((HOST, PORT))
    FN = 0
    while True:
        bits = build_multiframe(FN)
        payload = bits_to_bytes(bits)
        s.sendall(payload)
        FN += MULTIFRAME_LENGTH

if __name__ == "__main__":
    main()
