import doublemetaphone

def apply(value: str) -> list[str]:
    words = [doublemetaphone.doublemetaphone(word) for word in value.split(' ')]
    return [' '.join(permutations) for permutations in zip(*words)]
