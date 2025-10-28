import random
from typing import List


REPLACEMENT_WORDS = [
    "amazing", "wonderful", "fantastic", "incredible", "awesome",
    "spectacular", "brilliant", "outstanding", "remarkable", "extraordinary",
    "fabulous", "magnificent", "splendid", "superb", "exceptional",
]


def transform_text(text: str, change_probability: float = 0.3) -> str:
    """
    Transform text by randomly replacing words with random alternatives.
    
    Args:
        text: Input text to transform
        change_probability: Probability (0-1) of changing each word
    
    Returns:
        Transformed text with some words randomly changed
    """
    words = text.split()
    transformed_words = []
    
    for word in words:
        if random.random() < change_probability and len(word) > 2:
            replacement = random.choice(REPLACEMENT_WORDS)
            transformed_words.append(replacement)
        else:
            transformed_words.append(word)
    
    return " ".join(transformed_words)
