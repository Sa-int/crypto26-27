from rsa_common import generate_prime, save
rejected = []
p = generate_prime(256, rejected)
q = generate_prime(256, rejected)
while q == p:
    q = generate_prime(256, rejected)
p1 = generate_prime(256, rejected)
q1 = generate_prime(256, rejected)
while q1 == p1:
    q1 = generate_prime(256, rejected)
if p * q > p1 * q1:
    p, q, p1, q1 = p1, q1, p, q
assert p * q <= p1 * q1
params = {'p': p, 'q': q, 'p1': p1, 'q1': q1, 'nA': p*q, 'nB': p1*q1, 'rejected': rejected}
save('02_prime_pairs.json', params)
print('Пункт 2. Чотири прості числа по 256 біт згенеровано')
for name in ('p', 'q', 'p1', 'q1'):
    print(f'{name} = {params[name]} ({params[name].bit_length()} біт)')
print('Умова nA ≤ nB:', params['nA'] <= params['nB'])
