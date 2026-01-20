from re import A


def getKeys(formatString):
    keys = []
    count = formatString.count("{")
    end = 0
    for i in range(count):
        start = formatString.find("{", end) + 1
        end = formatString.index("}", start)
        key = formatString[start:end]
        keys.append(key)

    return set(keys)


def addPick(cue, userPicks):
    promptFormat = "Enter an example for {name}: "
    prompt = promptFormat.format(name=cue)
    response = input(prompt)
    userPicks[cue] = response


def getUserPicks(cues):
    userPicks = {}
    for cue in cues:
        addPick(cue, userPicks)

    return userPicks


def tellStory(formatString):
    cues = getKeys(formatString)
    userPicks = getUserPicks(cues)
    story = formatString.format(**userPicks)
    print(story)


def main():
    originalStoryFormat = """
    Once upon a time, deep in an ancient jungle,
    there lived a {animal}. This {animal}
    liked to eat {food}, but the jungle had
    very little {food} to offer. One day, an
    explorer found the {animal} and discovered
    it liked {food}. The explorer took the
    {animal} back to {city}, where it could
    eat as much {food} as it wanted. However,
    the {animal} became homesick, so the
    explorer brought it back to the jungle,
    leaving a large supply of {food}.
    The End
    """

    tellStory(originalStoryFormat)
    input("Press Enter to end the program.")


if __name__ == "__main__":
    main()
