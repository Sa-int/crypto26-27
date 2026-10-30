import runpy
from pathlib import Path
root = Path(__file__).resolve().parent
for file in ('1_prime_generation.py', '2_prime_pairs.py', '3_rsa_keys.py', '4_rsa_operations.py', '5_key_transfer.py'):
    print('\n' + '=' * 70 + '\n' + file + '\n' + '=' * 70)
    runpy.run_path(str(root / file), run_name='__main__')
