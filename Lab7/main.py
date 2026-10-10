import os, sys, random

USAGE_MESSAGE = f"Usage: {sys.argv[0]} [input_file] [encrypted_file] [decrypted_file]"
BLOCK_SIZE = 16

class CurvePoint:
    def __init__(self, x, y):
        self.x = x
        self.y = y

    def __eq__(self, other):
        return self.x == other.x and self.y == other.y
    
    def __add__(self, other):
        if self.x is None:
            return other
        if other.x is None:
            return self
        
        p = CURVE_P
        if self.x == other.x and (self.y + other.y) % p == 0:
            return CurvePoint(None, None)
        if self.x == other.x and self.y == other.y:
            lam = (3 * self.x * self.x + CURVE_A) * pow(2 * self.y, -1, p) % p
        else:
            lam = (other.y - self.y) * pow(other.x - self.x, -1, p) % p
        x = (lam * lam - self.x - other.x) % p
        y = (lam * (self.x - x) - self.y) % p
        return CurvePoint(x, y)
    
    def __mul__(self, k):
        result = CurvePoint(None, None)
        cumulative = self
        while k:
            if k & 1:
                result = result + cumulative
            cumulative = cumulative + cumulative
            k >>= 1
        return result
    
    def __neg__(self):
        if self.x is None:
            return self
        return CurvePoint(self.x, (-self.y) % CURVE_P)
    
    def to_bytes(self):
        if self.x is None:
            return b'\x00' * 64
        return self.x.to_bytes(32, 'big') + self.y.to_bytes(32, 'big')
    

CURVE_P = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFD97
CURVE_A = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFD94
CURVE_B = 0xA6
CURVE_Q = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF6C611070995AD10045841B09B761B893
CURVE_POINT = CurvePoint(
    0x0000000000000000000000000000000000000000000000000000000000000001,
    0x8D91E471E0989CDA27DF505A453F2B7635294F2DDF23E3B122ACC99C9E9F1E14
)

def is_quadratic_residue(a, p):
    if a % p == 0:
        return True
    return pow(a, (p - 1) // 2, p) == 1

def modular_sqrt(a, p):
    return pow(a, (p + 1) // 4, p)

def koblitz_encode(m, K = 100):
    for j in range(K):
        x = m * K + j
        if x >= CURVE_P:
            break

        rhs = (pow(x, 3, CURVE_P) + CURVE_A * x + CURVE_B) % CURVE_P
        if is_quadratic_residue(rhs, CURVE_P):
            y = modular_sqrt(rhs, CURVE_P)
            return CurvePoint(x, y)
    raise ValueError(f"Could not encode m={m} in {K} tries")

def koblitz_decode(P: CurvePoint, K: int = 100):
    if P.x is None:
        raise ValueError("Point on infinity")
    return P.x // K

def generate_keys():
    x = random.randint(1, CURVE_Q - 1)
    P = CURVE_POINT * x
    return x, P

def encrypt(M, public_key):
    k = random.randint(1, CURVE_Q - 1)
    C1 = CURVE_POINT * k
    C2 = M + public_key * k
    return C1, C2

def decrypt(Points, private_key):
    C1, C2 = Points
    M = C2 + (-(C1 * private_key))
    return M

def read_file(filename):
    try:
        with open(filename, 'rb') as file:
            return file.read()
    except:
        print(f"Error while reading from file {filename}")

def write_file(filename, data):
    try:
        with open(filename, 'wb') as file:
            file.write(data)
    except:
        print(f"Error while writin into file {filename}")

def main():
    if len(sys.argv) != 4:
        print(USAGE_MESSAGE)
        return
    
    input_file = sys.argv[1]
    encrypted_file = sys.argv[2]
    decrypted_file = sys.argv[3]

    if not os.path.isfile(input_file):
        print(f"File '{input_file}' not found")
        return

    private_key, public_key = generate_keys()
    print(f"public key:\n x={hex(public_key.x)}\n y={hex(public_key.y)}\nprivate key: {private_key}")

    data = read_file(input_file)
    encrypted_data = bytearray()
    decrypted_data = bytearray()

    alignment = b'\x00' * ((BLOCK_SIZE - len(data) % BLOCK_SIZE) % BLOCK_SIZE)
    data += alignment

    try:
        for i in range(0, len(data), BLOCK_SIZE):
            block = data[i: i + BLOCK_SIZE]
            m = int.from_bytes(block, 'big')

            P = koblitz_encode(m)
            C1, C2 = encrypt(P, public_key)
            encrypted_data += C1.to_bytes() + C2.to_bytes()

            P = decrypt((C1, C2), private_key)
            m = koblitz_decode(P)
            decrypted_data += m.to_bytes(BLOCK_SIZE, 'big')
    except Exception as e:
        print(f"Error while crypting message: {e}")
        return

    if len(alignment) != 0:
        decrypted_data = decrypted_data[:-len(alignment)]

    write_file(encrypted_file, encrypted_data)
    write_file(decrypted_file, decrypted_data)

    print(f"Text from file '{input_file}' has been encrypted into '{encrypted_file}' and decrypted into '{decrypted_file}'")

if __name__ == "__main__":
    main()