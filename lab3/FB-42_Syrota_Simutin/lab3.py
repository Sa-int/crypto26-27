import sys
from collections import Counter
from itertools import permutations
from pathlib import Path

alphabet_variants = [
    'абвгдежзийклмнопрстуфхцчшщьыэюя',
    'абвгдежзийклмнопрстуфхцчшщыьэюя',
]

reference_bigrams = ['ст', 'но', 'то', 'на', 'ен']

invalid_bigrams = (
    'аь', 'оь', 'иь', 'еь', 'уь', 'юь', 'яь', 'ьь',
    'жы', 'шы', 'чы', 'щы', 'чя', 'щя', 'чю', 'щю',
    'йь', 'ыь', 'ьы', 'ьа', 'ьо', 'ьу', 'ьи', 'ьэ'
)

invalid_sequences = invalid_bigrams + (
    'аьы', 'оьы', 'еьы', 'иьы', 'уьы',
    'жыь', 'шыь', 'чьы', 'щьы',
    'ььы', 'ыьы', 'йьы'
)

invalid_limit = 0.003


def extended_gcd(a, b):
    u0, u1, v0, v1 = 1, 0, 0, 1

    while b:
        quotient = a // b
        a, b = b, a - quotient * b
        u0, u1 = u1, u0 - quotient * u1
        v0, v1 = v1, v0 - quotient * v1

    return a, u0, v0


def modular_inverse(a, n):
    divisor, coefficient, _ = extended_gcd(a % n, n)
    return coefficient % n if divisor == 1 else None


def solve_congruence(a, b, n):
    a, b = a % n, b % n
    divisor, _, _ = extended_gcd(a, n)

    if b % divisor:
        return []

    reduced_modulus = n // divisor

    if reduced_modulus == 1:
        return list(range(n))

    first_root = (
        (b // divisor)
        * modular_inverse(a // divisor, reduced_modulus)
    ) % reduced_modulus

    return [
        first_root + step * reduced_modulus
        for step in range(divisor)
    ]


def load_ciphertext(file_path, alphabet):
    raw_text = Path(file_path).read_text(encoding='utf-8').lower()
    return ''.join(symbol for symbol in raw_text if symbol in alphabet)


def split_bigrams(text):
    return [
        text[position:position + 2]
        for position in range(0, len(text) - 1, 2)
    ]


def bigram_number(pair, letter_positions, m):
    return (
        letter_positions[pair[0]] * m
        + letter_positions[pair[1]]
    )


def decode_text(ciphertext, a, b, alphabet, letter_positions):
    m = len(alphabet)
    modulus = m * m
    inverse = modular_inverse(a, modulus)

    if inverse is None:
        raise ValueError('Ключ a не має оберненого елемента')

    decoded_pairs = []

    for pair in split_bigrams(ciphertext):
        encoded_number = bigram_number(pair, letter_positions, m)
        decoded_number = (inverse * (encoded_number - b)) % modulus

        decoded_pairs.append(
            alphabet[decoded_number // m]
            + alphabet[decoded_number % m]
        )

    return ''.join(decoded_pairs)


def inspect_sequences(text):
    occurrences = {
        sequence: text.count(sequence)
        for sequence in invalid_sequences
    }

    total_hits = sum(occurrences.values())
    frequency = total_hits / max(1, len(text))

    detected = {
        sequence: amount
        for sequence, amount in occurrences.items()
        if amount
    }

    return total_hits, frequency, detected


def passes_language_check(text):
    _, frequency, _ = inspect_sequences(text)
    return frequency < invalid_limit


def search_keys(ciphertext, alphabet, history):
    m = len(alphabet)
    modulus = m * m

    letter_positions = {
        symbol: position
        for position, symbol in enumerate(alphabet)
    }

    frequent_cipher_pairs = [
        pair
        for pair, _ in Counter(split_bigrams(ciphertext)).most_common(5)
    ]

    x = [
        bigram_number(pair, letter_positions, m)
        for pair in reference_bigrams
    ]

    y = [
        bigram_number(pair, letter_positions, m)
        for pair in frequent_cipher_pairs
    ]

    discovered_keys = {}
    checked_systems = 0

    for i, j in permutations(range(5), 2):
        for k, l in permutations(range(5), 2):
            checked_systems += 1

            x_difference = (x[i] - x[j]) % modulus
            y_difference = (y[k] - y[l]) % modulus

            possible_multipliers = solve_congruence(
                x_difference,
                y_difference,
                modulus
            )

            suitable_keys = []

            for a in possible_multipliers:
                if modular_inverse(a, modulus) is None:
                    continue

                b = (y[k] - a * x[i]) % modulus

                suitable_keys.append((a, b))

                discovered_keys.setdefault(
                    (a, b),
                    (
                        reference_bigrams[i],
                        reference_bigrams[j],
                        frequent_cipher_pairs[k],
                        frequent_cipher_pairs[l]
                    )
                )

            history.append({
                'number': checked_systems,
                'alphabet': alphabet,
                'plain': (reference_bigrams[i], reference_bigrams[j]),
                'cipher': (
                    frequent_cipher_pairs[k],
                    frequent_cipher_pairs[l]
                ),
                'dx': x_difference,
                'dy': y_difference,
                'solutions': possible_multipliers,
                'keys': suitable_keys
            })

    evaluated_keys = []

    for (a, b), pair_mapping in discovered_keys.items():
        decoded_text = decode_text(
            ciphertext,
            a,
            b,
            alphabet,
            letter_positions
        )

        hit_count, hit_frequency, detected = inspect_sequences(
            decoded_text
        )

        evaluated_keys.append((
            passes_language_check(decoded_text),
            hit_count,
            hit_frequency,
            a,
            b,
            pair_mapping,
            decoded_text,
            detected
        ))

    evaluated_keys.sort(
        key=lambda entry: (
            not entry[0],
            entry[2],
            entry[1]
        )
    )

    return evaluated_keys, checked_systems, frequent_cipher_pairs


def main():
    source_file = (
        Path(sys.argv[1])
        if len(sys.argv) > 1
        else Path(__file__).with_name('04.txt')
    )

    destination = source_file.parent
    collected_candidates = []
    search_history = []

    for alphabet in alphabet_variants:
        ciphertext = load_ciphertext(source_file, alphabet)

        candidates, system_count, frequent_pairs = search_keys(
            ciphertext,
            alphabet,
            search_history
        )

        passed_count = sum(
            1 for candidate in candidates if candidate[0]
        )

        print('\nАлфавіт:', alphabet)
        print(
            'Довжина:', len(ciphertext),
            ' Систем:', system_count,
            ' Унікальних ключів:', len(candidates)
        )
        print(
            'Топ-5 біграм:',
            Counter(split_bigrams(ciphertext)).most_common(5)
        )

        if candidates:
            (
                accepted,
                hit_count,
                hit_frequency,
                a,
                b,
                pair_mapping,
                decoded_text,
                detected
            ) = candidates[0]

            print(
                f'Кандидат: a = {a}, b = {b}, '
                f'Заборонених l-грам = {hit_count}, '
                f'Частка = {hit_frequency:.6f} '
            )

            print('Початок:', decoded_text[:250])

            for candidate in candidates:
                collected_candidates.append((
                    candidate[0],
                    candidate[1],
                    candidate[2],
                    alphabet,
                    *candidate[3:]
                ))

    collected_candidates.sort(
        key=lambda entry: (
            not entry[0],
            entry[2],
            entry[1]
        )
    )

    (
        accepted,
        hit_count,
        hit_frequency,
        alphabet,
        a,
        b,
        pair_mapping,
        decoded_text,
        detected
    ) = collected_candidates[0]

    (destination / 'decrypted.txt').write_text(
        decoded_text,
        encoding='utf-8'
    )

    with (destination / 'combinations.txt').open(
        'w',
        encoding='utf-8'
    ) as report:
        report.write(
            'Для кожного алфавіту 400 систем: '
            '20 упорядкованих пар відкритого тексту '
            '× 20 пар шифртексту.\n'
        )
        report.write(
            'dx*a ≡ dy (mod 961). '
            'Усі розв’язки a наведені до перевірки оборотності.\n\n'
        )

        for record in search_history:
            first_plain, second_plain = record['plain']
            first_cipher, second_cipher = record['cipher']

            report.write(
                f"[{record['number']:03d}] "
                f"Алфавіт: {record['alphabet']}\n"
            )

            report.write(
                f'  Відповідності: '
                f'{first_plain} -> {first_cipher}; '
                f'{second_plain} -> {second_cipher}\n'
            )

            report.write(
                f"  Порівняння: {record['dx']}*a ≡ "
                f"{record['dy']} (mod 961)\n"
            )

            report.write(
                f"  Розв’язки a: "
                f"{record['solutions'] if record['solutions'] else 'немає'}\n"
            )

            report.write(
                f"  Допустимі ключі (a,b): "
                f"{record['keys'] if record['keys'] else 'немає'}\n\n"
            )

    with (destination / 'candidates.txt').open(
        'w',
        encoding='utf-8'
    ) as report:
        for candidate_number, candidate in enumerate(
            collected_candidates,
            1
        ):
            (
                passed,
                total_hits,
                frequency,
                letter_order,
                key_a,
                key_b,
                mapping,
                text_sample,
                found_sequences
            ) = candidate

            report.write(
                f'Кандидат {candidate_number}: '
                f'a={key_a}, b={key_b}, '
                f'alphabet={letter_order}\n'
            )

            report.write(
                f'Фільтр: '
                f'{"пройдено" if passed else "не пройдено"}; '
                f'заборонених l-грам: {total_hits} '
                f'Частка: {frequency:.6f}\n'
            )

            report.write(
                f'Заборонені l-грами: {found_sequences}\n'
            )

            report.write(
                f'Початок тексту: {text_sample[:300]}\n\n'
            )



if __name__ == '__main__':
    main()