from gost3411 import gost3411
import random

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
    
CURVE_P = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFD97
CURVE_A = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFD94
CURVE_B = 0xA6
CURVE_Q = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF6C611070995AD10045841B09B761B893
CURVE_POINT = CurvePoint(
    0x0000000000000000000000000000000000000000000000000000000000000001,
    0x8D91E471E0989CDA27DF505A453F2B7635294F2DDF23E3B122ACC99C9E9F1E14
)

def sign(data, private_key):
    h = gost3411(data, 256)
    z = int.from_bytes(h)

    e = z % CURVE_Q
    if e == 0:
        e = 1

    while True:
        k = random.randint(1, CURVE_Q - 1)
        
        C = CURVE_POINT * k
        r = C.x % CURVE_Q
        if r == 0:
            continue

        s = (r * private_key + k * e) % CURVE_Q
        if s == 0:
            continue

        return (r, s)

def verify(data, signature, public_key):
    r, s = signature

    if not (0 < r < CURVE_Q and 0 < s < CURVE_Q):
        return False
    
    h = gost3411(data, 256)
    z = int.from_bytes(h)

    e = z % CURVE_Q
    if e == 0:
        e = 1

    v = pow(e, -1, CURVE_Q)
    
    z1 = (s * v) % CURVE_Q
    z2 = (-r * v) % CURVE_Q

    C = CURVE_POINT * z1 + public_key * z2
    
    if C.x is None:
        return False
    R = C.x % CURVE_Q

    return R == r