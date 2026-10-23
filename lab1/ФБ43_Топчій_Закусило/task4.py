import random
from task2 import char_frequencies, bigram_frequencies, h1, h2

ALPHABET_SOURCE = "text_with_spaces.txt"
LENGTH = 34_000

def report(name, seq):
    chars = char_frequencies(seq)
    b_overlap = bigram_frequencies(seq, 1)
    b_nonoverlap = bigram_frequencies(seq, 2)
    print(f"{name}:")
    print(f"  H1 = {h1(chars):.4f}")
    print(f"  H2 overlapping = {h2(b_overlap):.4f}")
    print(f"  H2 non-overlapping = {h2(b_nonoverlap):.4f}")
    print(f"  distinct chars = {len(chars)}")

def main():
    random.seed(42)
    with open(ALPHABET_SOURCE, encoding="utf-8") as f:
        alphabet = sorted(set(f.read()))
    period = len(alphabet)
    repeats = LENGTH // period

    seq_d = "".join(alphabet) * repeats
    shuffled = list(seq_d)
    random.shuffle(shuffled)
    seq_g = "".join(shuffled)

    report("G random order", seq_g)
    report("D periodic", seq_d)

if __name__ == "__main__":
    main()