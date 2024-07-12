"""Write files for acceptable words for Twee voor Twaalf for each game type"""

import pandas as pd


def main():
    """Write files for acceptable words for Twee voor Twaalf for each game type"""
    suitability_cols = [
        "AllLowercase",
        "AllBasicAlpha",
        "ZelfstandigNaamwoord",
        "IsEnkelvoud",
    ]
    df = pd.read_csv("../Data/wordlist.csv").assign(
        Suitable=lambda df: df[suitability_cols].fillna(False).all("columns")
    )

    for n_letters in (8, 9, 12):
        suitable_words = df.query("Suitable & Length == @n_letters")["Word"]
        suitable_words.to_csv(
            f"../Output/suitable_{n_letters}_letter_words.txt",
            index=False,
            header=False,
        )


if __name__ == "__main__":

    main()
