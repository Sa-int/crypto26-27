from rsa_common import generate_prime, miller_rabin, save
rejected = []
p = generate_prime(256, rejected)
passed, log = miller_rabin(p, trace=True)
assert passed and len(log) == 24
result = {'prime': p, 'bit_length': p.bit_length(), 'rejected': rejected, 'miller_rabin_base_example': log[0], 'rounds': 24}
save('01_primes_test.json', result)
print('Пункт 1. Згенероване просте число:', p)
print('Бітова довжина:', p.bit_length())
print('Відхилених кандидатів у журналі:', len(rejected))
print('Проміжні дані Міллера–Рабіна (1 основа):', log[0])
