"""Навчальна реалізація RSA згідно з КП4. Без сторонніх криптобібліотек.
УВАГА: textbook RSA без OAEP/PSS — лише для лабораторної, не для реального захисту.
"""
import json
import math
import random
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DATA = ROOT / 'results'
DATA.mkdir(exist_ok=True)
RNG = random.SystemRandom()
SMALL_PRIMES = (2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37, 41, 43, 47)


def save(name, value):
    (DATA / name).write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding='utf-8')


def load(name):
    return json.loads((DATA / name).read_text(encoding='utf-8'))


def miller_rabin(n, rounds=24, trace=False):
    if n < 2:
        return (False, []) if trace else False
    for p in SMALL_PRIMES:
        if n == p:
            return (True, []) if trace else True
        if n % p == 0:
            return (False, []) if trace else False
    d, s = n - 1, 0
    while d % 2 == 0:
        d //= 2
        s += 1
    log = []
    for i in range(rounds):
        a = RNG.randrange(2, n - 1)
        x = pow(a, d, n)
        entry = {'round': i + 1, 'a': a, 's': s, 'd': d, 'x0': x, 'squares': []}
        if x == 1 or x == n - 1:
            entry['passed'] = True
            log.append(entry)
            continue
        passed = False
        for r in range(1, s):
            x = x * x % n
            entry['squares'].append({'r': r, 'x': x})
            if x == n - 1:
                passed = True
                break
            if x == 1:
                break
        entry['passed'] = passed
        log.append(entry)
        if not passed:
            return (False, log) if trace else False
    return (True, log) if trace else True


def generate_prime(bits=256, rejected=None):
    if bits < 3:
        raise ValueError('Потрібно щонайменше 3 біти')
    while True:
        # Вибираємо випадкове непарне число з установленим старшим бітом.
        n = RNG.getrandbits(bits) | (1 << (bits - 1)) | 1
        divisor = next((p for p in SMALL_PRIMES if n % p == 0 and n != p), None)
        if divisor:
            if rejected is not None and len(rejected) < 8:
                rejected.append({'candidate': n, 'reason': f'пробне ділення на {divisor}'})
            continue
        if miller_rabin(n):
            return n
        if rejected is not None and len(rejected) < 8:
            rejected.append({'candidate': n, 'reason': 'тест Міллера–Рабіна'})


def GenerateKeyPair(p, q, e=65537):
    if p == q or not miller_rabin(p) or not miller_rabin(q):
        raise ValueError('p і q мають бути різними простими числами')
    n = p * q
    phi = (p - 1) * (q - 1)
    if not (1 < e < phi) or math.gcd(e, phi) != 1:
        raise ValueError('e не є взаємно простим із φ(n)')
    d = pow(e, -1, phi)
    return {'public': {'n': n, 'e': e}, 'private': {'d': d, 'p': p, 'q': q}, 'phi': phi}


def Encrypt(m, public):
    n, e = public['n'], public['e']
    if not 0 <= m < n:
        raise ValueError('M має задовольняти 0 ≤ M < n')
    return pow(m, e, n)


def Decrypt(c, private):
    n = private['p'] * private['q']
    if not 0 <= c < n:
        raise ValueError('C поза діапазоном')
    return pow(c, private['d'], n)


def Sign(m, private):
    n = private['p'] * private['q']
    if not 0 <= m < n:
        raise ValueError('Повідомлення поза діапазоном')
    return pow(m, private['d'], n)


def Verify(m, signature, public):
    n = public['n']
    return 0 <= m < n and 0 <= signature < n and pow(signature, public['e'], n) == m


def SendKey(k, sender_private, recipient_public):
    # Протокол із методички: спочатку підпис, потім шифрування обох чисел.
    n_sender = sender_private['p'] * sender_private['q']
    n_recipient = recipient_public['n']
    if not (0 < k < n_sender <= n_recipient):
        raise ValueError('Необхідно 0 < k < nA ≤ nB')
    s = Sign(k, sender_private)
    return {'k1': Encrypt(k, recipient_public), 'S1': Encrypt(s, recipient_public)}


def ReceiveKey(packet, recipient_private, sender_public):
    if sender_public['n'] > recipient_private['p'] * recipient_private['q']:
        raise ValueError('Порушено умову nA ≤ nB')
    k = Decrypt(packet['k1'], recipient_private)
    signature = Decrypt(packet['S1'], recipient_private)
    valid = 0 < k < sender_public['n'] and Verify(k, signature, sender_public)
    return {'k': k, 'S': signature, 'valid': valid}
