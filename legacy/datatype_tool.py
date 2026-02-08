import struct

DEFAULT_DECIMAL = 3

# ┌────────────────────┐
#   bits
# └────────────────────┘

def word1_to_bit(uint16, position):
    if 0 <= uint16 <= 65535 and 0 <= position < 16:
        bit = bool((uint16 >> position) & 1)
        return bit
    else:
        return None

def bit_to_word1(bit, position):
    if 0 <= position < 16 and isinstance(bit, bool):
        result = int(bit) << position
        return result
    else:
        return None

def word1_to_bits(uint16):
    if 0 <= uint16 <= 65535:
        bits = []
        for _ in range(16):
            bits.append(bool(uint16 & 1))
            uint16 >>= 1
        bits_rev = bits[::-1]
        return bits_rev
    else:
        return None

def bits_to_word1(bit00, bit01, bit02, bit03, bit04, bit05, bit06, bit07, 
                  bit08, bit09, bit10, bit11, bit12, bit13, bit14, bit15):
    bits = [bit15, bit14, bit13, bit12, bit11, bit10, bit09, bit08,
            bit07, bit06, bit05, bit04, bit03, bit02, bit01, bit00]
    if all(isinstance(bit, bool) for bit in bits):
        result = 0
        for i, bit in enumerate(bits):
            result |= int(bit) << i
        return result
    else:
        return None
    
# ┌────────────────────┐
#   unit16 / int16
# └────────────────────┘
    
def uint16_to_int16(uint16):
    uint16 = int(uint16)
    uint16 = uint16 % 65536
    return uint16 if uint16 <= 32767 else uint16 - 65536

def int16_to_uint16(int16):
    int16 = int(int16)
    int16 = ((int16 + 32768) % 65536) - 32768
    return int16 + 65536 if int16 < 0 else int16

def word1_to_uint16(word0):
    int0 = int(word0)
    uint16 = int0
    return uint16

def uint16_to_word1(uint16):
    uint16 = int(uint16)
    word0 = uint16 & 0xFFFF
    return word0

def word1_to_int16(word0):
    uint16 = word1_to_uint16(word0) % 65536
    return uint16 if uint16 <= 32767 else uint16 - 65536

def int16_to_word1(int16):
    int16 = int(int16)
    uint16 = int16_to_uint16(int16)
    word0 = int(uint16) & 0xFFFF
    return word0

# ┌────────────────────┐
#   uint32 / int32
# └────────────────────┘

def uint32_to_int32(uint32):
    uint32 = int(uint32) % 4294967296
    return uint32 if uint32 <= 2147483647 else uint32 - 4294967296

def int32_to_uint32(int32):
    int32 = int(int32)
    int32 = ((int32 + 2147483648) % 4294967296) - 2147483648
    return int32 + 4294967296 if int32 < 0 else int32

def word2_to_uint32(word0, word1):
    int0 = int(word0)
    int1 = int(word1)
    uint32 = (int0 * 65536) + int1
    return uint32

def word2_to_uint32_reversed(word0, word1):
    uint32 = word2_to_uint32(word1, word0)
    return uint32

def uint32_to_word2(uint32):
    uint32 = int(uint32)
    word0 = (uint32 >> 16) & 0xFFFF
    word1 = uint32 & 0xFFFF
    return word0, word1

def uint32_to_word2_reversed(uint32):
    word0, word1 = uint32_to_word2(uint32)
    return word1, word0

def word2_to_int32(word0, word1):
    uint32 = word2_to_uint32(word0, word1) % 4294967296
    return uint32 if uint32 <= 2147483647 else uint32 - 4294967296

def word2_to_int32_reversed(word0, word1):
    int32 = word2_to_int32(word1, word0)
    return int32

def int32_to_word2(int32):
    int32 = int(int32)
    uint32 = int32_to_uint32(int32)
    word0 = (uint32 >> 16) & 0xFFFF
    word1 = uint32 & 0xFFFF
    return word0, word1

def int32_to_word2_reversed(int32):
    word0, word1 = int32_to_word2(int32)
    return word1, word0

# ┌────────────────────┐
#   uint64 / int64
# └────────────────────┘
    
def uint64_to_int64(uint64):
    uint64 = int(uint64)
    if 0 <= uint64 <= 18446744073709551615:
        if uint64 <= 9223372036854775807:
            return uint64
        else:
            return uint64 - 18446744073709551616
    else:
        return None

def int64_to_uint64(int64):
    int64 = int(int64)
    if -9223372036854775808 <= int64 <= 9223372036854775807:
        if int64 < 0:
            return int64 + 18446744073709551616
        else:
            return int64
    else:
        return None

def word4_to_uint64(word0, word1, word2, word3):
    int0 = int(word0)
    int1 = int(word1)
    int2 = int(word2)
    int3 = int(word3)
    uint64 = (int0 * 65536**3) + (int1 * 65536**2) + (int2 * 65536) + int3
    return uint64

def uint64_to_word4(uint64):
    uint64 = int(uint64)
    word0 = (uint64 >> 48) & 0xFFFF
    word1 = (uint64 >> 32) & 0xFFFF
    word2 = (uint64 >> 16) & 0xFFFF
    word3 = uint64 & 0xFFFF
    return word0, word1, word2, word3

def word4_to_int64(word0, word1, word2, word3):
    uint64 = word4_to_uint64(word0, word1, word2, word3)
    if uint64 > 9223372036854775807:
        int64 = uint64 - 18446744073709551616
    else:
        int64 = uint64
    return int64

def int64_to_word4(int64):
    int64 = int(int64)
    uint64 = int64_to_uint64(int64)
    word0 = (uint64 >> 48) & 0xFFFF
    word1 = (uint64 >> 32) & 0xFFFF
    word2 = (uint64 >> 16) & 0xFFFF
    word3 = uint64 & 0xFFFF
    return word0, word1, word2, word3

# ┌────────────────────┐
#   float32
# └────────────────────┘

def word2_to_float32(word0, word1, decimal=DEFAULT_DECIMAL):
    bin0 = (int(word0) & 0xFFFF) << 16
    bin1 = (int(word1) & 0xFFFF)
    bin2 = bin0 | bin1
    float32 = struct.unpack('>f', struct.pack('>I', bin2))[0]
    return round(float32, decimal)

def word2_to_float32_reversed(word0, word1, decimal=DEFAULT_DECIMAL):
    float32 = word2_to_float32(word1, word0, decimal)
    return float32

def float32_to_word2(float32):
    float32 = float(float32)
    bin_float = struct.pack('>f', float32)
    uint32 = struct.unpack('>I', bin_float)[0]
    word0 = (uint32 >> 16) & 0xFFFF
    word1 = uint32 & 0xFFFF
    return word0, word1

def float32_to_word2_reversed(float32):
    word0, word1 = float32_to_word2(float32)
    return word1, word0

# ┌────────────────────┐
#   float64
# └────────────────────┘

def word4_to_float64(word0, word1, word2, word3, decimal=DEFAULT_DECIMAL):
    bin0 = (int(word0) & 0xFFFF) << 48
    bin1 = (int(word1) & 0xFFFF) << 32
    bin2 = (int(word2) & 0xFFFF) << 16
    bin3 = (int(word3) & 0xFFFF)
    bin4 = bin0 | bin1 | bin2 | bin3
    float64 = struct.unpack('>d', struct.pack('>Q', bin4))[0]
    return round(float64, decimal)

def float64_to_word4(float64):
    float64 = float(float64)
    bin_float = struct.pack('>d', float64)
    uint64 = struct.unpack('>Q', bin_float)[0]
    word0 = (uint64 >> 48) & 0xFFFF
    word1 = (uint64 >> 32) & 0xFFFF
    word2 = (uint64 >> 16) & 0xFFFF
    word3 = uint64 & 0xFFFF
    return word0, word1, word2, word3

# ┌────────────────────┐
#   fixed32
# └────────────────────┘

def word2_to_fixed32(word0, word1, decimal=DEFAULT_DECIMAL,
                     sign_bit=1, integer_bit=15, fraction_bit=16):
    
    # Convert two 16bit words to 16bit bins
    bin0 = format(word0, '016b')
    bin1 = format(word1, '016b')
    
    # Combine two 16bit bins to 32bit bin
    bin2 = bin0 + bin1
    
    # Calculate sign
    sign = -1 if bin2[0] == '1' else 1
    
    # Calculate integer part
    integer_begin = sign_bit
    integer_end = sign_bit + integer_bit
    integer_bin = bin2[integer_begin : integer_end]
    integer = int(integer_bin, 2)
    
    # Calculate fraction part
    fraction_begin = sign_bit + integer_bit
    fraction_end = sign_bit + integer_bit + fraction_bit
    fraction_bin = bin2[fraction_begin : fraction_end]
    fraction_divider = 2 ** fraction_bit
    fraction = int(fraction_bin, 2) / fraction_divider
    
    # Calculate float
    fixed32 = sign * (integer + fraction)
    return round(fixed32, decimal)

def word2_to_fixed32_reversed(word0, word1, decimal=DEFAULT_DECIMAL,
                              sign_bit=1, integer_bit=15, fraction_bit=16):
    fixed32 = word2_to_fixed32(word1, word0, decimal,
                               sign_bit, integer_bit, fraction_bit)
    return fixed32

def fixed32_to_word2(fixed32, sign_bit=1, integer_bit=15, fraction_bit=16):
    fixed32 = float(fixed32)
    
    # Calculate sign
    sign = 1 if fixed32 < 0 else 0
    fixed32 = abs(fixed32)
    
    # Calculate integer part
    integer = int(fixed32)
    
    # Calculate fraction part
    fraction = int((fixed32 - integer) * (2 ** fraction_bit))
    
    # Combine all to form a binary string
    bin_str = f'{sign:0{sign_bit}b}{integer:0{integer_bit}b}{fraction:0{fraction_bit}b}'
    
    # Split into two words
    word0 = int(bin_str[:16], 2)
    word1 = int(bin_str[16:], 2)
    
    return word0, word1

def fixed32_to_word2_reversed(fixed32, sign_bit=1, integer_bit=15, fraction_bit=16):
    word0, word1 = fixed32_to_word2(fixed32, sign_bit, integer_bit, fraction_bit)
    return word1, word0

# ┌────────────────────┐
#   fixed64
# └────────────────────┘

def word4_to_fixed64(word0, word1, word2, word3, decimal=DEFAULT_DECIMAL,
                     sign_bit=1, integer_bit=31, fraction_bit=32):
    
    # Convert four 16bit words to 16bit bins
    bin0 = format(word0, '016b')
    bin1 = format(word1, '016b')
    bin2 = format(word2, '016b')
    bin3 = format(word3, '016b')
    
    # Combine four 16bit bins to 32bit bin
    bin4 = bin0 + bin1 + bin2 + bin3
    
    # Calculate sign
    sign = -1 if bin4[0] == '1' else 1
    
    # Calculate integer part
    integer_begin = sign_bit
    integer_end = sign_bit + integer_bit
    integer_bin = bin4[integer_begin : integer_end]
    integer = int(integer_bin, 2)
    
    # Calculate fraction part
    faction_begin = sign_bit + integer_bit
    faction_end = sign_bit + integer_bit + fraction_bit
    faction_bin = bin4[faction_begin : faction_end]
    faction_divider = 2 ** fraction_bit
    faction = int(faction_bin, 2) / faction_divider
    
    # Calculate float
    fixed64 = sign * (integer + faction)
    return round(fixed64, decimal)

def fixed64_to_word4(fixed64, sign_bit=1, integer_bit=31, fraction_bit=32):
    fixed64 = float(fixed64)
    
    # Calculate sign
    sign = 1 if fixed64 < 0 else 0
    fixed64 = abs(fixed64)
    
    # Calculate integer part
    integer = int(fixed64)
    
    # Calculate fraction part
    fraction = int((fixed64 - integer) * (2 ** fraction_bit))
    
    # Combine all to form a binary string
    bin_str = f'{sign:0{sign_bit}b}{integer:0{integer_bit}b}{fraction:0{fraction_bit}b}'
    
    # Split into four words
    word0 = int(bin_str[:16], 2)
    word1 = int(bin_str[16:32], 2)
    word2 = int(bin_str[32:48], 2)
    word3 = int(bin_str[48:], 2)
    
    return word0, word1, word2, word3

# ┌────────────────────┐
#   char
# └────────────────────┘

def word1_to_char2(word):
    if 0 <= word <= 65535:
        char1 = chr((word >> 8) & 0xFF)
        char2 = chr(word & 0xFF)
        return char1 + char2
    else:
        return None

def char2_to_word1(char2):
    if len(char2) == 2:
        word = (ord(char2[0]) << 8) | ord(char2[1])
        return word
    else:
        return None

if __name__ == '__main__':
    while True:
        word1 = input('word1: ')
        word2 = input('word2: ')
        res = word2_to_float32(word1, word2)
        print(res)

        # word1 = int(input('word1: '))
        # word1 = True if word1 == 1 else False
        # word2 = int(input('word2: '))
        # res = bit_to_word1(word1, word2)
        # print(res)

        # int16 = input('int16: ')
        # res = int16_to_uint16(int16)
        # print(res)