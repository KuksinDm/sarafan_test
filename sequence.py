def generate_sequence(n):
    sequence = []
    number = 1
    while len(sequence) < n:
        sequence.extend([number] * number)
        number += 1
    return sequence[:n]


try:
    n = input('Введите количество элементов: ')
    if not n.isdigit() or int(n) <= 0:
        raise ValueError(
            'Введено некорректное значение.'
            'Пожалуйста, введите положительное целое число.'
        )

    n = int(n)
    result = generate_sequence(n)
    print('Последовательность:', result)

except ValueError as e:
    print('Ошибка:', e)
