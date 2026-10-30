import math
from collections import Counter

ALPHABET = "абвгдеёжзийклмнопрстуфхцчшщъыьэюя "
WITH_SPACES_FILE = "text_with_spaces.txt"
NO_SPACES_FILE = "text_no_spaces.txt"

def read_file(path):
    with open(path, encoding="utf-8") as f:
        return f.read()

def char_frequencies(text):
    counter = Counter(text)
    total = len(text)
    return [(ch, c, c / total) for ch, c in counter.most_common()]

def bigram_frequencies(text, step):
    counter = Counter(text[i:i + 2] for i in range(0, len(text) - 1, step))
    total = sum(counter.values())
    return [(bg, c, c / total) for bg, c in counter.most_common()]

def h1(freqs):
    return -sum(p * math.log2(p) for _, _, p in freqs)

def h2(freqs):
    return -sum(p * math.log2(p) for _, _, p in freqs) / 2

def report(title, text):
    chars = char_frequencies(text)
    bigrams_overlap = bigram_frequencies(text, 1)
    bigrams_nonoverlap = bigram_frequencies(text, 2)

    print(title)
    print(f"H1 = {h1(chars):.4f}")
    print(f"H2 overlapping bigrams = {h2(bigrams_overlap):.4f}")
    print(f"H2 non-overlapping bigrams = {h2(bigrams_nonoverlap):.4f}")

    print(f"top 5 characters ({len(chars)} distinct):")
    for ch, c, p in chars[:5]:
        label = "space" if ch == " " else ch
        print(f"  {label}: count={c}, freq={p:.5f}")

    print(f"top 5 bigrams overlapping ({len(bigrams_overlap)} distinct):")
    for bg, c, p in bigrams_overlap[:5]:
        print(f"  {bg}: count={c}, freq={p:.5f}")

    print(f"top 5 bigrams non-overlapping ({len(bigrams_nonoverlap)} distinct):")
    for bg, c, p in bigrams_nonoverlap[:5]:
        print(f"  {bg}: count={c}, freq={p:.5f}")
    print()

def main():
    report(f"TEXT WITH SPACES ({WITH_SPACES_FILE})", read_file(WITH_SPACES_FILE))
    report(f"TEXT WITHOUT SPACES ({NO_SPACES_FILE})", read_file(NO_SPACES_FILE))

if __name__ == "__main__":
    main()