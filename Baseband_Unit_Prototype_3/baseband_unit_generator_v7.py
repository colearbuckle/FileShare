import socket

# ============================================================
# CONFIGURATION
# ============================================================

HOST = "127.0.0.1"
PORT = 2000

SLOTS_PER_FRAME = 8

# Simple frame layout for now (will become 51-multiframe later)
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
# GSM BURST BUILDERS (PHY PLACEHOLDERS FOR NOW)
# ============================================================

def build_fcch():
    return [0] * 148


def build_sch():
    # Placeholder until real SCH coding implemented
    return [1, 0] * 74


def build_bcch():
    # Placeholder until real BCCH coding implemented
    return [0, 1] * 74


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

    print("v7 Structured GSM frame streaming...")

    while True:
        s.sendall(frame_payload)


if __name__ == "__main__":
    main()
