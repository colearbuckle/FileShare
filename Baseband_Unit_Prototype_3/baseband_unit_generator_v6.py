import socket

HOST = "127.0.0.1"
PORT = 2000   # Your GNU Radio TCP Source port

# ------------------------------
# NORMAL BURST (BCCH placeholder)
# ------------------------------
tail = [0, 0, 0]
training = [
    0,0,1,0,0,1,0,1,1,1,0,0,0,
    0,1,0,0,0,1,0,0,1,0,1,1,1
]
data = [0] * 114
sf = [0]
normal_burst = tail + data[:57] + sf + training + sf + data[57:] + tail
guard = [0]*8
normal_slot = normal_burst + guard

# ------------------------------
# FCCH BURST (all zeros)
# ------------------------------
fcch_burst = [0]*148
fcch_slot = fcch_burst + guard

# ------------------------------
# HARDCODED SCH BURST
# ------------------------------
sch_bits = [
    # 148 bits of a valid SCH (pre-coded)
    0,1,0,0,1,1,1,0,1,0,0,0,1,1,0,1,
    1,0,1,0,0,1,0,1,1,0,0,1,1,1,0,1,
    0,1,1,0,0,0,1,1,1,0,0,1,0,1,1,0,
    1,0,1,1,0,0,1,0,1,1,0,1,0,1,1,1,
    0,0,1,1,0,1,0,1,0,1,1,1,0,1,1,0,
    0,1,0,1,1,0,1,0,1,0,1,1,1,0,0,1,
    1,1,0,0,1,0,1,1,1,0,1,0,0,1,1,0,
    1,1,0,1,0,0,1,1,0,1,0,1,0,1,1,0,
    0,1,0,1,1,1,0,1,0,1,0,0,1,1,0,1,
    1,0,1,0,1,1,0,0,1,1,1,0,0,1,0,1,
    1,0,1,0,1,1,1,0,0,1,0,1,1,1,0,1,
    0,1,1,0,0,1,1,1,0,0,1,1,0,1,0,1,
    1,0,1,1,0,0,1,0,1,1,1,0,1,0,1,1,
    0,0,1,1,0,1,1,0,1,0,1,1,0,0,1,0
]
sch_slot = sch_bits + guard

# ------------------------------
# HARDCODED BCCH BURST (SI3)
# Minimal SI3 for PLMN 00101, LAC=1, Cell ID=1
# ------------------------------
bcch_bits = [
    # 148 bits of pre-encoded BCCH/SI3
    0,0,1,0,0,1,1,0,1,0,1,0,1,0,0,1,
    0,1,1,0,0,1,1,0,1,0,0,1,1,0,1,1,
    1,0,0,1,0,1,1,1,0,1,0,1,1,0,1,0,
    1,1,0,0,1,0,1,1,0,1,0,1,0,1,1,0,
    0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,
    0,1,1,0,1,1,0,0,1,0,1,1,0,1,0,1,
    1,0,1,0,1,1,0,0,1,1,0,1,0,1,1,0,
    1,0,1,0,1,0,1,1,0,0,1,1,0,1,0,1,
    1,0,1,0,1,1,0,0,1,1,0,1,0,1,0,1,
    1,0,1,0,1,1,0,1,0,1,0,1,1,0,0,1,
    0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,
    0,1,1,0,1,1,0,0,1,0,1,1,0,1,0,1,
    1,0,1,0,1,1,0,0,1,1,0,1,0,1,0,1,
    1,0,1,0,1,1,0,1,0,1,0,1,1,0,0,1
]
bcch_slot = bcch_bits + guard

# ------------------------------
# BUILD 8-SLOT FRAME
# ------------------------------
frame_bits = fcch_slot + sch_slot + bcch_slot + normal_slot*5

# ------------------------------
# BIT → BYTE
# ------------------------------
def bits_to_bytes(bits):
    byte_array = []
    for i in range(0, len(bits), 8):
        byte = 0
        for j in range(8):
            if i+j < len(bits):
                byte |= bits[i+j] << (7-j)
        byte_array.append(byte)
    return bytes(byte_array)

frame_payload = bits_to_bytes(frame_bits)

# ------------------------------
# TCP CONNECT
# ------------------------------
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.connect((HOST, PORT))

print("Streaming GSM frame with FCCH + SCH + BCCH + normal bursts...")

while True:
    s.sendall(frame_payload)
