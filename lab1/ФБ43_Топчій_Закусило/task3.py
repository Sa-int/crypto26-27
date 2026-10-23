import random
from task2 import read_file, char_frequencies, h1

WITH_SPACES_FILE = "text_with_spaces.txt"
LENGTH = 100_000

def main():
    random.seed(42)
    text = read_file(WITH_SPACES_FILE)
    alphabet = sorted(set(text))

    seq_a = text[:LENGTH]
    seq_b = alphabet[0] * LENGTH
    seq_v = "".join(random.choice(alphabet) for _ in range(LENGTH))

    for name, seq in (("A natural text fragment", seq_a),
                      ("B repeated single char", seq_b),
                      ("C random uniform", seq_v)):
        freqs = char_frequencies(seq)
        print(f"{name}: H1 = {h1(freqs):.4f}, distinct chars = {len(freqs)}, length = {len(seq)}")

if __name__ == "__main__":
    main()