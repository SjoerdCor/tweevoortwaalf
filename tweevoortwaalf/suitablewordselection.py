"""Write files for acceptable words for Twee voor Twaalf for each game type"""

from typing import Set

import pandas as pd


def generate_rotations(word: str) -> Set[str]:
    """Generate all rotations for a word"""
    return {word[i:] + word[:i] for i in range(len(word))}


def remove_rotated_duplicates(series: pd.Series) -> pd.Series:
    """Filter out all words that also occur rotated"""
    rotation_map = {}

    for word in series:
        rotations = generate_rotations(word)
        for rotation in rotations:
            if rotation in rotation_map:
                rotation_map[rotation].add(word)
            else:
                rotation_map[rotation] = {word}

    unique_words = [
        word
        for word in series
        if all(
            len(rotation_map[rotation]) == 1 for rotation in generate_rotations(word)
        )
    ]
    return pd.Series(unique_words)


def remove_anagrams(series: pd.Series) -> pd.Series:
    """Remove all words from a series that also occur as an anagram"""
    anagram_map = {}

    for word in series:
        sorted_word = "".join(sorted(word))
        if sorted_word in anagram_map:
            anagram_map[sorted_word].add(word)
        else:
            anagram_map[sorted_word] = {word}

    unique_words = [
        word for word in series if len(anagram_map["".join(sorted(word))]) == 1
    ]

    return pd.Series(unique_words)


def main():
    """Write files for acceptable words for Twee voor Twaalf for each game type"""
    suitability_cols = [
        "AllLowercase",
        "AllBasicAlpha",
        "ZelfstandigNaamwoord",
        "IsEnkelvoud",
    ]
    df = (
        pd.read_csv("Data/wordlist.csv")
        .assign(Suitable=lambda df: df[suitability_cols].fillna(False).all("columns"))
        .query("Suitable")
    )

    for n_letters in (8, 9, 12):
        suitable_words = df.query("Length == @n_letters")["Word"]
        if n_letters in (8, 9):
            suitable_words = remove_rotated_duplicates(suitable_words)
        if n_letters == 12:
            suitable_words = remove_anagrams(suitable_words)
        suitable_words.to_csv(
            f"../Output/suitable_{n_letters}_letter_words.txt",
            index=False,
            header=False,
        )


if __name__ == "__main__":

    main()
