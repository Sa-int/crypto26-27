from rsa_common import RNG, SendKey, ReceiveKey, load, save
keys = load('03_keys_PRIVATE_DO_NOT_SHARE.json')
a, b = keys['A'], keys['B']
k = RNG.randrange(2, a['public']['n'] - 1)
packet = SendKey(k, a['private'], b['public'])
received = ReceiveKey(packet, b['private'], a['public'])
assert received['valid'] and received['k'] == k
result = {'original_k': k, 'k1_transmitted': packet['k1'], 'S1_transmitted': packet['S1'], 'recovered_k': received['k'], 'recovered_S': received['S'], 'authentic': received['valid']}
save('05_key_transfer.json', result)
for title, val in result.items():
    print(f'{title}: {val}')
print('Конфіденційність: шифрування відкритим ключем B, розшифрування секретним B.')
print('Автентичність: підпис секретним ключем A, перевірка відкритим ключем A.')
