"""
КП №3. Афінна біграмна підстановка. Кроки 1-3 (варіант 2).
Кроки 4-5 (розпізнавач мови, вибір ключа) підключаються через find_candidates().
"""
import argparse
from collections import Counter
from itertools import permutations

ALPHABET = "абвгдежзийклмнопрстуфхцчшщыьэюя"   # m = 31 (без ё, ъ -> ь)
M = len(ALPHABET)
N = M * M                                       # модуль m^2 = 961
IDX = {c: i for i, c in enumerate(ALPHABET)}

# 5 найчастіших біграм російської мови 
LANG_TOP5 = ["ст", "но", "то", "на", "ен"]


# ---------- Крок 1: модулярна арифметика ----------

def egcd(a, b):
    """Розширений алгоритм Евкліда: повертає (d, u, v), де d = gcd(a,b) = u*a + v*b."""
    u0, u1, v0, v1 = 1, 0, 0, 1
    while b:
        q = a // b
        a, b = b, a - q * b
        u0, u1 = u1, u0 - q * u1
        v0, v1 = v1, v0 - q * v1
    return a, u0, v0


def inv(a, n):
    """Обернений елемент a^(-1) mod n; None, якщо gcd(a,n) != 1."""
    d, u, _ = egcd(a % n, n)
    return u % n if d == 1 else None


def solve_linear(a, b, n):
    """Розв'язує a*x = b (mod n). Повертає список ВСІХ розв'язків (може бути порожнім)."""
    a, b = a % n, b % n
    d = egcd(a, n)[0]
    if b % d != 0:
        return []                                # d > 1 і b не ділиться на d: розв'язків немає
    a1, b1, n1 = a // d, b // d, n // d
    x0 = (b1 * inv(a1, n1)) % n1 if n1 > 1 else 0
    return [x0 + k * n1 for k in range(d)]       # рівно d розв'язків


# ---------- Крок 2: біграми ----------

def load(path):
    """Читає текст, лишає лише літери алфавіту (ё -> е, ъ -> ь), повертає список чисел."""
    with open(path, encoding="utf-8") as f:
        text = f.read().lower().replace("ё", "е").replace("ъ", "ь")
    return [IDX[c] for c in text if c in IDX]


def bigram_to_num(bg):
    """'ст' -> x1*m + x2."""
    return IDX[bg[0]] * M + IDX[bg[1]]


def num_to_bigram(X):
    return ALPHABET[X // M] + ALPHABET[X % M]


def top_bigrams(seq, k=5):
    """k найчастіших біграм, що не перетинаються: [(число, кількість), ...]."""
    pairs = [seq[i] * M + seq[i + 1] for i in range(0, len(seq) - 1, 2)]
    return Counter(pairs).most_common(k)


# ---------- Крок 3: кандидати на ключ (a, b) ----------

def key_from_pairs(X1, X2, Y1, Y2):
    """Розв'язує систему (1): a*(X1-X2) = Y1-Y2 (mod m^2), b = Y1 - a*X1 (mod m^2).
    Повертає список допустимих ключів (a, b), де gcd(a, m^2) = 1."""
    keys = []
    for a in solve_linear(X1 - X2, Y1 - Y2, N):
        if egcd(a, N)[0] != 1:                   # a має бути взаємно простим з m^2
            continue
        keys.append((a, (Y1 - a * X1) % N))
    return keys


def find_candidates(seq, lang_top=LANG_TOP5, k=5):
    """Усі кандидати (a, b) для всіх зіставлень пар біграм мови та шифртексту."""
    X = [bigram_to_num(bg) for bg in lang_top]
    Y = [y for y, _ in top_bigrams(seq, k)]
    found = set()
    for xi, xj in permutations(range(len(X)), 2):        # впорядкована пара біграм мови
        for yi, yj in permutations(range(len(Y)), 2):    # впорядкована пара біграм шифртексту
            found.update(key_from_pairs(X[xi], X[xj], Y[yi], Y[yj]))
    return sorted(found)


# Для кроків 4-5 (допоміжне) 

def decrypt(seq, a, b):
    """X = a^(-1) * (Y - b) mod m^2; повертає рядок."""
    a_inv = inv(a, N)
    out = []
    for i in range(0, len(seq) - 1, 2):
        X = (a_inv * (seq[i] * M + seq[i + 1] - b)) % N
        out.append(num_to_bigram(X))
    return "".join(out)


# Крок 4: автоматичний розпізнавач російської мови
 
FREQUENT = set("оае")      # найчастіші літери 
RARE = set("фщэ")          # рідкісні літери 
VOWELS = "аеиоуыэюя"
FORBIDDEN = set(
    [v + "ь" for v in VOWELS]                              
    + ["ьь", "ьы", "ьй", "йь", "йй", "ыы"]                 
    + ["чя", "чю", "щя", "щю", "жя", "шя", "чы", "щы"]     
)
 
MIN_FREQ = 0.20    
MAX_RARE = 0.03    
MAX_FORB = 0.005   
 
 
def metrics(text):
    """(частка о+а+е, частка ф+щ+э, частка заборонених біграм)."""
    n = len(text)
    f_freq = sum(c in FREQUENT for c in text) / n
    f_rare = sum(c in RARE for c in text) / n
    bigrams = [text[i:i + 2] for i in range(n - 1)]      
    f_forb = sum(bg in FORBIDDEN for bg in bigrams) / len(bigrams)
    return f_freq, f_rare, f_forb
 
 
def is_meaningful(text):
    """Текст вважається змістовним, якщо виконано всі три критерії."""
    f_freq, f_rare, f_forb = metrics(text)
    return f_freq >= MIN_FREQ and f_rare <= MAX_RARE and f_forb <= MAX_FORB
 
 
def check_candidates(seq, cands):
    """Крок 4: розшифровує текст кожним кандидатом, повертає (прийняті, відхилені)."""
    accepted, rejected = [], []
    for a, b in cands:
        text = decrypt(seq, a, b)
        row = ((a, b), text, metrics(text))
        (accepted if is_meaningful(text) else rejected).append(row)
    return accepted, rejected
 
 
# Крок 5: вибір ключа та перевірка 
 
def encrypt(seq, a, b):
    """Y = (a*X + b) mod m^2 для кожної біграми, що не перетинається; повертає список чисел Y."""
    return [(a * (seq[i] * M + seq[i + 1]) + b) % N for i in range(0, len(seq) - 1, 2)]
 
 
def pairings_for_key(seq, key, lang_top=LANG_TOP5, k=5):
    """Які зіставлення (біграма мови -> біграма шифртексту) дають цей ключ."""
    X = [bigram_to_num(bg) for bg in lang_top]
    Y = [y for y, _ in top_bigrams(seq, k)]
    result = []
    for xi, xj in permutations(range(len(X)), 2):
        for yi, yj in permutations(range(len(Y)), 2):
            if key in key_from_pairs(X[xi], X[xj], Y[yi], Y[yj]):
                result.append(((lang_top[xi], lang_top[xj]),
                               (num_to_bigram(Y[yi]), num_to_bigram(Y[yj]))))
    return result
 
 
def pairing_statistics(seq, lang_top=LANG_TOP5, k=5):
    """Скільки кандидатів дає кожне з усіх зіставлень: {кількість кандидатів: кількість зіставлень}."""
    X = [bigram_to_num(bg) for bg in lang_top]
    Y = [y for y, _ in top_bigrams(seq, k)]
    stats = Counter()
    for xi, xj in permutations(range(len(X)), 2):
        for yi, yj in permutations(range(len(Y)), 2):
            stats[len(key_from_pairs(X[xi], X[xj], Y[yi], Y[yj]))] += 1
    return stats
 
 
if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--file", default="V2.txt")
    args = ap.parse_args()
 
    y = load(args.file)
    print(f"Довжина шифртексту: {len(y)} літер, біграм: {len(y) // 2}")
 
    # Крок 2 
    print("\n5 найчастіших біграм шифртексту:")
    for Yv, cnt in top_bigrams(y):
        print(f"  {num_to_bigram(Yv)}  (Y = {Yv})  {cnt} разів")
 
    # Крок 3
    cands = find_candidates(y)
    stats = pairing_statistics(y)
    total = sum(stats.values())
    print(f"\nПеребрано зіставлень біграм: {total}")
    print(f"  без жодного допустимого ключа: {stats[0]}")
    print(f"  з одним ключем:                {stats[1]}")
    print(f"  з кількома ключами:            {sum(v for n, v in stats.items() if n > 1)}"
          f"  (найбільше ключів від одного зіставлення: {max(stats)})")
    print(f"Різних кандидатів на ключ (a, b): {len(cands)}")
 
    # Крок 4 
    accepted, rejected = check_candidates(y, cands)
    print(f"\nКрок 4. Відхилено: {len(rejected)}, залишилось: {len(accepted)}")
    names = ["частка о+а+е", "частка ф+щ+э", "частка заборонених біграм"]
    print("Критерії для відхилених кандидатів (мін / середнє / макс):")
    for k in range(3):
        v = [r[2][k] for r in rejected]
        print(f"  {names[k]:28s} {min(v):.4f} / {sum(v) / len(v):.4f} / {max(v):.4f}")
 
    # Крок 5 
    if not accepted:
        print("\nЖодного змістовного тексту не знайдено: потрібно розширити перелік біграм або змінити пороги.")
        raise SystemExit
    if len(accepted) > 1:
        print(f"\nУвага: кандидатів, що пройшли перевірку, декілька ({len(accepted)}). Обрано найкращого за часткою о+а+е:")
        accepted.sort(key=lambda r: r[2][0], reverse=True)
 
    (a, b), text, m = accepted[0]
    print("\nКрок 5. Знайдений ключ:")
    print(f"  a = {a}, b = {b}, a^(-1) mod {N} = {inv(a, N)}")
    print(f"  критерії розшифрованого тексту: о+а+е = {m[0]:.4f}, ф+щ+э = {m[1]:.4f}, заборонені біграми = {m[2]:.4f}")
 
    print("  зіставлення біграм, що дали цей ключ:")
    for (x1, x2), (y1, y2) in pairings_for_key(y, (a, b)):
        print(f"    {x1} -> {y1},  {x2} -> {y2}")
 
    # перевірка: повторне шифрування розшифрованого тексту має дати вихідний шифртекст
    plain_nums = [IDX[c] for c in text]
    ok = encrypt(plain_nums, a, b) == [y[i] * M + y[i + 1] for i in range(0, len(y) - 1, 2)]
    print(f"  перевірка: шифрування розшифрованого тексту ключем (a, b) збігається з шифртекстом: {ok}")
 
    print(f"\nРозшифрований текст ({len(text)} літер):")
    for i in range(0, len(text), 100):
        print(text[i:i + 100])
 
    with open("decrypted.txt", "w", encoding="utf-8") as f:
        f.write(text)
    print("\nРозшифрований текст збережено у файл decrypted.txt")