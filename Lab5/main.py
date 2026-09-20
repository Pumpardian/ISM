import os, sys
from gost3411 import gost3411
from sha1 import sha1

USAGE_MESSAGE = f"Usage: {sys.argv[0]} mode:[gost3411|sha1] [input_file]"

def read_file(filename):
    try:
        with open(filename, 'rb') as file:
            return file.read()
    except:
        print(f"Error while reading from file {filename}")

def main():
    if len(sys.argv) != 3:
        print(USAGE_MESSAGE)
        return
    
    mode = sys.argv[1]
    input_file = sys.argv[2]

    if not os.path.isfile(input_file):
        print(f"File '{input_file}' not found")
        return
    if mode not in ("gost3411", "sha1"):
        print("Invalid mode")
        print(USAGE_MESSAGE)
        return
    
    data = read_file(input_file)
    print(f"Message: {data.decode()}")
    if mode == "gost3411":
        print(f"GOST3411 HASH (512): {gost3411(data, 512).hex()}")
        print(f"GOST3411 HASH (256): {gost3411(data, 256).hex()}")
    elif mode == "sha1":
        print(f"SHA1 HASH: {sha1(data).hex()}")

if __name__ == "__main__":
    main()