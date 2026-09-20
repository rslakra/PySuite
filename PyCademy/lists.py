def multiply_numbers(numList, multiplier):
    return [num * multiplier for num in numList]


def multipliers(numList, multiplier):
    multipliers = []
    for num in numList:
        multipliers.append(num * multiplier)
    return multipliers


if __name__ == "__main__":
    numbers = [1, 2, 3, 4, 5]
    multiplier = 5
    print(multiply_numbers(numbers, multiplier))
    print(multipliers(numbers, multiplier))
