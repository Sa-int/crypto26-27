import json
import sys

from lab4 import Decrypt, Encrypt, KEYS_PATH, ReceiveKey, SendKey, Sign, Verify

# перевірка взаємодії з http://asymcryptwebservice.appspot.com/?section=rsa
# усі числа на сайті — у шістнадцятковому вигляді; наш ключ — абонент A з keys.json
#   python3 server_check.py pub
#   python3 server_check.py encrypt M n e       — шифруємо для сервера
#   python3 server_check.py decrypt C           — розшифровуємо від сервера
#   python3 server_check.py sign M              — підпис для сервера
#   python3 server_check.py verify M S n e      — перевірка підпису сервера
#   python3 server_check.py send k n e          — надсилаємо ключ серверу
#   python3 server_check.py receive k1 S1 n e   — отримуємо ключ від сервера

with open(KEYS_PATH, encoding="utf-8") as f:
    keys = json.load(f)["A"]
public = (keys["public"]["n"], keys["public"]["e"])
private = (keys["private"]["d"], keys["private"]["p"], keys["private"]["q"])

cmd, *args = sys.argv[1:]
args = [int(a, 16) for a in args]
h = lambda x: f"{x:X}"

if cmd == "pub":
    print("Modulus:", h(public[0]))
    print("Public exponent:", h(public[1]))
elif cmd == "encrypt":
    m, n, e = args
    print("Ciphertext:", h(Encrypt(m, (n, e))))
elif cmd == "decrypt":
    print("Message:", h(Decrypt(args[0], private)))
elif cmd == "sign":
    print("Signature:", h(Sign(args[0], private)[1]))
elif cmd == "verify":
    m, s, n, e = args
    print("Verification:", Verify(m, s, (n, e)))
elif cmd == "send":
    k, n, e = args
    k1, s1 = SendKey(k, private, (n, e))
    print("Key:", h(k1))
    print("Signature:", h(s1))
elif cmd == "receive":
    k1, s1, n, e = args
    k, s, ok = ReceiveKey(k1, s1, private, (n, e))
    print("Key:", h(k))
    print("Verification:", ok)
