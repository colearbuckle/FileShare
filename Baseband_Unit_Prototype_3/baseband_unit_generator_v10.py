import socket

# ============================================================
# CONFIGURATION
# ============================================================

HOST = "127.0.0.1"
PORT = 2000

SLOTS_PER_FRAME = 8

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
# GSM SPEC ACCURATE CONVOLUTIONAL ENCODER
# ============================================================

def gsm_conv_encode(bits):
    """
    GSM convolutional encoder
    Constraint length K = 5
    Generators = (0o133, 0o171)
    """

    G0 = 0o133
    G1 = 0o171

    shift_reg = [0] * 5
    encoded = []

    # Append 4 zero tail bits (K-1)
    bits = bits + [0, 0, 0, 0]

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
# BASIC BURST BUILDERS
# ============================================================

def build_fcch():
    return [0] * 148


def build_sch():
    """
    v10: ONLY testing convolutional encoder for now.
    Not yet spec-accurate SCH.
    """

    # Example 25-bit test pattern
    logical_bits = [0] * 25

    encoded = gsm_conv_encode(logical_bits)

    # Trim or pad to 148 bits for now
    burst = encoded[:148]
    if len(burst) < 148:
        burst += [0] * (148 - len(burst))

    return burst


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

    print("v10 running — GSM spec convolutional encoder active")

    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((HOST, PORT))

    while True:
        s.sendall(frame_payload)


if __name__ == "__main__":
    main()
