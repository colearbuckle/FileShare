import socket
import time

HOST = "127.0.0.1"
PORT = 2000   # your working port

# GSM Normal Burst Components

tail = [0,0,0]

training = [
0,0,1,0,0,1,0,1,1,1,0,0,0,
0,1,0,0,0,1,0,0,1,0,1,1,1
]

# 57 + 57 = 114 data bits (all zeros for now)
data = [0] * 114

# Stealing flags (0 for BCCH)
sf = [0]

burst_bits = (
    tail +
    data[:57] +
    sf +
    training +
    sf +
    data[57:] +
    tail
)

# Convert bit list to bytes
def bits_to_bytes(bits):
    byte_array = []
    for i in range(0, len(bits), 8):
        byte = 0
        for j in range(8):
            if i+j < len(bits):
                byte |= bits[i+j] << (7-j)
        byte_array.append(byte)
    return bytes(byte_array)

burst = bits_to_bytes(burst_bits)

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.connect((HOST, PORT))

while True:
    s.sendall(burst)
    time.sleep(0.01)
