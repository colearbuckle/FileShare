import socket

# ============================================================
# CONFIG
# ============================================================

HOST = "127.0.0.1"
PORT = 2000

GUARD_BITS = [0] * 8

# ============================================================
# CONVOLUTIONAL ENCODER (GSM SPEC)
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
# SCH (REAL FN AWARE)
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

    info = fn_bits + bsic_bits

    fire = fire_code(info)
    encoded = gsm_conv_encode(fire)

    tail = [0,0,0]

    burst = (
        tail +
        encoded[:39] +
        encoded[39:39+64] +
        tail
    )

    if len(burst) < 148:
        burst += [0]*(148-len(burst))

    return burst

# ============================================================
# MULTIFRAME BUILDER
# ============================================================

def build_frame(frame_number):

    if frame_number % 51 == 0:
        burst = build_fcch()
    elif frame_number % 51 == 1:
        burst = build_sch(frame_number)
    else:
        burst = build_normal()

    return burst + GUARD_BITS

def build_multiframe(start_fn):
    bits = []
    for i in range(51):
        bits += build_frame(start_fn + i)
    return bits

# ============================================================
# BIT PACKING
# ============================================================

def bits_to_bytes(bits):
    output = []
    for i in range(0, len(bits), 8):
        b = 0
        for j in range(8):
            if i+j < len(bits):
                b |= bits[i+j] << (7-j)
        output.append(b)
    return bytes(output)

# ============================================================
# MAIN LOOP
# ============================================================

def main():
    print("v12 running — REAL 51 MULTIFRAME ACTIVE")

    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((HOST, PORT))

    FN = 0

    while True:
        bits = build_multiframe(FN)
        payload = bits_to_bytes(bits)
        s.sendall(payload)
        FN += 51

if __name__ == "__main__":
    main()
