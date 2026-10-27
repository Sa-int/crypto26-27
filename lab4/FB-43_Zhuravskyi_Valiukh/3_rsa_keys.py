import math
from rsa_common import GenerateKeyPair, load, save
pr = load('02_prime_pairs.json')
a = GenerateKeyPair(pr['p'], pr['q'])
b = GenerateKeyPair(pr['p1'], pr['q1'])
assert a['public']['n'] <= b['public']['n']
for x in (a, b):
    assert x['public']['n'] == x['private']['p'] * x['private']['q']
    assert x['phi'] == (x['private']['p'] - 1)*(x['private']['q'] - 1)
    assert math.gcd(x['public']['e'], x['phi']) == 1
    assert (x['public']['e'] * x['private']['d']) % x['phi'] == 1
save('03_keys_PRIVATE_DO_NOT_SHARE.json', {'A': a, 'B': b})
save('03_public_keys.json', {'A': a['public'], 'B': b['public']})
print('Пункт 3. Ключі RSA абонентів A і B згенеровані')
for name, x in (('A', a), ('B', b)):
    print(f'{name}: n={x["public"]["n"]}, e={x["public"]["e"]}')
    print(f'{name}: φ(n)={x["phi"]}')
    print(f'{name}: (e*d) mod φ(n)={(x["public"]["e"] * x["private"]["d"]) % x["phi"]}')
