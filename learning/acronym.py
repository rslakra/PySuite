def build_acronym(phrase):
    words = phrase.split()
    return "".join(word[0].upper() for word in words)


if __name__ == "__main__":
    phrase = input("Enter a phrase: ")
    print(build_acronym(phrase))
