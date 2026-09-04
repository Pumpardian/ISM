import sys, os, struct

USAGE_MESSAGE = f"Usage: {sys.argv[0]} mode:[simple|gamma|feedback|prefix] [input_filename] [output_filename] action:[encrypt|decrypt] (for simple/feedback only)"
SUBSTITUTION_TABLE = [
    [4,10,9,2,13,8,0,14,6,11,1,12,7,15,5,3],
    [14,11,4,12,6,13,15,10,2,3,8,1,0,7,5,9],
    [5,8,1,13,10,3,4,2,14,15,12,7,6,0,9,11],
    [7,13,10,1,0,8,9,15,14,4,6,12,11,2,5,3],
    [6,12,7,1,5,15,13,8,4,10,9,14,0,3,11,2],
    [4,11,10,0,7,2,1,13,3,6,8,5,9,12,15,14],
    [13,11,4,1,3,15,5,9,0,10,14,7,6,8,2,12],
    [1,15,13,0,5,7,10,4,9,2,3,14,6,11,8,12],
]
INITIALIZATION_VECTOR = [0x12345678, 0x9ABCDEF0]

def cycle_left(data):
    return ((data << 11) | (data >> 21)) & 0xFFFFFFFF

def substitute_block_part(block_part, key):
    sub = (block_part + key) & 0xFFFFFFFF
    for i in range (0, 8):
        s_in = (sub >> (4 * i)) & 0xF
        s_out = SUBSTITUTION_TABLE[i][s_in]
        sub = (sub & ~(0xF << (4 * i))) | (s_out << (4 * i))
    return cycle_left(sub)

def crypt_block(block, key, decrypt, rounds=32):
    L, R = block
    for i in range(rounds-1, -1, -1) if decrypt else range(0, rounds):
        k_i = key[i % 8] if i < 24 else key[7 - (i % 8)]
        new_R = substitute_block_part(L, k_i) ^ R
        L, R = new_R, L
    return [R, L]

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

def align(data, mode):
    alignment = (8 - (len(data) % 8)) % 8
    if alignment > 0:
        data += bytes([alignment] * alignment)
    elif mode in ("simple", "feedback"):
        data += bytes([8] * 8)
    return data

def remove_alignment(data):
    if not data:
        return data
    alignment_len = data[-1]
    if 0 < alignment_len <= 8:
        return data[:-alignment_len]
    return data

def process_simple(data, key, decrypt):
    processed_data = bytearray()
    for i in range(0, len(data), 8):
        processed_block = crypt_block(struct.unpack('2I', data[i:i + 8]), key, decrypt)
        processed_data.extend(struct.pack('2I', *processed_block))
    return processed_data

def process_gamma(data, key):
    processed_data = bytearray()
    gamma = crypt_block(INITIALIZATION_VECTOR, key, False)
    C1 = 0x01010101
    C2 = 0x01010104
    for i in range(0, len(data), 8):
        gamma_block = crypt_block(gamma, key, False)
        plain_block = struct.unpack('2I', data[i:i + 8])
        processed_block = [plain_block[0] ^ gamma_block[0], plain_block[1] ^ gamma_block[1]]
        processed_data.extend(struct.pack('2I', *processed_block))

        gamma[0] = (gamma[0] + C2) & 0xFFFFFFFF
        gamma[1] = (gamma[1] + C1)
        if gamma[1] > 0xFFFFFFFF:
            gamma[1] = (gamma[1] + 1) & 0xFFFFFFFF
    return processed_data

def process_feedback(data, key, decrypt):
    processed_data = bytearray()
    feedback = list(INITIALIZATION_VECTOR)
    for i in range(0, len(data), 8):
        gamma_block = crypt_block(feedback, key, False)
        plain_block = struct.unpack('2I', data[i:i + 8])
        processed_block = [plain_block[0] ^ gamma_block[0], plain_block[1] ^ gamma_block[1]]
        processed_data.extend(struct.pack('2I', *processed_block))
        feedback = list(plain_block) if decrypt else processed_block
    return processed_data

def process_prefix(data, key):
    register = [0, 0]
    for i in range(0, len(data), 8):
        plain_block = struct.unpack('2I', data[i:i + 8])
        register[0] ^= plain_block[0]
        register[1] ^= plain_block[1]
        register = crypt_block(register, key, False, 16)
    return struct.pack('2I', *register)[:4]

def main():
    key = [0x00001111, 0x22223333, 0x44445555, 0x66667777, 0x88889999, 0xAAAABBBB, 0xCCCCDDDD, 0xEEEEFFFF]

    if len(sys.argv) not in (4, 5):
        print("Invalid arguments")
        print(USAGE_MESSAGE)
        return
    mode = sys.argv[1].lower()
    input_file = sys.argv[2]
    output_file = sys.argv[3]
    action = sys.argv[4].lower() if len(sys.argv) == 5 else None
    
    if mode not in ("simple", "gamma", "feedback", "prefix"):
        print("Invalid mode")
        print(USAGE_MESSAGE)
        return
    if mode not in ("prefix","gamma") and action not in ("encrypt", "decrypt"):
        print("Invalid action")
        print(USAGE_MESSAGE)
        return
    elif mode in ("prefix","gamma") and action is not None:
        print(f"{mode} mode doesn't support actions")
        print(USAGE_MESSAGE)
        return
    if not os.path.isfile(input_file):
        print(f"File '{input_file}' not found")
        return

    decrypt = True if action == "decrypt" else False
    data = read_file(input_file)
    if not decrypt:
        data = align(data, mode)

    try:
        if mode == "simple":
            data = process_simple(data, key, decrypt)
        elif mode == "gamma":
            data = process_gamma(data, key)
        elif mode == "feedback":
            data = process_feedback(data, key, decrypt)
        elif mode == "prefix":
            data = process_prefix(data, key)
    except:
        print(f"Error while encrypting/decrypting data from file '{input_file}'. " \
               "In case of decrypting make sure you're decrypting correctly encrypted file")
        return

    if (decrypt and mode in ("simple", "feedback")) or mode == "gamma":
        data = remove_alignment(data)

    write_file(output_file, data)
    if mode == "prefix":
        print(f"Prefix for file {input_file} has been generated into {output_file}")
    else:
        print(f"File {input_file} has been processed into {output_file} using {mode} mode")   

if __name__ == "__main__":
    main()