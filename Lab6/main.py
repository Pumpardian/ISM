import os, sys
from gost3410 import sign, verify, CURVE_POINT, CURVE_Q, random

USAGE_MESSAGE = f"Usage: {sys.argv[0]} [input_file]"

def read_file(filename):
    try:
        with open(filename, 'rb') as file:
            return file.read()
    except:
        print(f"Error while reading from file {filename}")

def main():
    private_key = random.randint(1, CURVE_Q - 1)
    public_key = CURVE_POINT * private_key

    if len(sys.argv) != 2:
        print(USAGE_MESSAGE)
        return
    
    input_file = sys.argv[1]

    if not os.path.isfile(input_file):
        print(f"File '{input_file}' not found")
        return

    data = read_file(input_file)
    fake_data = data + b" (Fake message)"
    print(f"Message: {data.decode()}")
    print(f"Fake message: {fake_data.decode()}")
    print(f"Private key (d): {hex(private_key)}")
    print(f"Public key (Q):\n   x={hex(public_key.x)}\n   y={hex(public_key.y)}")

    signature = sign(data, private_key)
    is_valid = verify(data, signature, public_key)
    print(f"Signature is {"VALID" if is_valid else "INVALID"} for REAL message")
    is_valid = verify(fake_data, signature, public_key)
    print(f"Signature is {"VALID" if is_valid else "INVALID"} for FAKE message")


if __name__ == "__main__":
    main()