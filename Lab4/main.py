import os, sys, numpy as np

USAGE_MESSAGE = f"Usage: {sys.argv[0]} [input_file] [output_file_encrypted] [output_file_decrypted]"

G = np.array([[1, 0, 0, 0, 1, 1, 0],
              [0, 1, 0, 0, 1, 0, 1],
              [0, 0, 1, 0, 0, 1, 1],
              [0, 0, 0, 1, 1, 1, 1]], dtype=int)

H = np.array([[1, 1, 0, 1, 1, 0, 0],
              [1, 0, 1, 1, 0, 1, 0],
              [0, 1, 1, 1, 0, 0, 1]], dtype=int)

rng = np.random.default_rng()

def generate_S(k):
    while True:
        S = rng.integers(0, 2, size=(k, k), dtype=int)
        if int(np.round(np.linalg.det(S))) % 2 != 0:
            return S

def generate_P(n):
    I_n = np.eye(n)
    P = rng.permutation(I_n)
    return P.astype(int)

def calculate_G1(S, G, P):
    G1 = (S @ G @ P) % 2
    return G1

def generate_z(n, t):
    ones_count = np.random.randint(0, t + 1)
    z = np.zeros(n, dtype=int)
    if ones_count > 0:
        ones_indicies = rng.choice(n,size=ones_count, replace=False)
        z[ones_indicies] = 1
    return z

def read_file(filename):
    try:
        with open(filename, 'rb') as file:
            return file.read()
    except:
        print(f"Error while reading from file {filename}")

def write_file(filename, data, mode='w'):
    try:
        with open(filename, mode) as file:
            file.write(data)
    except:
        print(f"Error while wrtiting into file {filename}")

def split_data(data, k):
    blocks = []
    for i in range(0, len(data), k):
        block = data[i:i+k]
        if len(block) < k:
            block = block + '0' * (k - len(block))
        blocks.append(block)
    return blocks

def encrypt(block, open_key):
    G1, t = open_key
    n = G1.shape[1]
    z = generate_z(n, t)
    m = np.array([int(b) for b in block])
    c = (m @ G1 + z) % 2
    return c

def decrypt(c, private_key):
    S, G, P = private_key
    P_inv = P.T
    S_inv = np.linalg.inv(S).astype(int)
    c1 = (c @ P_inv) % 2

    syndrome = (H @ c1) % 2
    if np.any(syndrome):
        error_pos = None
        for i in range(H.shape[1]):
            if np.array_equal(H[:, i], syndrome):
                error_pos = i
                break
        if error_pos is None:
            raise ValueError("Found more than 1 error")
        c1[error_pos] ^= 1

    u = c1[:S_inv.shape[0]]
    m = (u @ S_inv) % 2
    return m

def main():
    n, k, t = 7, 4, 2

    if len(sys.argv) != 4:
        print(USAGE_MESSAGE)
        return
    
    input_file = sys.argv[1]
    encrypted_file = sys.argv[2]
    decrypted_file = sys.argv[3]

    if not os.path.isfile(input_file):
        print(f"File '{input_file}' not found")
        return

    S = generate_S(k)
    P = generate_P(n)
    G1 = calculate_G1(S, G, P)

    open_key = (G1, t)
    private_key = (S, G, P)

    data = read_file(input_file)
    binary_data = ''.join(format(byte, '08b') for byte in data)
    blocks = split_data(binary_data, k)
    
    processed_encryption = []
    encryption_string = []
    processed_decryption = []
    for block in blocks:
        enc_block = encrypt(block, open_key)
        processed_encryption.append(enc_block)
        str_block = ''.join(str(b) for b in enc_block)
        encryption_string.append(str_block)
    write_file(encrypted_file, ''.join(encryption_string))

    for block in processed_encryption:
        c = np.array([int(ch) for ch in block], dtype=int)
        m = decrypt(c, private_key)
        processed_decryption.append(''.join(str(b) for b in m))
    processed_decryption = ''.join(processed_decryption)
    byte_list = []
    for i in range(0, len(processed_decryption), 8):
        byte_str = processed_decryption[i:i+8]
        if len(byte_str) == 8:
            byte_val = int(byte_str, 2)
            byte_list.append(byte_val)
    while byte_list and byte_list[-1] == 0:
            byte_list.pop()
    write_file(decrypted_file, bytes(byte_list), 'wb')
    print(f"Text from file '{input_file}' has been encrypted into '{encrypted_file}' and decrypted into '{decrypted_file}'")

if __name__ == "__main__":
    main()