def getKeys(formatString, unique=False):
    """
    Get the keys from the format string using indexes.

    Args:
        formatString (str): The format string to get the keys from
        i.e. "blah {delicious} blah blah {food} blah {drink} ..."

    Returns:
        list: A list of keys
        i.e. ["delicious", "food", "drink"]

    Example:
        >>> getKeys("blah {delicious} blah blah {food} blah {drink} ...")
        ["delicious", "food", "drink"]
    """
    keys = []
    count = formatString.count("{")

    # If there are no keys, return an empty list
    if count == 0:
        return keys

    # Get the keys from the format string using indexes
    end = 0
    for i in range(count):
        start = formatString.find("{", end)
        end = formatString.index("}", start)
        if start == -1 or end == -1:
            break

        # Get the key from the format string
        key = formatString[start + 1 : end]
        keys.append(key)

    # Return the keys
    return list(set(keys)) if unique else keys


if __name__ == "__main__":
    formatString = input("Enter a format string: ")
    print()
    print(getKeys(formatString))
    print()
    print("Unique keys:")
    print(getKeys(formatString, unique=True))
    print()
