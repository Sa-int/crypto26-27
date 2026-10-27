"""Крок 4: остаточне розшифрування за обраним ключем."""
import json
from step1_prepare import ROOT, MOD
from step3_find_keys import decrypt, inverse

if __name__ == '__main__':
    text = (ROOT / 'step1_clean.txt').read_text(encoding='utf-8')
    keys = json.loads((ROOT / 'step3_keys.json').read_text(encoding='utf-8'))
    if not keys:
        raise SystemExit('Ключі не знайдено. Перевірте шифротекст або критерії кроку 3.')
    a, b = keys[0]['a'], keys[0]['b']
    plain = decrypt(text, a, b)
    output = ROOT / 'step4_decrypted.txt'
    output.write_text(plain, encoding='utf-8')
    print(f'Ключ a={a}, b={b}; a^(-1) mod {MOD} = {inverse(a, MOD)}')
    print('Початок тексту:', plain[:200])
    print('Розшифрований текст:', output.name)
