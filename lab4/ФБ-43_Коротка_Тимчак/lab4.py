import json
import random
import sys

BITS = 256  # довжина кожного простого числа
E = 2**16 + 1  # відкрита експонента, як рекомендовано в методичці
MR_ROUNDS = 20  # кількість основ у тесті Міллера-Рабіна, помилка ≤ 4^(-20)
SMALL_LIMIT = 1000  # пробні ділення на всі прості < 1000
RESULTS_PATH = "results.txt"
CANDIDATES_PATH = "candidates.txt"
KEYS_PATH = "keys.json"


# решето Ератосфена — малі прості для пробних ділень
def small_primes(limit):
    sieve = [True] * limit
    sieve[0] = sieve[1] = False
    for i in range(2, int(limit**0.5) + 1):
        if sieve[i]:
            sieve[i * i::i] = [False] * len(sieve[i * i::i])
    return [i for i, is_p in enumerate(sieve) if is_p]


SMALL_PRIMES = small_primes(SMALL_LIMIT)


# розширений алгоритм Евкліда: повертає (d, u, v), d = gcd(a, b) = u*a + v*b
def egcd(a, b):
    u0, u1, v0, v1 = 1, 0, 0, 1
    while b:
        q = a // b
        a, b = b, a - q * b
        u0, u1 = u1, u0 - q * u1
        v0, v1 = v1, v0 - q * v1
    return a, u0, v0


def gcd(a, b):
    return egcd(a, b)[0]


def inverse(a, n):
    d, u, _ = egcd(a % n, n)
    if d != 1:
        raise ValueError(f"{a} не має оберненого за модулем {n}")
    return u % n


# схема Горнера: біти показника від старшого до молодшого
def mod_pow(x, alpha, m):
    y = 1
    for bit in bin(alpha)[2:]:
        y = y * y % m
        if bit == "1":
            y = y * x % m
    return y


# пробні ділення: повертає дільник, якщо знайшовся, інакше None
def trial_division(p):
    for q in SMALL_PRIMES:
        if q * q > p:
            break
        if p % q == 0:
            return q
    return None


# p - 1 = d * 2^s, d непарне
def decompose(p):
    d, s = p - 1, 0
    while d % 2 == 0:
        d //= 2
        s += 1
    return d, s


# чи є p сильно псевдопростим за основою x (кроки 2.1–2.3 методички)
def is_strong_pseudoprime(p, x, d, s):
    xr = mod_pow(x, d, p)
    if xr == 1 or xr == p - 1:
        return True
    for _ in range(1, s):
        xr = xr * xr % p
        if xr == p - 1:
            return True
        if xr == 1:
            return False
    return False


def miller_rabin(p, k=MR_ROUNDS):
    if p in (2, 3):
        return True
    if p < 2 or p % 2 == 0:
        return False
    d, s = decompose(p)
    for _ in range(k):
        x = random.randrange(2, p - 1)
        if gcd(x, p) > 1:
            return False
        if not is_strong_pseudoprime(p, x, d, s):
            return False
    return True


# проміжні значення тесту Міллера-Рабіна для однієї основи — для звіту
def miller_rabin_trace(p, x):
    d, s = decompose(p)
    lines = [
        f"p = {p}",
        f"p - 1 = d * 2^s, s = {s}, d = {d}",
        f"основа x = {x}, gcd(x, p) = {gcd(x, p)}",
    ]
    xr = mod_pow(x, d, p)
    lines.append(f"x^d mod p = {xr}")
    if xr == 1 or xr == p - 1:
        lines.append("x^d ≡ ±1 (mod p) -> p сильно псевдопросте за основою x")
        return lines
    for r in range(1, s):
        xr = xr * xr % p
        lines.append(f"r = {r}: x^(d*2^{r}) mod p = {xr}")
        if xr == p - 1:
            lines.append(f"x_{r} = -1 -> p сильно псевдопросте за основою x")
            return lines
        if xr == 1:
            lines.append(f"x_{r} = 1 -> p складене")
            return lines
    lines.append("-1 не зустрілося -> p складене")
    return lines


# пошук простого в послідовності m0, m0 + 2, ..., починаючи з випадкового x з [n0, n1]
# rejected — список (кандидат, причина) для звіту
def random_prime(n0, n1, rejected=None):
    while True:
        x = random.randint(n0, n1)
        m0 = x if x % 2 else x + 1
        for m in range(m0, n1 + 1, 2):
            divisor = trial_division(m)
            if divisor is not None:
                if rejected is not None:
                    rejected.append((m, f"ділиться на {divisor}"))
                continue
            if miller_rabin(m):
                return m
            if rejected is not None:
                rejected.append((m, "не пройшло тест Міллера-Рабіна"))


# два старші біти = 1, щоб добуток двох таких чисел мав рівно 2*bits біт
def random_prime_bits(bits, rejected=None):
    return random_prime(3 * 2 ** (bits - 2), 2**bits - 1, rejected)


# ключова пара: відкритий (n, e), секретний (d, p, q)
def GenerateKeyPair(p, q, e=E):
    n = p * q
    phi = (p - 1) * (q - 1)
    if gcd(e, phi) != 1:
        raise ValueError("gcd(e, phi(n)) != 1, потрібні інші p, q")
    d = inverse(e, phi)
    return (n, e), (d, p, q)


def Encrypt(m, public_key):
    n, e = public_key
    return mod_pow(m, e, n)


def Decrypt(c, private_key):
    d, p, q = private_key
    return mod_pow(c, d, p * q)


def Sign(m, private_key):
    d, p, q = private_key
    return m, mod_pow(m, d, p * q)


def Verify(m, s, public_key):
    n, e = public_key
    return mod_pow(s, e, n) == m


# A -> B: (k1, S1) = (k^e1 mod n1, (k^d mod n)^e1 mod n1)
def SendKey(k, sender_private, receiver_public):
    n1, _ = receiver_public
    d, p, q = sender_private
    if p * q > n1:
        raise ValueError("протокол вимагає n ≤ n1")
    _, s = Sign(k, sender_private)
    return Encrypt(k, receiver_public), Encrypt(s, receiver_public)


# B: розшифровує k та S своїм d1 і перевіряє підпис відкритим ключем A
def ReceiveKey(k1, s1, receiver_private, sender_public):
    k = Decrypt(k1, receiver_private)
    s = Decrypt(s1, receiver_private)
    return k, s, Verify(k, s, sender_public)


# save=False — лише друк у консоль; файли перезаписуються тільки з прапорцем --save
def main(save=False):
    out = []
    w = lambda line="": out.append(line)

    # 1–2. дві пари простих довжиною 256 біт, pq ≤ p1q1
    rejected = {}
    primes = {}
    for name in ("p", "q", "p1", "q1"):
        rejected[name] = []
        primes[name] = random_prime_bits(BITS, rejected[name])
    p, q, p1, q1 = primes["p"], primes["q"], primes["p1"], primes["q1"]
    if p * q > p1 * q1:
        p, q, p1, q1 = p1, q1, p, q
        rejected["p"], rejected["q"], rejected["p1"], rejected["q1"] = (
            rejected["p1"], rejected["q1"], rejected["p"], rejected["q"])
        primes = {"p": p, "q": q, "p1": p1, "q1": q1}

    w("1. ГЕНЕРАЦІЯ ПРОСТИХ ЧИСЕЛ")
    w(f"Пробні ділення на {len(SMALL_PRIMES)} простих < {SMALL_LIMIT}, "
      f"далі Міллер-Рабін з {MR_ROUNDS} випадковими основами")
    for name, value in primes.items():
        failed_mr = [m for m, why in rejected[name] if why.startswith("не")]
        w(f"{name} = {value}")
        w(f"   {value.bit_length()} біт; відкинуто кандидатів: {len(rejected[name])} "
          f"(пробні ділення: {len(rejected[name]) - len(failed_mr)}, "
          f"Міллер-Рабін: {len(failed_mr)})")
        for m in failed_mr:
            w(f"   не пройшло МР: {m}")
    w(f"pq ≤ p1q1: {p * q <= p1 * q1}")
    w()

    if save:
        with open(CANDIDATES_PATH, "w", encoding="utf-8") as f:
            for name in primes:
                f.write(f"# {name}: відкинуті кандидати\n")
                for m, why in rejected[name]:
                    f.write(f"{m}  {why}\n")
                f.write(f"{primes[name]}  ПРОСТЕ\n\n")

    # для наочності — просте з найбільшим s у розкладі p - 1 = d * 2^s
    traced = max(primes, key=lambda name: decompose(primes[name])[1])
    w(f"2. ПРОМІЖНІ РЕЗУЛЬТАТИ ТЕСТУ МІЛЛЕРА-РАБІНА (для {traced})")
    for line in miller_rabin_trace(primes[traced], random.randrange(2, primes[traced] - 1)):
        w(line)
    w()

    # 3. ключі RSA для A і B
    public_a, private_a = GenerateKeyPair(p, q)
    public_b, private_b = GenerateKeyPair(p1, q1)
    if save:
        with open(KEYS_PATH, "w", encoding="utf-8") as f:
            json.dump({
                "A": {"public": {"n": public_a[0], "e": public_a[1]},
                      "private": {"d": private_a[0], "p": private_a[1], "q": private_a[2]}},
                "B": {"public": {"n": public_b[0], "e": public_b[1]},
                      "private": {"d": private_b[0], "p": private_b[1], "q": private_b[2]}},
            }, f, indent=2)

    n, e = public_a
    d = private_a[0]
    phi = (p - 1) * (q - 1)
    w("3. КЛЮЧІ RSA")
    w("Абонент A:")
    w(f"   n = p*q = {n}")
    w(f"   phi(n) = (p-1)(q-1) = {phi}")
    w(f"   e = {e}")
    w(f"   d = {d}")
    w("   перевірка співвідношень:")
    w(f"     n = p*q: {n == p * q};  n має {n.bit_length()} біт")
    w(f"     gcd(e, phi(n)) = {gcd(e, phi)}")
    w(f"     e*d mod phi(n) = {e * d % phi}")
    w(f"     1 < e < phi(n), 1 < d < phi(n): {1 < e < phi and 1 < d < phi}")
    w("Абонент B:")
    w(f"   n1 = {public_b[0]}")
    w(f"   e1 = {public_b[1]}")
    w(f"   d1 = {private_b[0]}")
    w(f"Hex для тестового середовища: n = {n:X}, e = {e:X}")
    w(f"                              n1 = {public_b[0]:X}")
    w()

    # 4. шифрування / розшифрування / підпис для A і B
    w("4. ШИФРУВАННЯ ТА ЦИФРОВИЙ ПІДПИС")
    for who, public, private in (("A", public_a, private_a), ("B", public_b, private_b)):
        m = random.randrange(1, public[0])
        c = Encrypt(m, public)
        m_dec = Decrypt(c, private)
        _, s = Sign(m, private)
        w(f"Абонент {who}:")
        w(f"   M = {m}")
        w(f"   C = M^e mod n = {c}")
        w(f"   C^d mod n = {m_dec}  (збігається з M: {m_dec == m})")
        w(f"   S = M^d mod n = {s}")
        w(f"   Verify(M, S): {Verify(m, s, public)};  "
          f"Verify(M + 1, S): {Verify(m + 1, s, public)}")
    w()

    # 5. протокол розсилання ключів A -> B
    k = random.randrange(1, n)
    k1, s1 = SendKey(k, private_a, public_b)
    k_recv, s_recv, ok = ReceiveKey(k1, s1, private_b, public_a)
    w("5. ПРОТОКОЛ КОНФІДЕНЦІЙНОГО РОЗСИЛАННЯ КЛЮЧА A -> B")
    w(f"Умова n ≤ n1: {n <= public_b[0]}")
    w(f"A: секретний ключ k = {k}")
    w(f"A: S = k^d mod n = {Sign(k, private_a)[1]}")
    w(f"A: k1 = k^e1 mod n1 = {k1}")
    w(f"A: S1 = S^e1 mod n1 = {s1}")
    w("A -> B по відкритому каналу: (k1, S1)")
    w(f"B: k = k1^d1 mod n1 = {k_recv}")
    w(f"B: S = S1^d1 mod n1 = {s_recv}")
    w(f"B: S^e mod n = {mod_pow(s_recv, e, n)}")
    w(f"B: підпис вірний (k = S^e mod n): {ok};  отриманий k збігається з надісланим: {k_recv == k}")

    print("\n".join(out))
    if save:
        with open(RESULTS_PATH, "w", encoding="utf-8") as f:
            f.write("\n".join(out) + "\n")
        print(f"\nЗбережено: {RESULTS_PATH}, {CANDIDATES_PATH}, {KEYS_PATH}")


if __name__ == "__main__":
    main(save="--save" in sys.argv)
