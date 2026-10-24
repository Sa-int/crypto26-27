"""Крок 1: завантаження і очищення шифротексту."""
from pathlib import Path
import sys

ALPHA = 'абвгдежзийклмнопрстуфхцчшщьыэюя'
M = len(ALPHA)
MOD = M * M
INDEX = {letter: i for i, letter in enumerate(ALPHA)}
ROOT = Path(__file__).resolve().parent


def clean_text(source):
    return ''.join(ch for ch in source.lower() if ch in INDEX)


def bigrams(text):
    return [text[i:i + 2] for i in range(0, len(text) - 1, 2)]


def read_cipher(path):
    try:
        return path.read_text(encoding='utf-8-sig')
    except UnicodeDecodeError:
        return path.read_text(encoding='cp1251')


if __name__ == '__main__':
    source = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / '03 (1).txt'
    text = clean_text(read_cipher(source))
    output = ROOT / 'step1_clean.txt'
    output.write_text(text, encoding='utf-8')
    print('Алфавіт:', ALPHA)
    print('Модуль:', MOD)
    print('Символів:', len(text))
    print('Біграм:', len(bigrams(text)))
    print('Збережено:', output.name)
