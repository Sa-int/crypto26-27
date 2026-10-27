"""Крок 3: підбір ключів і перевірка кандидатів статистикою."""
import json
from itertools import permutations
from collections import Counter
from math import gcd
from step1_prepare import ALPHA, M, MOD, INDEX, ROOT, bigrams
from step2_frequencies import RUSSIAN_TOP, top_bigrams

FORBIDDEN = ['аь', 'оь', 'иь', 'еь', 'уь', 'юь', 'яь', 'ыь', 'шь', 'щь', 'чь', 'йь', 'ьь', 'ьы', 'ьй', 'ьъ', 'аы', 'оы', 'уы', 'эы', 'юы', 'яы', 'ыы', 'эь', 'фь']


def egcd(a, b):
    old_r, r = a, b
    old_s, s = 1, 0
    old_t, t = 0, 1
    while r:
        q = old_r // r
        old_r, r = r, old_r - q * r
        old_s, s = s, old_s - q * s
        old_t, t = t, old_t - q * t
    return old_r, old_s, old_t


def inverse(a, modulus):
    d, x, _ = egcd(a % modulus, modulus)
    return x % modulus if d == 1 else None


def solve_linear(a, b, modulus):
    a, b = a % modulus, b % modulus
    d = gcd(a, modulus)
    if b % d:
        return []
    reduced = modulus // d
    if reduced == 1:
        return list(range(modulus))
    inv = inverse(a // d, reduced)
    x0 = (inv * (b // d)) % reduced
    return [x0 + k * reduced for k in range(d)]


def bg_to_num(bg):
    return INDEX[bg[0]] * M + INDEX[bg[1]]


def num_to_bg(value):
    return ALPHA[value // M] + ALPHA[value % M]


def decrypt(text, a, b):
    inv = inverse(a, MOD)
    if inv is None:
        return None
    return ''.join(num_to_bg((inv * (bg_to_num(bg) - b)) % MOD) for bg in bigrams(text))


def score(text):
    count = Counter(text)
    n = len(text)
    frequent = sum(count[ch] for ch in 'оае') / n
    rare = sum(count[ch] for ch in 'фщь') / n
    all_pairs = Counter(text[i:i + 2] for i in range(n - 1))
    bad = sum(all_pairs[bg] for bg in FORBIDDEN) / (n - 1)
    return frequent, rare, bad


def meaningful(text):
    f, r, bad = score(text)
    return f > 0.22 and r < 0.06 and bad < 0.005


def attack(text):
    xs = [bg_to_num(bg) for bg in RUSSIAN_TOP]
    ys = [bg_to_num(bg) for bg, _ in top_bigrams(text)]
    possible = set()
    matches = []
    equations = raw_solutions = 0
    for i, j in permutations(range(5), 2):
        for k, l in permutations(range(5), 2):
            equations += 1
            for a in solve_linear(xs[i] - xs[j], ys[k] - ys[l], MOD):
                if gcd(a, MOD) != 1:
                    continue
                b = (ys[k] - a * xs[i]) % MOD
                raw_solutions += 1
                if (a, b) not in possible:
                    possible.add((a, b))
                    plain = decrypt(text, a, b)
                    if meaningful(plain):
                        matches.append({'a': a, 'b': b, 'score': score(plain)})
    return equations, raw_solutions, possible, sorted(matches, key=lambda v: (v['a'], v['b']))


if __name__ == '__main__':
    text = (ROOT / 'step1_clean.txt').read_text(encoding='utf-8')
    eqs, count, possible, matches = attack(text)
    (ROOT / 'step3_keys.json').write_text(json.dumps(matches, ensure_ascii=False, indent=2), encoding='utf-8')
    print('Зіставлень:', eqs)
    print('Розв’язків систем:', count)
    print('Різних ключів:', len(possible))
    print('Кандидатів за критерієм:', len(matches))
    for candidate in matches:
        print('Ключ a =', candidate['a'], 'b =', candidate['b'], 'оцінки =', candidate['score'])
    print('Ключі збережено у step3_keys.json')
