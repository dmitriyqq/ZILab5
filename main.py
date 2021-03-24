from math import ceil, isqrt
from argparse import ArgumentParser
from random import randrange, getrandbits


def is_prime(n, k=128):
    # Test if n is not even.
    # But care, 2 is prime !
    if n == 2 or n == 3:
        return True
    if n <= 1 or n % 2 == 0:
        return False
    # find r and s
    s = 0
    r = n - 1
    while r & 1 == 0:
        s += 1
        r //= 2
    # do k tests
    for _ in range(k):
        a = randrange(2, n - 1)
        x = pow(a, r, n)
        if x != 1 and x != n - 1:
            j = 1
            while j < s and x != n - 1:
                x = pow(x, 2, n)
                if x == 1:
                    return False
                j += 1
            if x != n - 1:
                return False
    return True


def generate_prime_candidate(length):
    # generate random bits
    p = getrandbits(length)
    # apply a mask to set MSB and LSB to 1
    p |= (1 << length - 1) | 1
    return p


def generate_prime_number(length=1024):
    p = 4
    while not is_prime(p, 128):
        p = generate_prime_candidate(length)
    return p


def encode(in_file, out_file, key_file):
    try:
        with open(in_file, "rb") as f:
            ba = bytearray(f.read())
            m = int.from_bytes(bytearray([1, 3, 3, 7]) + ba, byteorder="little")
    except:
        print("Failed to read from input file")

    print('read source file with bit length', m.bit_length())

    m_len = ceil((isqrt(m)).bit_length()) + 1

    print('need to generate 2 prime numbers with bit length', m_len)

    p = generate_prime_number(m_len)
    q = generate_prime_number(m_len)

    while p % 4 != 3:
        p = generate_prime_number(m_len)
    while q % 4 != 3:
        q = generate_prime_number(m_len)

    print('p', p)
    print('q', q)

    if m > p * q:
        print('m', m)
        print('pq', p * q)
        raise Exception("Internal error m > n")

    c = pow(m, 2, p * q)
    print('source m', m)
    print('encode c', c)

    try:
        with open(out_file, "wb") as f:
            number_of_bytes = int(ceil(m.bit_length() / 8))
            f.write(c.to_bytes(number_of_bytes, byteorder="little"))
    except:
        print("Failed to write to out file")

    try:
        with open(key_file, "wb") as f:
            number_of_bytes_p = int(ceil(p.bit_length() / 8))
            number_of_bytes_q = int(ceil(q.bit_length() / 8))

            head_p = number_of_bytes_p.to_bytes(4, byteorder="little")
            head_q = number_of_bytes_q.to_bytes(4, byteorder="little")
            data_p = p.to_bytes(number_of_bytes_p, byteorder="little")
            data_q = q.to_bytes(number_of_bytes_q, byteorder="little")
            f.write(head_p + head_q + data_p + data_q)
    except:
        print("Failed to write to key file")

    return p, q


def cal_gcd(a, b):
    if a == 0:
        return b

    return cal_gcd(b % a, a)


def cal_power(x, y, m):
    if y == 0:
        return 1

    p = cal_power(x, y // 2, m) % m

    p = (p * p) % m

    if y % 2 == 0:
        return p
    else:
        return (x * p) % m


def mod_inv(a, m):
    gcd = cal_gcd(a, m)
    if gcd != 1:
        print("Inverse doesn't exist")
    else:
        x = cal_power(a, m - 2, m)
        print("Modular multiplicative inverse is ", x)
        return x


def decode(in_file, out_file, key_file):
    print("Decoding")

    try:
        with open(in_file, "rb") as f:
            ba = bytearray(f.read())
            c = int.from_bytes(ba, byteorder="little")
    except:
        print("Failed to read from input file")

    try:
        with open(key_file, "rb") as f:
            b = bytes(f.read())
            p_size = int.from_bytes(b[:4], 'little')
            p = int.from_bytes(b[8:8+p_size], 'little')
            q = int.from_bytes(b[8+p_size:], 'little')
    except:
        print('failed to generate p and q')

    print('p', p)
    print('q', q)

    m1 = pow(c, (p + 1) // 4, p)
    m2 = p - pow(c, (p + 1) // 4, p)
    m3 = pow(c, (q + 1) // 4, q)
    m4 = q - pow(c, (q + 1) // 4, q)

    print("Calculated m1-m4")

    a = q * (pow(q, -1, p))
    b = p * (pow(p, -1, q))

    print("Calculated a,b")

    n = (p * q)
    big_m1 = (a * m1 + b * m3) % n
    big_m2 = (a * m1 + b * m4) % n
    big_m3 = (a * m2 + b * m3) % n
    big_m4 = (a * m2 + b * m4) % n

    print("Calculated big_m1-big_m4")

    try:
        with open(out_file, "wb") as f:
            for i in [big_m1, big_m2, big_m3, big_m4]:
                number_of_bytes = int(ceil(i.bit_length() / 8))
                decoded_bytes = i.to_bytes(number_of_bytes, byteorder="little")
                if decoded_bytes[0] == 1 and decoded_bytes[1] == 3 and decoded_bytes[2] == 3 and decoded_bytes[3] == 7:
                    f.write(decoded_bytes[4:])
    except:
        print("Failed to write to output file")

    print("Finished Decoding")


def main():
    parser = ArgumentParser(description="encrypt/decrypt files using Rabin algorithm")
    parser.add_argument("-m", "--mode", nargs=1, metavar="mode", type=str, default=None,
                        help="specifies mode encode/decode")
    parser.add_argument("-i", "--inp", nargs=1, metavar="in_file", type=str, default=None,
                        help="path to source file")
    parser.add_argument("-o", "--out", nargs=1, metavar="out_file", type=str, default=None,
                        help="path to output file")
    parser.add_argument("-k", "--key", nargs=1, metavar="key_file", type=str, default=None,
                        help="path to key file")

    # parse the arguments from standard input
    args = parser.parse_args()

    if args.mode is None:
        return
    elif args.inp is None:
        return
    elif args.out is None:
        return
    elif args.key is None:
        return

    if args.mode == ["encode"]:
        print("encode")
        encode(args.inp[0], args.out[0], args.key[0])
    elif args.mode == ["decode"]:
        decode(args.inp[0], args.out[0], args.key[0])

    # p, q = encode("test.txt")
    # decode(p, q)


if __name__ == "__main__":
    # execute only if run as a script
    main()
