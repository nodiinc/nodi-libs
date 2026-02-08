       
def num10_to_alphanum36(YYMMDDNN: int) -> str:
    if not isinstance(YYMMDDNN, int) or YYMMDDNN < 0:
        raise ValueError("Input must be a non-negative integer")
    if YYMMDDNN == 0:
        return '0'
    result = ''
    while YYMMDDNN > 0:
        digit = YYMMDDNN % 36
        if digit < 10:
            result = str(digit) + result
        else:
            result = chr(ord('A') + (digit - 10)) + result
        YYMMDDNN //= 36
    return result

if __name__ == '__main__':
    print(num10_to_alphanum36(24091617))