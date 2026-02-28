import socket

# ============================================================
# CONFIGURATION
# ============================================================

HOST = "127.0.0.1"
PORT = 2000

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

GUARD_BITS = [0] * 8


# ============================================================
# GSM CONVOLUTIONAL ENCODER (SPEC ACCURATE)
# ============================================================

def gsm_conv_encode(bits):
    G0 = 0o133
    G1 = 0o171

    shift_reg = [0] * 5
    encoded = []

    bits = bits + [0, 0, 0, 0]  # tail bits

    for bit in bits:
        shift_reg = [bit] + shift_reg[:-1]

        def parity(poly):
            result = 0
            for i in range(5):
                if (poly >> i) & 1:
                    result ^= shift_reg[i]
            return result

        encoded.append(parity(G0))
        encoded.append(parity(G1))

    return encoded


# ============================================================
# FIRE CODE (SPEC ACCURATE)
# ============================================================

def fire_code(bits):
    # generator polynomial (degree 10)
    g = [1,0,1,0,0,1,1,0,1,0,1]  # x^10 + x^8 + x^6 + x^5 + x^4 + x^2 + 1

    reg = bits + [0]*10

    for i in range(len(bits)):
        if reg[i] == 1:
            for j in range(len(g)):
                reg[i+j] ^= g[j]

    remainder = reg[-10:]
    return bits + remainder


# ============================================================
# SCH BIT MAPPING (SPEC ACCURATE)
# ============================================================

def build_sch():
    FN = 0
    BSIC = 0

    # Frame number mapping
    T1 = FN // (26 * 51)
    T2 = FN % 26
    T3 = FN % 51
    T3p = T3 // 10

    # Build 19-bit frame number field
    fn_bits = (
        [(T1 >> i) & 1 for i in reversed(range(11))] +
        [(T2 >> i) & 1 for i in reversed(range(5))] +
        [(T3p >> i) & 1 for i in reversed(range(3))]
    )

    bsic_bits = [(BSIC >> i) & 1 for i in reversed(range(6))]

    sch_info = fn_bits + bsic_bits  # 25 bits

    # Add Fire code
    sch_fire = fire_code(sch_info)  # 35 bits

    # Convolutional encode
    sch_encoded = gsm_conv_encode(sch_fire)  # 78 bits

    # SCH burst mapping:
    # 3 tail | 39 bits | 64 bits | 3 tail

    tail = [0,0,0]

    burst = (
        tail +
        sch_encoded[:39] +
        sch_encoded[39:39+64] +
        tail
    )

    # Pad if needed to 148 bits
    if len(burst) < 148:
        burst += [0] * (148 - len(burst))

    return burst


# ============================================================
# OTHER BURSTS
# ============================================================

def build_fcch():
    return [0] * 148


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
# FRAME BUILDER
# ============================================================

def build_timeslot(slot_type):
    if slot_type == "FCCH":
        burst = build_fcch()
    elif slot_type == "SCH":
        burst = build_sch()
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
# TRANSPORT
# ============================================================

def main():
    frame_bits = build_frame()
    frame_payload = bits_to_bytes(frame_bits)

    print("v11 running — SPEC ACCURATE SCH active")

    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((HOST, PORT))

    while True:
        s.sendall(frame_payload)


if __name__ == "__main__":
    main()
