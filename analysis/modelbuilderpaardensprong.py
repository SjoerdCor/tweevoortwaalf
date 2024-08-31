"""Create the pipeline for fitting paardensprongen"""

import importlib.resources
from functools import wraps

import pandas as pd
from sklearn.base import BaseEstimator, TransformerMixin
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestClassifier
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.model_selection import GridSearchCV
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import FunctionTransformer

DATA_PATH = importlib.resources.files("tweevoortwaalf.Data").joinpath(
    "suitable_8_letter_words.txt"
)
eightletterwords = pd.read_csv(DATA_PATH, header=None).squeeze()
eightlettervectorizer = CountVectorizer(analyzer="char", ngram_range=(2, 2))
eightlettervectorizer.fit(eightletterwords)
ngrams_occurences_total = (
    eightlettervectorizer.transform(eightletterwords).toarray().sum(axis=0)
)

wordlist = pd.read_csv("../tweevoortwaalf/Data/wordlist.csv")
# There are some duplicates in Word for words including ij, where one occurs very infrequently
frequency = wordlist.query("Length == 8").groupby("Word")["Frequency"].max().dropna()


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

ct = ColumnTransformer(
    [
        ("DirectionTransformer", directiontransformer, "answer"),
        ("WordBoundaryTransformer", wordboundarytransformer, "answer"),
        ("FrequencyTransformer", frequencytransformer, "answer"),
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
]


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


# pylint: enable=unused-argument,attribute-defined-outside-init,invalid-name

column_selector = ColumnSelector("all")

pipe = Pipeline([("text_prep", ct), ("columnselection", column_selector), ("clf", rf)])
pipe.set_output(transform="pandas")
param_grid = {
    "columnselection__columns": [minimal_columns, "all"],
    "clf__max_depth": [3, 8],
    "clf__min_samples_leaf": [2, 5, 10],
}

grid = GridSearchCV(
    pipe, param_grid, scoring="roc_auc", verbose=3, return_train_score=True
)
