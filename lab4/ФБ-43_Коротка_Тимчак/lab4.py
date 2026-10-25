"""Computer practice 4: educational textbook RSA and Miller-Rabin.

No external crypto/primality implementations are used. The --sample option
reproduces the saved numbers from the submitted report. No padding is used:
this RSA variant is ONLY for the course demonstration, not real security.
"""
import json
import random
import sys
from pathlib import Path

BITS = 256
E = 2**16 + 1
MR_ROUNDS = 20
SMALL_LIMIT = 1000
HERE = Path(__file__).resolve().parent
RESULTS_PATH = HERE / "results.txt"
CANDIDATES_PATH = HERE / "candidates.txt"
KEYS_PATH = HERE / "keys.json"
SAMPLE_PATH = HERE / "sample_run.json"


def small_primes(limit):
    if limit <= 2:
        return []
    sieve = [True] * limit
    sieve[0] = sieve[1] = False
    for i in range(2, int(limit**0.5) + 1):
        if sieve[i]:
            sieve[i*i::i] = [False] * len(sieve[i*i::i])
    return [i for i, is_prime in enumerate(sieve) if is_prime]


SMALL_PRIMES = small_primes(SMALL_LIMIT)


def egcd(a, b):
    """Return (g, u, v), where g = gcd(a,b) = u*a + v*b."""
    u0, u1, v0, v1 = 1, 0, 0, 1
    while b:
        quotient = a // b
        a, b = b, a - quotient * b
        u0, u1 = u1, u0 - quotient * u1
        v0, v1 = v1, v0 - quotient * v1
    return a, u0, v0


def gcd(a, b):
    return egcd(a, b)[0]


def inverse(a, n):
    if n <= 1:
        raise ValueError("modulus must exceed 1")
    divisor, u, _ = egcd(a % n, n)
    if divisor != 1:
        raise ValueError("No modular inverse exists")
    return u % n


def mod_pow(x, alpha, m):
    """Horner square-and-multiply, from the highest exponent bit."""
    if m < 1 or alpha < 0:
        raise ValueError("invalid modulus or negative exponent")
    y = 1 % m
    x %= m
    for bit in bin(alpha)[2:]:
        y = y * y % m
        if bit == '1':
            y = y * x % m
    return y


def trial_division(n):
    """Return a small prime divisor, if found, or None."""
    for divisor in SMALL_PRIMES:
        if divisor * divisor > n:
            break
        if n % divisor == 0:
            return divisor
    return None


def decompose(n):
    """For odd n > 2, represent n-1 = d * 2**s, d odd."""
    if n <= 2 or n % 2 == 0:
        raise ValueError("an odd integer > 2 is required")
    d, s = n - 1, 0
    while d % 2 == 0:
        d //= 2
        s += 1
    return d, s


def is_strong_pseudoprime(n, base, d, s):
    value = mod_pow(base, d, n)
    if value in (1, n - 1):
        return True
    for _ in range(1, s):
        value = value * value % n
        if value == n - 1:
            return True
        if value == 1:
            return False
    return False


def miller_rabin(n, k=MR_ROUNDS, used_bases=None, first_base=None, rng=None):
    """Own MR test. Store the ACTUAL chosen bases of each successful round.

    The optional first_base supports rechecking the historical saved sample
    with a stated reproducible witness, followed by further random bases.
    """
    if k < 1:
        raise ValueError("k must be positive")
    if n in (2, 3):
        return True
    if n < 2 or n % 2 == 0:
        return False
    d, s = decompose(n)
    generator = rng if rng is not None else random
    visited = set()
    if first_base is not None and not 2 <= first_base <= n - 2:
        raise ValueError("base outside allowed interval")
    for round_index in range(min(k, n - 3)):
        if round_index == 0 and first_base is not None:
            base = first_base
        else:
            base = generator.randrange(2, n - 1)
            while base in visited:
                base = generator.randrange(2, n - 1)
        visited.add(base)
        if used_bases is not None:
            used_bases.append(base)
        if gcd(base, n) != 1 or not is_strong_pseudoprime(n, base, d, s):
            return False
    return True


def miller_rabin_trace(n, base):
    """Show one complete witnessed round (base must be from a real test)."""
    if not 2 <= base <= n - 2:
        raise ValueError("base outside allowed interval")
    d, s = decompose(n)
    lines = [
        f"n = {n}",
        f"n-1 = d*2^s: s = {s}, d = {d}",
        f"base x = {base}; gcd(x,n) = {gcd(base, n)}",
    ]
    value = mod_pow(base, d, n)
    lines.append(f"x_0 = x^d mod n = {value}")
    if value in (1, n - 1):
        lines.append("x_0 is +1 or -1 modulo n: this round PASSED")
        return lines
    for r in range(1, s):
        value = value * value % n
        lines.append(f"r={r}: x_{r} = x_(r-1)^2 mod n = {value}")
        if value == n - 1:
            lines.append("x_r = n-1: this round PASSED")
            return lines
        if value == 1:
            lines.append("non-trivial square root of 1: COMPOSITE")
            return lines
    lines.append("no -1 appeared: COMPOSITE")
    return lines


def random_prime(n0, n1, rejected=None, bases_for_prime=None, rng=None):
    """Choose random x in [n0,n1]; scan ascending odd candidates."""
    if n0 < 3 or n1 < n0:
        raise ValueError("invalid interval")
    generator = rng if rng is not None else random
    while True:
        x = generator.randint(n0, n1)
        start = x if x % 2 else x + 1
        for candidate in range(start, n1 + 1, 2):
            divisor = trial_division(candidate)
            if divisor is not None:
                if rejected is not None:
                    rejected.append((candidate, f"divisible by {divisor}"))
                continue
            bases = []
            if miller_rabin(candidate, used_bases=bases, rng=generator):
                if bases_for_prime is not None:
                    bases_for_prime.extend(bases)
                return candidate
            if rejected is not None:
                rejected.append((candidate, "Miller-Rabin rejected"))


def random_prime_bits(bits, rejected=None, bases_for_prime=None, rng=None):
    if bits < 3:
        raise ValueError("bits >= 3 required")
    # Two highest bits are set; thus both p,q are >= 3*2^(bits-2).
    return random_prime(3 * 2**(bits-2), 2**bits - 1,
                        rejected, bases_for_prime, rng)


def GenerateKeyPair(p, q, e=E):
    """Return public (n,e), private (d,p,q); p,q already passed MR."""
    if p <= 2 or q <= 2 or p == q or p % 2 == 0 or q % 2 == 0:
        raise ValueError("p and q must be different odd primes > 2")
    n = p * q
    phi = (p - 1) * (q - 1)
    if not 1 < e < phi or gcd(e, phi) != 1:
        raise ValueError("invalid public exponent for these primes")
    d = inverse(e, phi)
    assert e * d % phi == 1
    return (n, e), (d, p, q)


def Encrypt(m, public_key):
    n, e = public_key
    if not 0 <= m < n:
        raise ValueError("message must satisfy 0 <= m < n")
    return mod_pow(m, e, n)


def Decrypt(c, private_key):
    d, p, q = private_key
    n = p * q
    if not 0 <= c < n:
        raise ValueError("ciphertext must satisfy 0 <= c < n")
    return mod_pow(c, d, n)


def Sign(m, private_key):
    d, p, q = private_key
    n = p * q
    if not 0 <= m < n:
        raise ValueError("message must satisfy 0 <= m < n")
    return m, mod_pow(m, d, n)


def Verify(m, s, public_key):
    n, e = public_key
    return 0 <= m < n and 0 <= s < n and mod_pow(s, e, n) == m


def SendKey(k, sender_private, receiver_public):
    """A: sign k with d_A; encrypt k and signature for B using e_B."""
    _, p, q = sender_private
    n = p * q
    n1, _ = receiver_public
    if n > n1:
        raise ValueError("protocol requires sender n <= receiver n1")
    if not 0 < k < n:
        raise ValueError("shared key must satisfy 0 < k < sender n")
    _, s = Sign(k, sender_private)
    return Encrypt(k, receiver_public), Encrypt(s, receiver_public)


def ReceiveKey(k1, s1, receiver_private, sender_public):
    """B: validate ranges; decrypt and verify; NEVER accept an invalid key.

    Returns (k,S,True) only for a valid key; otherwise (None,None,False).
    The provided sender public key must be authenticated out of band.
    """
    _, p1, q1 = receiver_private
    n1 = p1 * q1
    n, _ = sender_public
    if n > n1 or not (0 <= k1 < n1 and 0 <= s1 < n1):
        return None, None, False
    k = Decrypt(k1, receiver_private)
    s = Decrypt(s1, receiver_private)
    if not (0 < k < n and 0 <= s < n and Verify(k, s, sender_public)):
        return None, None, False
    return k, s, True


def load_sample():
    with SAMPLE_PATH.open(encoding="utf-8") as f:
        return json.load(f)


def recreate_candidates(prime, total_rejected):
    """Reconstruct the historical consecutive odd search interval.

    Counts and candidate classifications are checked against the saved report.
    This is only for reproducing the example, not part of random generation.
    """
    start = prime - 2 * total_rejected
    rejected = []
    for candidate in range(start, prime, 2):
        divisor = trial_division(candidate)
        rejected.append((candidate, f"divisible by {divisor}" if divisor
                         else "Miller-Rabin rejected"))
    return rejected


def create_parameters(sample=False):
    if sample:
        data = load_sample()
        primes = {key: data[key] for key in ("p", "q", "p1", "q1")}
        rejected = {name: recreate_candidates(primes[name], data["rejected_count"][name])
                    for name in primes}
        # Repeat an MR verification with an ACTUALLY USED, recorded first base.
        rng = random.Random(20261025)
        base_log = {}
        for name, prime in primes.items():
            bases = []
            kwargs = {"first_base": data["trace_base"]} if name == "p1" else {}
            assert miller_rabin(prime, used_bases=bases, rng=rng, **kwargs)
            base_log[name] = bases
        return primes, rejected, base_log, data

    while True:
        primes, rejected, base_log = {}, {}, {}
        for name in ("p", "q", "p1", "q1"):
            rejected[name], base_log[name] = [], []
            primes[name] = random_prime_bits(BITS, rejected[name], base_log[name])
        if len(set(primes.values())) != 4:
            continue
        if primes["p"] * primes["q"] > primes["p1"] * primes["q1"]:
            primes = {"p": primes["p1"], "q": primes["q1"],
                      "p1": primes["p"], "q1": primes["q"]}
            rejected = {"p": rejected["p1"], "q": rejected["q1"],
                        "p1": rejected["p"], "q1": rejected["q"]}
            base_log = {"p": base_log["p1"], "q": base_log["q1"],
                        "p1": base_log["p"], "q1": base_log["q"]}
        try:
            GenerateKeyPair(primes["p"], primes["q"])
            GenerateKeyPair(primes["p1"], primes["q1"])
            return primes, rejected, base_log, None
        except ValueError:
            # In particular, retry if gcd(e,phi(n)) != 1.
            continue


def main(save=False, sample=False):
    primes, rejected, base_log, data = create_parameters(sample)
    p, q, p1, q1 = (primes[name] for name in ("p", "q", "p1", "q1"))
    public_a, private_a = GenerateKeyPair(p, q)
    public_b, private_b = GenerateKeyPair(p1, q1)
    n, e = public_a
    n1, e1 = public_b
    out = []
    w = lambda line="": out.append(line)
    w("1. PRIME GENERATION")
    w(f"Trial division by {len(SMALL_PRIMES)} primes < {SMALL_LIMIT}; then {MR_ROUNDS} MR bases")
    for name, value in primes.items():
        mr_failed = [v for v, reason in rejected[name] if reason.startswith("Miller")]
        w(f"{name} = {value}")
        w(f" {value.bit_length()} bits, rejected {len(rejected[name])}: "
          f"trial={len(rejected[name]) - len(mr_failed)}, MR={len(mr_failed)}")
        for v in mr_failed:
            w(f" MR rejected: {v}")
    w(f"pq <= p1*q1: {p*q <= p1*q1}")
    w()
    traced = max(primes, key=lambda name: decompose(primes[name])[1])
    used_base = base_log[traced][0]
    w(f"2. MILLER-RABIN TRACE: {traced}; base from actual verification round 1 of {len(base_log[traced])}")
    w(f"MR bases actually used for {traced}: {base_log[traced]}")
    w(f"The selected trace base occurred in the test: {used_base in base_log[traced]}")
    for line in miller_rabin_trace(primes[traced], used_base):
        w(line)
    w()
    phi = (p - 1) * (q - 1)
    w("3. RSA KEYS")
    w(f"A: n={n}; phi={phi}; e={e}; d={private_a[0]}")
    w(f"A: n=p*q: {n==p*q}; bits={n.bit_length()}")
    w(f"A: gcd(e,phi)={gcd(e,phi)}; e*d mod phi={e*private_a[0]%phi}")
    w(f"B: n1={n1}; e1={e1}; d1={private_b[0]}")
    phi1 = (p1 - 1) * (q1 - 1)
    w(f"B: gcd(e1,phi1)={gcd(e1,phi1)}; e1*d1 mod phi1={e1*private_b[0]%phi1}")
    w(f"n <= n1: {n <= n1}")
    w(f"Server HEX: n={n:X}, e={e:X}")
    w()
    w("4. ENCRYPTION AND SIGNATURES")
    for name, public, private in (("A", public_a, private_a), ("B", public_b, private_b)):
        m = data["M_"+name] if data else random.randrange(1, public[0] - 1)
        c = Encrypt(m, public)
        m2 = Decrypt(c, private)
        _, sig = Sign(m, private)
        w(f"{name}: M={m}")
        w(f"{name}: C={c}; decrypted={m2}; equals M={m2==m}")
        w(f"{name}: S={sig}; Verify={Verify(m,sig,public)}; "
          f"Verify tampered={Verify(m+1,sig,public)}")
    w()
    k = data["k"] if data else random.randrange(1, n)
    k1, s1 = SendKey(k, private_a, public_b)
    got_k, got_s, ok = ReceiveKey(k1, s1, private_b, public_a)
    w("5. SEND KEY A -> B")
    w(f"k={k}; S={Sign(k,private_a)[1]}")
    w(f"k1={k1}; S1={s1}")
    w(f"received k={got_k}; received S={got_s}")
    w(f"verified={ok}; same key={got_k==k}")
    w(f"invalid zero key rejected by SendKey: {test_send_invalid(private_a,public_b)}")
    w(f"altered signature rejected by ReceiveKey: {ReceiveKey(k1,(s1+1)%n1,private_b,public_a)[2] is False}")

    print("\n".join(out))
    if save:
        with RESULTS_PATH.open("w", encoding="utf-8") as f:
            f.write("\n".join(out) + "\n")
        with CANDIDATES_PATH.open("w", encoding="utf-8") as f:
            for name in primes:
                f.write(f"# {name}: {len(rejected[name])} rejected\n")
                for value, cause in rejected[name]:
                    f.write(f"{value} {cause}\n")
                f.write(f"{primes[name]} PRIME\n\n")
        with KEYS_PATH.open("w", encoding="utf-8") as f:
            json.dump({"A": {"public": {"n": n, "e": e},
                             "private": {"d": private_a[0], "p": p, "q": q}},
                       "B": {"public": {"n": n1, "e": e1},
                             "private": {"d": private_b[0], "p": p1, "q": q1}}},
                      f, indent=2, ensure_ascii=False)
        print("Saved: results.txt, candidates.txt, keys.json")


def test_send_invalid(sender_private, receiver_public):
    try:
        SendKey(0, sender_private, receiver_public)
    except ValueError:
        return True
    return False


if __name__ == "__main__":
    if any(arg not in ("--save", "--sample") for arg in sys.argv[1:]):
        raise SystemExit("Usage: python3 lab4.py [--sample] [--save]")
    main(save="--save" in sys.argv, sample="--sample" in sys.argv)
