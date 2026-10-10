import os, sys, cv2 as cv, numpy as np

USAGE_MESSAGE = f"Usage: {sys.argv[0]} action:[embed|extract] [input_file](embed only) [source_image_file](embed only) [embedded_image_file]"
BLOCK_PART = (1,2)
QUANT = 8

def text_to_bits(text):
    data = text.encode('utf-8')
    header = len(data).to_bytes(4)
    bits = []
    for b in header + data:
        for i in range(7, -1, -1):
            bits.append((b >> i) & 1)
    return bits

def bits_to_bytes(bits):
    result = bytearray()
    for i in range(0, len(bits), 8):
        byte = 0
        for j in range(8):
            byte = (byte << 1) | bits[i + j]
        result.append(byte)
    return bytes(result)

def embed(image, text, output):
    ycrcb = cv.cvtColor(image, cv.COLOR_BGR2YCrCb)
    y = ycrcb[:, :, 0].astype(np.float32)
    
    h, w = y.shape
    H, W = (h // 8) * 8, (w // 8) * 8
    
    aligned = np.zeros((H, W), dtype=np.float32)
    aligned[:H, :W] = y[:H, :W]

    text_bits = text_to_bits(text)
    total_blocks = (H // 8) * (W // 8)
    if len(text_bits) > total_blocks:
        raise ValueError(f"Message is too large: {len(text_bits)} bits, for provided image only {total_blocks} available")
    
    bit_index = 0
    for i in range(0, H, 8):
        for j in range(0, W, 8):
            if bit_index >= len(text_bits):
                break

            block = aligned[i:i+8, j:j+8]
            dct = cv.dct(block)

            coef = dct[BLOCK_PART]
            val = int(np.round(coef / QUANT))
            if text_bits[bit_index] == 1:
                if val % 2 == 0: val += 1
            else:
                if val % 2 != 0: val -= 1
            
            dct[BLOCK_PART] = float(val * QUANT)
            aligned[i:i+8, j:j+8] = cv.idct(dct)
            bit_index += 1

    result_y = np.clip(aligned, 0, 255).astype(np.uint8)
    ycrcb[:H, :W, 0] = result_y
    result = cv.cvtColor(ycrcb, cv.COLOR_YCrCb2BGR)

    cv.imwrite(output, result, [cv.IMWRITE_JPEG_QUALITY, 100])
    print(f"Embedded {bit_index} bits ({bit_index // 8} bytes) into image")

def extract(encoded_image):
    img = cv.imread(encoded_image)
    ycrcb = cv.cvtColor(img, cv.COLOR_BGR2YCrCb)
    y = ycrcb[:, :, 0].astype(np.float32)

    h, w = y.shape
    H, W = h // 8 * 8, w // 8 * 8

    bits = []
    for i in range(0, H, 8):
        for j in range(0, W, 8):
            block = y[i:i+8, j:j+8]
            dct = cv.dct(block)

            coef = dct[BLOCK_PART]
            val = int(np.round(coef / QUANT))
            bits.append(val % 2)

    header_bytes = bits_to_bytes(bits[:32])
    length = int.from_bytes(header_bytes, 'big')

    if length <= 0 or length * 8 > len(bits) - 32:
        raise ValueError(f"Invalid length {length}, image does not contain a message or was recompressed")

    data_bits = bits[32:32 + length * 8]
    return bits_to_bytes(data_bits).decode('utf-8')

def read_file(filename):
    try:
        with open(filename, 'r') as file:
            return file.read()
    except:
        print(f"Error while reading from file {filename}")

def main():
    if len(sys.argv) not in (5, 3):
        print(USAGE_MESSAGE)
        return
    
    action = sys.argv[1]
    if action not in ("embed", "extract"):
        print(USAGE_MESSAGE)
        return
    elif action == "embed" and len(sys.argv) != 5:
        print(USAGE_MESSAGE)
    elif action == "extract" and len(sys.argv) != 3:
        print(USAGE_MESSAGE)
    
    if len(sys.argv) == 5:
        text_file = sys.argv[2]
        source_image_file = sys.argv[3]
        embedded_image_file = sys.argv[4]
    elif len(sys.argv) == 3:
        embedded_image_file = sys.argv[2]
    
    try:
        if action == "embed":
            if not os.path.isfile(text_file):
                print(f"File '{text_file}' not found")
                return
            if not os.path.isfile(source_image_file):
                print(f"File '{source_image_file}' not found")
                return
    
            text = read_file(text_file)
            source_image = cv.imread(source_image_file, cv.IMREAD_UNCHANGED)
            if source_image is None:
                print("Something went wrong")
                return
            embed(source_image, text, embedded_image_file)
            print(f"Message from file '{text_file}' was embedded into file '{source_image_file}', results were exported into '{embedded_image_file}'")
        elif action == "extract":
            msg = extract(embedded_image_file)
            print(msg)
    except Exception as e:
        print(f"An error occured during image processing: {e}")

if __name__ == "__main__":
    main()