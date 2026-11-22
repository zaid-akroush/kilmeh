def sum_positive(numbers):
    total = 0
    for n in numbers:
        if n > 0:
            total += n
    return total
