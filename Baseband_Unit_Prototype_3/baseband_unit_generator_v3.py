import socket
import time

HOST = "127.0.0.1"
PORT = 2000   # Make sure this matches your GNU Radio TCP Source port

# ===============================
# GSM NORMAL BURST CONSTRUCTION
# ===============================

# Tail bits
tail = [0, 0, 0]

# 26-bit Training Sequence Code (TSC 0)
training = [
    0,0,1,0,0,1,0,1,1,1,0,0,0,
    0,1,0,0,0,1,0,0,1,0,1,1,1
]

# 114 data bits (all zeros for now)
data = [0] * 114

# Stealing flags (0 for BCCH-type burst)
sf = [0]

# Construct 148-bit normal burst
burst_bits = (
    tail +
    data[:57] +
    sf +
    training +
    sf +
    data[57:] +
    tail
)

# ===============================
# GSM GUARD PERIOD
# ===============================

# Approximate 8 symbol guard (close enough for now)
guard_bits = [0] * 8

# One full GSM timeslot (burst + guard)
timeslot_bits = burst_bits + guard_bits

# ===============================
# BIT → BYTE CONVERSION
# ===============================

def bits_to_bytes(bits):
    byte_array = []
    for i in range(0, len(bits), 8):
        byte = 0
        for j in range(8):
            if i + j < len(bits):
                byte |= bits[i + j] << (7 - j)
        byte_array.append(byte)
    return bytes(byte_array)

frame_payload = bits_to_bytes(timeslot_bits)

# ===============================
# TCP CONNECTION
# ===============================

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.connect((HOST, PORT))

print("Connected to GNU Radio. Streaming GSM timeslots...")

# Continuous transmission
while True:
    s.sendall(frame_payload)
