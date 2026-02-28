import socket

HOST = "127.0.0.1"
PORT = 2000

# ===============================
# NORMAL BURST
# ===============================

tail = [0, 0, 0]

training = [
    0,0,1,0,0,1,0,1,1,1,0,0,0,
    0,1,0,0,0,1,0,0,1,0,1,1,1
]

data = [0] * 114
sf = [0]

normal_burst = (
    tail +
    data[:57] +
    sf +
    training +
    sf +
    data[57:] +
    tail
)

# ===============================
# FCCH BURST (all zeros)
# ===============================

fcch_burst = [0] * 148

# Guard period
guard = [0] * 8

normal_slot = normal_burst + guard
fcch_slot = fcch_burst + guard

# ===============================
# BUILD SIMPLE 8-SLOT FRAME
# ===============================

frame_bits = (
    fcch_slot +
    normal_slot +
    normal_slot +
    normal_slot +
    normal_slot +
    normal_slot +
    normal_slot +
    normal_slot
)

# ===============================
# BIT → BYTE
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

frame_payload = bits_to_bytes(frame_bits)

# ===============================
# TCP CONNECT
# ===============================

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.connect((HOST, PORT))

print("Streaming frame with FCCH...")

while True:
    s.sendall(frame_payload)
