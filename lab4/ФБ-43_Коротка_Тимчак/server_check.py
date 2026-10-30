"""Manual interoperation with the RSA educational test website (hex input).

Commands (hex numbers, without 0x):
  python3 server_check.py pub
  python3 server_check.py encrypt M server_n server_e
  python3 server_check.py decrypt C
  python3 server_check.py sign M
  python3 server_check.py verify M S server_n server_e
  python3 server_check.py send k server_n server_e
  python3 server_check.py receive k1 S1 server_n server_e

This script does not access the network; paste numbers from the website.
"""
import argparse
import json
from lab4 import Decrypt, Encrypt, KEYS_PATH, ReceiveKey, SendKey, Sign, Verify


def parse_hex(value):
    return int(value, 16)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=['pub', 'encrypt', 'decrypt',
                                          'sign', 'verify', 'send', 'receive'])
    parser.add_argument('numbers', nargs='*', type=parse_hex)
    opts = parser.parse_args()
    expected = {'pub': 0, 'encrypt': 3, 'decrypt': 1, 'sign': 1,
                'verify': 4, 'send': 3, 'receive': 4}[opts.command]
    if len(opts.numbers) != expected:
        parser.error(f"{opts.command} requires {expected} hex number(s)")
    with KEYS_PATH.open(encoding='utf-8') as f:
        keys = json.load(f)['A']
    public = (keys['public']['n'], keys['public']['e'])
    private = (keys['private']['d'], keys['private']['p'], keys['private']['q'])
    h = lambda value: format(value, 'X')
    args = opts.numbers
    if opts.command == 'pub':
        print('Modulus:', h(public[0]))
        print('Public exponent:', h(public[1]))
    elif opts.command == 'encrypt':
        m, n, e = args
        print('Ciphertext:', h(Encrypt(m, (n, e))))
    elif opts.command == 'decrypt':
        print('Message:', h(Decrypt(args[0], private)))
    elif opts.command == 'sign':
        print('Signature:', h(Sign(args[0], private)[1]))
    elif opts.command == 'verify':
        m, s, n, e = args
        print('Verification:', Verify(m, s, (n, e)))
    elif opts.command == 'send':
        k, n, e = args
        k1, s1 = SendKey(k, private, (n, e))
        print('Key:', h(k1))
        print('Signature:', h(s1))
    elif opts.command == 'receive':
        k1, s1, n, e = args
        k, _s, is_valid = ReceiveKey(k1, s1, private, (n, e))
        print('Verification:', is_valid)
        if is_valid:
            print('Key:', h(k))
        else:
            print('Key rejected')


if __name__ == '__main__':
    main()
