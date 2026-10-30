"""Крок 2: частотний аналіз неперекривних біграм."""
from collections import Counter
from step1_prepare import ROOT, bigrams

RUSSIAN_TOP = ['ст', 'но', 'то', 'на', 'ен']


def top_bigrams(text, count=5):
    return Counter(bigrams(text)).most_common(count)


if __name__ == '__main__':
    text = (ROOT / 'step1_clean.txt').read_text(encoding='utf-8')
    pairs = bigrams(text)
    print('П’ять найчастіших біграм шифротексту:')
    for bg, n in top_bigrams(text):
        print(bg, n, f'{n / len(pairs) * 100:.2f}%')
    print('Поширені біграми мови:', ', '.join(RUSSIAN_TOP))
