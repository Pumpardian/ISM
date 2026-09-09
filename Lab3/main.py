import os, sys, random

USAGE_MESSAGE = f"Usage: {sys.argv[0]} [input_file] [output_file_encrypted] [output_file_decrypted]"

def is_prime_number(number):
    if number <= 1:
        return False
    for i in range(2, int(number ** 0.5) + 1):
        if number % i == 0:
            return False
    return True

def generate_prime_number(limit):
    while True:
        number = random.getrandbits(limit)
        if is_prime_number(number) and number % 4 == 3:
            return number

def generate_keys(limit):
    p, q = 0, 0
    while p == q:
        p = generate_prime_number(limit)
        q = generate_prime_number(limit)
    return p * q, (p, q)

def bezu(p, q):
    if q == 0:
        return (1, 0)
    else:
        x, y = bezu(q, p % q)
        return (y, x - (p // q) * y)

def chinese_remainder_theorem(p, q, x, y, m, n):
    r1 = (x * p * n + y * q * m) % (p * q)
    r2 = (p * q) - r1
    r3 = (x * p * n - y * q * m) % (p * q)
    r4 = (p * q) - r3
    print(f"{r1} {r2} {r3} {r4}")
    return (r1, r2, r3, r4)

def modular_pow(base, exponent, mod):
    if mod == 1:
        return 0
    result = 1
    base = base % mod
    while exponent > 0:
        if exponent % 2 == 1:
            result = (result * base) % mod
        exponent = exponent // 2
        base = (base * base) % mod
    return result

def encrypt(data, public_key):
    return data**2 % public_key

def decrypt(c, private_key):
    p, q = private_key
    x, y = bezu(p, q)
    m = modular_pow(c, (p + 1) // 4, p)
    n = modular_pow(c, (q + 1) // 4, q)
    remainders = chinese_remainder_theorem(p, q, x, y, m, n)
    for r in remainders:
        if r >= 0 and r <= 255:
            return r

def write_file(filename, data, mode='wb'):
    try:
        with open(filename, mode) as file:
            file.write(data)
    except:
        print("Failed to write to file")

def read_file(filename):
    try:
        with open(filename, 'rb') as file:
            return file.read()
    except:
        print(f"Failed to read from file '{filename}'")

def main():
    if len(sys.argv) != 4:
        print(USAGE_MESSAGE)
        return
    
    input_file = sys.argv[1]
    output_file_enc = sys.argv[2]
    output_file_dec = sys.argv[3]

    if not os.path.isfile(input_file):
        print(f"File '{input_file}' not found")
        return
    
    data = read_file(input_file)
    numbers = list(data)

    public_key, private_key = generate_keys(30)
    print(f"public key: {public_key}\nprivate key: {private_key}")
    processed_encryption = []
    processed_decryption = []
    for number in numbers:
        enc = encrypt(number, public_key)
        dec = decrypt(enc, private_key)
        processed_encryption.append(enc)
        processed_decryption.append(dec)

    processed_encryption = ' '.join(str(num) for num in processed_encryption)
    processed_decryption = bytes(processed_decryption)
    write_file(output_file_enc, processed_encryption, 'w')
    write_file(output_file_dec, processed_decryption)
    print(f"Text from file '{input_file}' has been encrypted into '{output_file_enc}' and decrypted into '{output_file_dec}'")

if __name__ == "__main__":
    main()