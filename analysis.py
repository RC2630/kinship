import pandas as pd
from enumerate import *

# ----------------------------------------------------------------------

df = pd.read_csv("data/schemes.csv")
len(df)

# ----------------------------------------------------------------------

df.head()

# ----------------------------------------------------------------------

score_columns: list[str] = list(Scores._fields)
df["score"] = df.apply(lambda row: row[score_columns].sum(), axis = 1)
df.head()

# ----------------------------------------------------------------------

df.score.max()

# ----------------------------------------------------------------------

df.groupby("score")[["scheme"]].count().rename(columns = dict(scheme = "num_schemes"))

# ----------------------------------------------------------------------

len(df[score_columns].drop_duplicates())

# ----------------------------------------------------------------------

df[df.score == 6.25]

# ----------------------------------------------------------------------

distinct_scores: pd.DataFrame = (
    df.groupby(score_columns, as_index = False)
    .scheme.count()
    .sort_values("scheme", ascending = False) # type: ignore
)

distinct_scores.head()

# ----------------------------------------------------------------------

distinct_scores.scheme.describe()

# ----------------------------------------------------------------------

from collections import Counter
from functools import reduce

counts: dict[int, int] = Counter(distinct_scores.scheme)
print(counts)

reduce(lambda sum, curr: sum + curr[0] * curr[1], counts.items(), 0)

# ----------------------------------------------------------------------

{k: v for k, v in counts.items() if k % 2 == 1}

# ----------------------------------------------------------------------

len(counts)

# ----------------------------------------------------------------------

print({2 ** i: sum(v for k, v in counts.items() if k % (2 ** i) == 0) for i in range(10)})

# ----------------------------------------------------------------------

odds: pd.DataFrame = distinct_scores[distinct_scores.scheme % 2 == 1]
odd_scores: list[Iterable[float]] = list(odds[score_columns].to_numpy())
score_to_multiplicity: dict[tuple[float, ...], int] = \
    {tuple(odd_scores[i]): odds.scheme.iloc[i] for i in range(len(odds))}

odd_df: pd.DataFrame = df[df.set_index(score_columns).index.isin(odd_scores)]

# ----------------------------------------------------------------------

odd_df["multiplicity"] = 0
for i in odd_df.index:
    odd_df.loc[i, "multiplicity"] = \
        score_to_multiplicity[tuple(odd_df.loc[i, score_columns])] # type: ignore

pd.set_option("display.max_rows", None)
odd_df.sort_values(["multiplicity"] + score_columns, inplace = True)

# ----------------------------------------------------------------------

odd_df = odd_df.reset_index(drop = True)
odd_df["group_id"] = odd_df.groupby(score_columns, sort = False).ngroup()
odd_df

# ----------------------------------------------------------------------

groups_df = odd_df.drop_duplicates(score_columns).reset_index()[score_columns + ["score", "multiplicity"]]
groups_df

# ----------------------------------------------------------------------

from helpers.pandas_util import *

class GenderSwapRow(NamedTuple):
    swapped_family_id: int
    original_group_id: int
    swapped_group_id: int
    multiplicity: int
    score: float

families: list[Family] = import_families_from_dataframe(odd_df)
gender_swap_data: list[GenderSwapRow] = []

for i, family in enumerate(families):
    swapped_family_id: int = families.index(family.gender_swap())
    original_group_id: int = odd_df.loc[i, "group_id"].item() # type: ignore
    swapped_group_id: int = odd_df.loc[swapped_family_id, "group_id"].item() # type: ignore
    multiplicity: int = groups_df.loc[original_group_id, "multiplicity"].item() # type: ignore
    assert multiplicity == groups_df.loc[swapped_group_id, "multiplicity"].item() # type: ignore
    score: float = groups_df.loc[original_group_id, "score"].item() # type: ignore
    assert score == groups_df.loc[swapped_group_id, "score"].item() # type: ignore
    gender_swap_data.append(GenderSwapRow(swapped_family_id, original_group_id, swapped_group_id, multiplicity, score))

gender_swap_df = build_df_from_named_tuples(gender_swap_data)
gender_swap_df.index.rename("original_family_id", inplace = True)

gender_swap_df

# ----------------------------------------------------------------------

gender_swap_df[gender_swap_df.original_group_id == gender_swap_df.swapped_group_id]

# ----------------------------------------------------------------------

gender_swap_df[gender_swap_df.index == gender_swap_df.swapped_family_id]

# ----------------------------------------------------------------------

print(list(enumerate(distinct_scores.scheme.head(30))))

# ----------------------------------------------------------------------

schemes: list[type[Scheme]] = \
    import_schemes_from_dataframe(df.loc[:, Family._fields], df.scheme) # type: ignore

[scheme.__name__ for scheme in schemes[:5]]

# ----------------------------------------------------------------------

target_family = Family(
    father_birth = "A-B",
    father_married = "A-D",
    mother_birth = "C-D",
    mother_married = "A-D",
    son_birth = "A-D",
    daughter_birth = "A-D"
)

if any(
    (target_index := i) == i and export_scheme_to_family(scheme) == target_family
    for i, scheme in enumerate(schemes)
):
    print(target_index)

# ----------------------------------------------------------------------

df.iloc[target_index]

# ----------------------------------------------------------------------

df[df.score == 6]

# ----------------------------------------------------------------------

from schemes import *

schemes: set[type[Scheme]] = {
    value for value in globals().values()
    if isinstance(value, type) and issubclass(value, Scheme) and value is not Scheme
    and not value.__name__.startswith("Scheme_")
}

schemes

# ----------------------------------------------------------------------

COLUMNS: list[str] = list(Family._fields)
VALUES: list[list[str]] = [list(export_scheme_to_family(scheme)) for scheme in schemes]

manual_schemes: pd.DataFrame = df[df.set_index(COLUMNS).index.isin(VALUES)]
manual_schemes

# ----------------------------------------------------------------------

manual_schemes["manual"] = [[] for i in range(len(manual_schemes))]

for i in manual_schemes.index:
    row_scheme: type[Scheme] = import_scheme_from_dataframe_row_index(manual_schemes, i)
    for scheme in schemes:
        if export_scheme_to_family(scheme) == export_scheme_to_family(row_scheme):
            manual_schemes.loc[i, "manual"].append(scheme.__name__)

manual_schemes