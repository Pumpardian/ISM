import os, sys, struct

USAGE_MESSAGE = f"Usage: {sys.argv[0]} mode:[encrypt|decrypt|gencrypt|gdecrypt] [input_file] [output_file]"
H = [
    0xB1, 0x94, 0xBA, 0xC8, 0x0A, 0x0B, 0xF5, 0x3B, 0x36, 0x6D, 0x00, 0xBE, 0x58, 0x4A, 0x5D, 0xE4,
    0xB5, 0x04, 0xFA, 0x9D, 0x1B, 0xB6, 0xC7, 0xAC, 0x25, 0x2E, 0x72, 0xC2, 0x02, 0xFD, 0xCE, 0x0D,
    0x5B, 0xE3, 0xD6, 0x12, 0x17, 0xB9, 0x61, 0x81, 0xFE, 0x67, 0x86, 0xAD, 0x71, 0x6B, 0x89, 0x0B,
    0x5C, 0xB0, 0xC0, 0xFF, 0x33, 0xC3, 0x56, 0xB8, 0x35, 0xC4, 0x05, 0xAE, 0xD8, 0xE0, 0x7F, 0x99,
    0xE1, 0x2B, 0xDC, 0x1A, 0xE2, 0x82, 0x57, 0xEC, 0x70, 0x3F, 0xCC, 0xF0, 0x95, 0xEE, 0x8D, 0xF1,
    0xC1, 0xAB, 0x76, 0x38, 0x9F, 0xE6, 0x78, 0xCA, 0xF7, 0xC6, 0xF8, 0x60, 0xD5, 0xBB, 0x9C, 0x4F,
    0xF3, 0x3C, 0x65, 0x7B, 0x63, 0x7C, 0x30, 0x6A, 0xDD, 0x4E, 0xA7, 0x79, 0x9E, 0xB2, 0x3D, 0x31,
    0x3E, 0x98, 0xB5, 0x6E, 0x27, 0xD3, 0xBC, 0xCF, 0x59, 0x1E, 0x18, 0x1F, 0x4C, 0x5A, 0xB7, 0x93,
    0xE9, 0xDE, 0xE7, 0x2C, 0x8F, 0x0C, 0x0F, 0xA6, 0x2D, 0xDB, 0x49, 0xF4, 0x6F, 0x73, 0x96, 0x47,
    0x06, 0x07, 0x53, 0x16, 0xED, 0x24, 0x7A, 0x37, 0x39, 0xCB, 0xA3, 0x83, 0x03, 0xA9, 0x8B, 0xF6,
    0x92, 0xBD, 0x9B, 0x1C, 0xE5, 0xD1, 0x41, 0x01, 0x54, 0x45, 0xFB, 0xC9, 0x5E, 0x4D, 0x0E, 0xF2,
    0x68, 0x20, 0x80, 0xAA, 0x22, 0x7D, 0x64, 0x2F, 0x26, 0x87, 0xF9, 0x34, 0x90, 0x40, 0x55, 0x11,
    0xBE, 0x32, 0x97, 0x13, 0x43, 0xFC, 0x9A, 0x48, 0xA0, 0x2A, 0x88, 0x5F, 0x19, 0x4B, 0x09, 0xA1,
    0x7E, 0xCD, 0xA4, 0xD0, 0x15, 0x44, 0xAF, 0x8C, 0xA5, 0x84, 0x50, 0xBF, 0x66, 0xD2, 0xE8, 0x8A,
    0xA2, 0xD7, 0x46, 0x52, 0x42, 0xA8, 0xDF, 0xB3, 0x69, 0x74, 0xC5, 0x51, 0xEB, 0x23, 0x29, 0x21,
    0xD4, 0xEF, 0xD9, 0xB4, 0x3A, 0x62, 0x28, 0x75, 0x91, 0x14, 0x10, 0xEA, 0x77, 0x6C, 0xDA, 0x1D
]
INITIALIZATION_VECTOR = [0x11223344, 0x55667788, 0x99AABBCC, 0xDDEEFF00]

def int_to_byte_list(value):
    return [(value >> i) & 0xFF for i in [0, 8, 16, 24]]

def byte_list_to_int(bytes):
    return (bytes[0] << 0) | (bytes[1] << 8) | (bytes[2] << 16) | (bytes[3] << 24)

def to_blocks(data):
    return [data[i:i+16] for i in range(0, len(data), 16)]

def block_to_ints(block):
    return [byte_list_to_int(block[j * 4: j * 4 + 4]) for j in range(4)]

def ints_to_block(ints):
    return b''.join(bytes(int_to_byte_list(i)) for i in ints)

def rothi(data, r):
    return ((data << r) | (data >> (32 - r))) & 0xFFFFFFFF

def sum_mod(*values):
    sum = 0
    for value in values:
        sum = (sum + value) % 2**32
    return sum

def sub_mod(value1, value2):
    return (value1 - value2) % 2**32

def G(value, r):
    bytes = [H[b] for b in int_to_byte_list(value)]
    new_value = byte_list_to_int(bytes)
    return rothi(new_value, r)

def write_file(filename, data):
    try:
        with open(filename, 'wb') as file:
            file.write(data)
    except:
        print("Failed to write to file")

def read_file(filename):
    try:
        with open(filename, 'rb') as file:
            return file.read()
    except:
        print(f"Failed to read from file '{filename}'")

def align(data):
    alignment = (16 - (len(data) % 16)) % 16
    return data + bytes([alignment] * alignment)

def remove_alignment(data):
    if not data:
        return data
    alignment_len = data[-1]
    if 0 < alignment_len <= 16:
        return data[:-alignment_len]
    return data

def encrypt(block, key):
    a, b, c, d = block
    for i in range(1, 9):
        b = b ^ G(sum_mod(a, key[7*i - 7]), 5)
        c = c ^ G(sum_mod(d, key[7*i - 6]), 21)
        a = sub_mod(a, G(sum_mod(b, key[7*i - 5]), 13))
        e = G(sum_mod(b, c, key[7*i - 4]), 21) ^ i
        b = sum_mod(b, e)
        c = sub_mod(c, e)
        d = sum_mod(d, G(sum_mod(c, key[7*i - 3]), 13))
        b = b ^ G(sum_mod(a, key[7*i - 2]), 21)
        c = c ^ G(sum_mod(d, key[7*i - 1]), 5)
        a, b = b, a
        c, d = d, c
        b, c = c, b
    a = int_to_byte_list(a)
    b = int_to_byte_list(b)
    c = int_to_byte_list(c)
    d = int_to_byte_list(d)
    return b + d + a + c

def decrypt(block, key):
    a, b, c, d = block
    for i in range(8, 0, -1):
        b = b ^ G(sum_mod(a, key[7*i - 1]), 5)
        c = c ^ G(sum_mod(d, key[7*i - 2]), 21)
        a = sub_mod(a, G(sum_mod(b, key[7*i - 3]), 13))
        e = G(sum_mod(b, c, key[7*i - 4]), 21) ^ i
        b = sum_mod(b, e)
        c = sub_mod(c, e)
        d = sum_mod(d, G(sum_mod(c, key[7*i - 5]), 13))
        b = b ^ G(sum_mod(a, key[7*i - 6]), 21)
        c = c ^ G(sum_mod(d, key[7*i - 7]), 5)
        a, b = b, a
        c, d = d, c
        a, d = d, a
    a = int_to_byte_list(a)
    b = int_to_byte_list(b)
    c = int_to_byte_list(c)
    d = int_to_byte_list(d)
    return c + a + d + b

def encrypt_gamma(blocks, key):
    processed = bytearray()
    prev_block = INITIALIZATION_VECTOR
    for block in blocks:
        enc_prev_block = encrypt(prev_block, key)
        enc_prev_block_ints = block_to_ints(bytes(enc_prev_block))
        block_ints = block_to_ints(block)
        processed_block = [a ^ b for a,b in zip(block_ints, enc_prev_block_ints)]
        processed.extend(ints_to_block(processed_block))
        prev_block = processed_block
    return processed

def decrypt_gamma(blocks, key):
    processed = bytearray()
    prev_block = INITIALIZATION_VECTOR
    for block in blocks:
        enc_prev_block = encrypt(prev_block, key)
        enc_prev_block_ints = block_to_ints(bytes(enc_prev_block))
        unprocessed_block_ints = block_to_ints(block)
        block_ints = [a ^ b for a,b in zip(unprocessed_block_ints, enc_prev_block_ints)]
        processed.extend(ints_to_block(block_ints))
        prev_block = unprocessed_block_ints
    return processed

def main():
    key = [0x00001111, 0x22223333, 0x44445555, 0x66667777, 0x88889999, 0xAAAABBBB, 0xCCCCDDDD, 0xEEEEFFFF]
    key = [key[i % 8] for i in range(56)]

    if len(sys.argv) != 4:
        print(USAGE_MESSAGE)
        return
    
    mode = sys.argv[1]
    input_file = sys.argv[2]
    output_file = sys.argv[3]

    if mode not in ("encrypt", "decrypt", "gencrypt", "gdecrypt"):
        print("Invalid mode")
        print(USAGE_MESSAGE)
        return
    if not os.path.isfile(input_file):
        print(f"File '{input_file}' not found")
        return

    data = read_file(input_file)
    data = align(data)
    blocks = to_blocks(data)

    processed = bytearray()
    try:
        if mode == "encrypt":
            for block in blocks:
                block_ints = block_to_ints(block)
                processed_block = encrypt(block_ints, key)
                processed.extend(processed_block)
        elif mode == "decrypt":
            for block in blocks:
                block_ints = block_to_ints(block)
                processed_block = decrypt(block_ints, key)
                processed.extend(processed_block)
        elif mode == "gencrypt":
            processed = encrypt_gamma(blocks, key)
        elif mode == "gdecrypt":
            processed = decrypt_gamma(blocks, key)
    except:
        print(f"Error while encrypting/decrypting data from file '{input_file}'. " \
               "In case of decrypting make sure you're decrypting correctly encrypted file")
        return

    if mode in ("decrypt", "gdecrypt"):
        processed = remove_alignment(processed)

    write_file(output_file, processed)
    print(f"File {input_file} has been processed into {output_file} using {mode} mode")

if __name__ == "__main__":
    main()