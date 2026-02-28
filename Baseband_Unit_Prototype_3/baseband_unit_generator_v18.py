import os
import time

# ============================================================
# CONFIGURATION
# ============================================================

ACTIVE_FILE = "gsmbits_active.bin"
TEMP_FILE = "gsmbits_next.bin"

GUARD_BITS = [0] * 8
MULTIFRAME_LENGTH = 51
REPEAT_MULTIFRAMES = 256   # ~60 seconds
REGEN_INTERVAL = 50        # seconds (must be < playback time)

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
# BURSTS
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

    burst = [0,0,0] + encoded
    if len(burst) < 148:
        burst += [0]*(148-len(burst))

    return burst[:148]

def build_bcch():
    bits = [0]*184
    fire = fire_code(bits)
    encoded = gsm_conv_encode(fire)

    burst = [0,0,0] + encoded
    if len(burst) < 148:
        burst += [0]*(148-len(burst))

    return burst[:148]

# ============================================================
# FRAME / MULTIFRAME
# ============================================================

def build_frame(frame_number):
    mod = frame_number % MULTIFRAME_LENGTH

    if mod == 0:
        return build_fcch() + GUARD_BITS
    elif mod == 1:
        return build_sch(frame_number) + GUARD_BITS
    elif mod in [2,3,4,5]:
        return build_bcch() + GUARD_BITS
    else:
        return build_normal() + GUARD_BITS

def build_multiframe(FN):
    bits = []
    for i in range(MULTIFRAME_LENGTH):
        bits += build_frame(FN+i)
    return bits

def build_repeating_multiframes(FN):
    bits = []
    for _ in range(REPEAT_MULTIFRAMES):
        bits += build_multiframe(FN)
    return bits

# ============================================================
# FILE WRITER (NO PACKING)
# ============================================================

def write_active_file(bits):
    # Convert each bit to a byte (0x00 or 0x01)
    byte_data = bytes(bits)

    with open(TEMP_FILE, "wb") as f:
        f.write(byte_data)

    os.replace(TEMP_FILE, ACTIVE_FILE)

# ============================================================
# MAIN LOOP
# ============================================================

def main():
    print("v18 running — unpack-free GSM generator")
    FN = 0

    bits = build_repeating_multiframes(FN)
    write_active_file(bits)
    print("Initial file written.")

    while True:
        time.sleep(REGEN_INTERVAL)

        FN += MULTIFRAME_LENGTH * REPEAT_MULTIFRAMES

        bits = build_repeating_multiframes(FN)
        write_active_file(bits)

        print("File updated.")

if __name__ == "__main__":
    main()
