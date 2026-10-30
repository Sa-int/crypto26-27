from rsa_common import RNG, Encrypt, Decrypt, Sign, Verify, load, save
keys = load('03_keys_PRIVATE_DO_NOT_SHARE.json')
results = {}
for label in ('A', 'B'):
    public = keys[label]['public']
    private = keys[label]['private']
    m = RNG.randrange(2, public['n'] - 1)
    c = Encrypt(m, public)
    decoded = Decrypt(c, private)
    signature = Sign(m, private)
    ok = Verify(m, signature, public)
    assert decoded == m and ok
    assert not Verify((m+1) % public['n'], signature, public)
    results[label] = {'M': m, 'C': c, 'M_decrypted': decoded, 'S': signature, 'signature_valid': ok, 'changed_message_valid': False}
    print(f'Абонент {label}: M={m}\nC={c}\nM після розшифрування={decoded}\nS={signature}\nПідпис коректний={ok}\n')
save('04_operations.json', results)
