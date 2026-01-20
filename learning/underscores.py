def replace_underscores(text):
    return text and text.replace(' ', '_')


if __name__ == "__main__":
    phrase = input("Enter a phrase: ")
    print(replace_underscores(phrase))
