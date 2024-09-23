"""Create the pipeline for fitting paardensprongen"""

import importlib.resources
from functools import wraps

import pandas as pd
from sklearn.base import BaseEstimator, TransformerMixin
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestClassifier
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.impute import SimpleImputer
from sklearn.model_selection import GridSearchCV
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import FunctionTransformer

DATA_PATH = importlib.resources.files("tweevoortwaalf.Data").joinpath(
    "suitable_8_letter_words.txt"
)
eightletterwords = pd.read_csv(DATA_PATH, header=None).squeeze()
DATA_PATH = importlib.resources.files("tweevoortwaalf.Data").joinpath(
    "suitable_9_letter_words.txt"
)
nineletterwords = pd.read_csv(DATA_PATH, header=None).squeeze()
eightlettervectorizer = CountVectorizer(analyzer="char", ngram_range=(2, 2))
eightlettervectorizer.fit(eightletterwords)
ngrams_occurences_total = (
    eightlettervectorizer.transform(eightletterwords).toarray().sum(axis=0)
)

wordlist = pd.read_csv("../tweevoortwaalf/Data/wordlist.csv")
# There are some duplicates in Word for words including ij, where one occurs very infrequently
frequency = wordlist.query("Length == 8").groupby("Word")["Frequency"].max().dropna()


# pylint: disable=redefined-outer-name
def get_occurence_ngrams(
    ngram_length: int = 1, wordlist: pd.Series = nineletterwords
) -> pd.Series:
    """Find how often (combinations of) letters occur

    Parameters
    ----------
    ngram_length : int
        The length of the letter string
    wordlist : pd.Series
        A series containing words from which to count the combination of lengths
    """
    cv = CountVectorizer(analyzer="char_wb", ngram_range=(ngram_length, ngram_length))
    occurences = cv.fit_transform(wordlist)
    df = pd.DataFrame(occurences.toarray(), columns=cv.get_feature_names_out()).rename(
        columns=lambda s: s.replace(" ", "_")
    )
    return df.sum()


def calculate_odds_letters():
    """Calculate the combination of a letter given another letter before or after it"""
    twograms = get_occurence_ngrams(2)
    twograms.index = pd.MultiIndex.from_arrays(
        [twograms.index.str[0], twograms.index.str[1]],
        names=["FirstLetter", "SecondLetter"],
    )

    odds = twograms.to_frame("Occurrences").assign(
        PercentageSecondLetterGivenFirst=lambda df: df["Occurrences"]
        / df.groupby("FirstLetter")["Occurrences"].sum(),
        PercentageFirstLetterGivenSecond=lambda df: df["Occurrences"]
        / df.groupby("SecondLetter")["Occurrences"].sum(),
    )
    return odds


odds = calculate_odds_letters()


def apply_on_array(func):
    """Decorator so function works in sklearn pipeline"""

    @wraps(func)
    def wrapper(arr):
        outc = [func(x) for x in arr]
        return pd.Series(outc, index=arr.index)

    return wrapper


def easyness_score(woord, vectorizer=eightlettervectorizer):
    "Sums all transitions of letters -> the higher, the more logical"
    ngrams_occurences_word = vectorizer.transform([woord])
    return (ngrams_occurences_word * ngrams_occurences_total).sum()


def logical_single_direction(word):
    """Check the second least likely transition including the transition across the word boundary"""
    circular_word = word + word[0]
    logical = []
    for i in range(len(circular_word) - 1):
        logical.append(easyness_score(circular_word[i] + circular_word[i + 1]))
    return sorted(logical)[1]


def logical_correct_direction(word, compensation=0.5):
    """Compare both directions"""
    logical_actual_direction = logical_single_direction(word)
    logical_wrong_direction = logical_single_direction(word[::-1])
    return (logical_actual_direction + compensation) / (
        logical_wrong_direction + compensation
    )


@apply_on_array
def direction_on_array(word):
    """Calculate whether the direction of the word is the most logical of each word in array"""
    return logical_correct_direction(word)


def logical_word_boundary(word, compensation=0.5):
    """Assuming the correct direction, see howeasy it is to find the beginning of word"""
    circular_word = word + word[0]
    logical = []
    for i in range(len(circular_word) - 1):
        logical.append(
            1 / (easyness_score(circular_word[i] + circular_word[i + 1]) + compensation)
        )
    return logical[-1] / sum(logical)


@apply_on_array
def wordboundary_on_array(word):
    """Calculate how obvious it is where the word starts for each word in array"""
    return logical_word_boundary(word)


@apply_on_array
def calc_frequency(word):
    """Get the frequency of each word in array"""
    return frequency.get(word, 0)


directiontransformer = FunctionTransformer(
    func=direction_on_array,
    feature_names_out=lambda self, input_features: [
        x + "DirectionLogical" for x in input_features
    ],
)
wordboundarytransformer = FunctionTransformer(
    func=wordboundary_on_array,
    feature_names_out=lambda self, input_features: [
        x + "BoundaryLogical" for x in input_features
    ],
)

frequencytransformer = FunctionTransformer(
    func=calc_frequency,
    feature_names_out=lambda self, input_features: [
        x + "Frequency" for x in input_features
    ],
)

datetime_transformer = FunctionTransformer(
    lambda x: pd.DataFrame(x.astype("int64") // 10**9),
    validate=False,
    feature_names_out=lambda self, feature_names_in: pd.Index(["start_time"]),
)
simple_imputer = SimpleImputer(
    strategy="constant", fill_value=-10, missing_values=pd.NA
)


# pylint: disable=unused-argument,attribute-defined-outside-init,invalid-name
class ColumnSelector(BaseEstimator, TransformerMixin):
    """Allow feature selection by name in GridSearch"""

    def __init__(self, columns):
        self.columns = columns

    def fit(self, X, y=None):
        """Fit"""
        if self.columns == "all":
            self.columns_ = X.columns.tolist()
        else:
            self.columns_ = self.columns
        return self

    def transform(self, X):
        """Transform"""
        return X[self.columns_]

    def get_feature_names_out(self, input_features=None):
        """Return feature names"""
        return self.columns_


class LetterProbabilityTransformer(BaseEstimator, TransformerMixin):
    """Calculate likelyness of missing letter between two others"""

    def fit(self, X, y=None):
        """Fit"""
        self.column_names_ = X.columns
        return self

    @staticmethod
    def extract_letters(row):
        """Find letters before, being and directly after missing letter"""
        index = row["missing_letter_index"]
        if pd.isna(index):
            return pd.Series([pd.NA] * 3)
        answer = row["answer"]

        letter_before = answer[index - 1] if index > 0 else "_"
        letter_missing = answer[index]
        letter_after = answer[index + 1] if index < len(answer) - 1 else "_"

        return pd.Series(
            [letter_before, letter_missing, letter_after],
            index=["LetterBefore", "LetterMissing", "LetterAfter"],
        )

    def transform(self, X):
        """Transform"""
        df_ps = X.query("IsTaartpuzzel == 0").copy()
        df_tp = X.query("IsTaartpuzzel == 1").copy()
        if df_tp.empty:
            new_col = pd.Series(name="MaxPercentageProbableLetter")
            return pd.concat([df_ps, new_col], axis="columns")
        relevant_letters = df_tp.apply(self.extract_letters, axis=1)

        relevant_letters_probs = relevant_letters.merge(
            odds[["PercentageSecondLetterGivenFirst"]],
            how="left",
            left_on=["LetterBefore", "LetterMissing"],
            right_index=True,
        ).merge(
            odds[["PercentageFirstLetterGivenSecond"]],
            how="left",
            left_on=["LetterMissing", "LetterAfter"],
            right_index=True,
        )

        df_tp["MaxPercentageProbableLetter"] = (
            relevant_letters_probs[
                ["PercentageSecondLetterGivenFirst", "PercentageFirstLetterGivenSecond"]
            ]
            .max("columns")
            .fillna(1)
        )
        result = pd.concat([df_tp, df_ps]).loc[X.index]
        return result

    def get_feature_names_out(self, input_features=None):
        "Return feature names"
        return self.column_names_.tolist() + ["MaxPercentageProbableLetter"]


# pylint: enable=unused-argument,attribute-defined-outside-init,invalid-name

ct = ColumnTransformer(
    [
        ("DirectionTransformer", directiontransformer, "answer"),
        ("WordBoundaryTransformer", wordboundarytransformer, "answer"),
        ("FrequencyTransformer", frequencytransformer, "answer"),
        ("DatetimeTransformer", datetime_transformer, "start_time"),
    ],
    remainder="passthrough",
    force_int_remainder_cols=False,
)

rf = RandomForestClassifier(
    n_estimators=100, max_depth=3, min_samples_leaf=5, random_state=42, n_jobs=-1
)
minimal_columns = [
    "remainder__NTimesWordSeenBefore",
    "DirectionTransformer__answerDirectionLogical",
    "WordBoundaryTransformer__answerBoundaryLogical",
    "remainder__IsTaartpuzzel",
    "remainder__MaxPercentageProbableLetter",
]


column_selector = ColumnSelector("all")

pipe = Pipeline(
    [
        ("missing_letter_prep", LetterProbabilityTransformer()),
        ("imputer", simple_imputer),
        ("text_prep", ct),
        ("columnselection", column_selector),
        ("clf", rf),
    ]
)
pipe.set_output(transform="pandas")
param_grid = {
    "columnselection__columns": [minimal_columns, "all"],
    "clf__max_depth": [3, 8],
    "clf__min_samples_leaf": [2, 5, 10],
}

grid = GridSearchCV(
    pipe, param_grid, scoring="roc_auc", verbose=3, return_train_score=True
)
