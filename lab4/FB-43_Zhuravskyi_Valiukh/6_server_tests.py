"""КП4: ручна взаємодія з RSA Testing Environment (без зовнішніх бібліотек).
Використовує збережену ключову пару з 3_rsa_keys.py; не відправляє ключі в мережу.
Це навчальний textbook RSA (без OAEP/PSS).
"""
from rsa_common import load, Encrypt, Decrypt, Sign, Verify, SendKey, ReceiveKey

URL = 'https://asymcryptwebservice.appspot.com/?section=rsa'

def h(x):
    # HEX байти: парна кількість символів, якщо сервер вибрано в режимі Bytes
    s = format(x, 'X')
    return s if len(s) % 2 == 0 else '0' + s

def parse(label):
    s = input(label + ' (HEX): ').strip().replace(' ', '').removeprefix('0x').removeprefix('0X')
    return int(s, 16)

def main():
    keys = load('03_keys_PRIVATE_DO_NOT_SHARE.json')
    A, B = keys['A'], keys['B']
    print('RSA Testing Environment:', URL)
    print('Відкритий ключ A (із збережених results, 512 біт приблизно):')
    print('Modulus A:', h(A['public']['n']))
    print('Exponent A:', h(A['public']['e']))
    print('Відкритий ключ B:')
    print('Modulus B:', h(B['public']['n']))
    print('Exponent B:', h(B['public']['e']))
    print('\nУвага: не запускай run_all.py повторно під час перевірок — це замінить ключі!')
    while True:
        print('''
1 — Server Encryption -> Python Decryption
2 — Server Signature -> Python Verification
3 — Python Signature -> Server Verification
4 — Python SendKey -> Server ReceiveKey (сервер 1024 біт)
5 — Server SendKey -> Python ReceiveKey (сервер 256 біт)
0 — Вийти''')
        cmd = input('Пункт: ').strip()
        try:
            if cmd == '1':
                print('На сайті Encryption: Modulus A та Exponent A наведені вище; Message = 3039; Bytes; Encrypt.')
                c = parse('Ciphertext з сайту')
                m = Decrypt(c, A['private'])
                print('Decrypted M:', h(m), '\nУСПІХ:', m == 12345)
            elif cmd == '2':
                print('На сайті Server Key згенеруй ключ (наприклад 512 біт). Потім Signature: Message=3039, Bytes, Sign.')
                n = parse('Modulus сервера')
                e = parse('Public exponent сервера')
                signature = parse('Signature із сайту')
                print('Signature valid:', Verify(12345, signature, {'n': n, 'e': e}))
            elif cmd == '3':
                m = 12345
                s = Sign(m, A['private'])
                print('На сайті Verification (режим Bytes):')
                print('Message:', h(m))
                print('Signature:', h(s))
                print('Modulus:', h(A['public']['n']))
                print('Public exponent:', h(A['public']['e']))
                print('Натисни Verify — очікується true.')
            elif cmd == '4':
                print('На сайті Server Key згенеруй 1024-бітний ключ сервера, скопіюй його поля.')
                n = parse('Modulus сервера (1024 біт)')
                e = parse('Public exponent сервера')
                k = 12345
                packet = SendKey(k, A['private'], {'n': n, 'e': e})
                print('На сайті Receive Key введи:')
                print('Key:', h(packet['k1']))
                print('Signature:', h(packet['S1']))
                print('Modulus A:', h(A['public']['n']))
                print('Public exponent A:', h(A['public']['e']))
                print('Натисни Receive. Очікується Key=3039 (можливо 003039 з нулями), Verification=true.')
            elif cmd == '5':
                print('На сайті Server Key згенеруй 256-бітний ключ сервера, після цього Send Key.')
                print('Введи на сайті Send Key:')
                print('Modulus B:', h(B['public']['n']))
                print('Public exponent B:', h(B['public']['e']))
                print('Натисни Send; скопіюй Key і Signature нижче:')
                n = parse('Modulus сервера (256 біт)')
                e = parse('Public exponent сервера')
                k1 = parse('Key (зашифрований) із сайту')
                s1 = parse('Signature (зашифрована) із сайту')
                result = ReceiveKey({'k1': k1, 'S1': s1}, B['private'], {'n': n, 'e': e})
                print('Recovered Key:', h(result['k']))
                print('Verification:', result['valid'])
            elif cmd == '0':
                break
            else:
                print('Обери 1–5 або 0.')
        except (ValueError, KeyError) as err:
            print('Помилка вводу/перевірки:', err)

if __name__ == '__main__':
    main()
