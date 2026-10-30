import collections
import itertools

alphabet = 'абвгдежзийклмнопрстуфхцчшщьыэюя'
m = 31
m2 = m * m

def ext_gcd(a, b):
    if a == 0:
        return b, 0, 1
    gcd, x1, y1 = ext_gcd(b % a, a)
    x = y1 - (b // a) * x1
    y = x1
    return gcd, x, y

def modinv(a, m):
    g, x, y = ext_gcd(a, m)
    if g != 1:
        return None
    return x % m

def solve_linear_congruence(a, b, n):
    g, x, y = ext_gcd(a, n)
    if b % g != 0:
        return []
    a1, b1, n1 = a // g, b // g, n // g
    x0 = (b1 * modinv(a1, n1)) % n1
    return [(x0 + i * n1) % n for i in range(g)]

def bigram_to_num(b):
    return alphabet.index(b[0]) * m + alphabet.index(b[1])

def num_to_bigram(n):
    return alphabet[n // m] + alphabet[n % m]

with open("06.txt", "r", encoding="utf-8") as f:
    ciphertext = f.read().replace('\n', '').strip()
cipher_bigrams = [ciphertext[i:i + 2] for i in range(0, len(ciphertext), 2)]
counter = collections.Counter(cipher_bigrams)
top_5_cipher = [b for b, c in counter.most_common(5)]
print("Топ-5 біграм шифртексту:", top_5_cipher)
top_5_ru = ["ст", "но", "то", "на", "ен"]

forbidden = ['аь', 'еь', 'иь', 'оь', 'уь', 'ыь', 'эь', 'юь', 'яь', 'ьь', 'ьы', 'йь', 'жы', 'шы']

def is_valid_russian(text):
    for fb in forbidden:
        if fb in text: return False
    o_freq = text.count('о') / len(text)
    e_freq = text.count('е') / len(text)
    if o_freq < 0.05 or e_freq < 0.04: return False
    return True

Y_vals = [bigram_to_num(b) for b in top_5_cipher]
X_vals = [bigram_to_num(b) for b in top_5_ru]

possible_keys = set()

for X_pair in itertools.permutations(X_vals, 2):
    for Y_pair in itertools.permutations(Y_vals, 2):
        X1, X2 = X_pair
        Y1, Y2 = Y_pair

        dX = (X1 - X2) % m2
        dY = (Y1 - Y2) % m2

        a_candidates = solve_linear_congruence(dX, dY, m2)
        for a in a_candidates:
            if ext_gcd(a, m2)[0] == 1:
                b = (Y1 - a * X1) % m2
                possible_keys.add((a, b))

print(f"Кількість кандидатів на ключ: {len(possible_keys)}")
for a, b in possible_keys:
    a_inv = modinv(a, m2)
    if not a_inv: continue

    plaintext = ""
    for Y_char in cipher_bigrams:
        Y = bigram_to_num(Y_char)
        X = (a_inv * (Y - b)) % m2
        plaintext += num_to_bigram(X)

    if is_valid_russian(plaintext):
        print(f"\n--- ЗНАЙДЕНО КЛЮЧ ---")
        print(f"a = {a}, b = {b}")
        print("Розшифрований текст:")
        print(plaintext)
        break