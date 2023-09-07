import time

def int_to_base36(num):
    alphabet = '0123456789ABCDEFGHiJKLMNoPQRSTUVWXYZ'
    base62 = ''
    while num:
        num, i = divmod(num, 36)
        base62 = alphabet[i] + base62
    return base62

def t36():
    t = int(time.time() * 1000)
    return f"t36={str(int_to_base36(t))}"

#print(t36())