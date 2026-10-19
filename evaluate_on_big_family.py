from generate_family import *
from statistics import mean, pstdev, quantiles

class EvaluationRecord(NamedTuple):
    mean: float
    std: float
    min: float
    quartile_1: float
    median: float
    quartile_3: float
    max: float

def distances_to_all_people(person: Person) -> dict[Person, int]:
    frontier: deque[Person] = deque([person])
    distances: dict[Person, int] = {person: 0}
    while len(frontier) > 0:
        curr: Person = frontier.popleft()
        for p in (
            [*curr.parents, *curr.siblings, *curr.children] +
            ([curr.spouse] if curr.spouse is not None else [])
        ):
            if p not in distances:
                distances[p] = distances[curr] + 1
                frontier.append(p)
    return distances

def get_path_and_genetic_similarity_scores() -> dict[tuple[Person, Person], tuple[float, float]]:
    path_and_genetic_scores: dict[tuple[Person, Person], tuple[float, float]] = {}
    people: list[Person] = list(PEOPLE.values())
    for i, p1 in enumerate(people):
        dists: dict[Person, int] = distances_to_all_people(p1)
        for p2 in people[i + 1:]:
            rel: float = relatedness(p1, p2)
            genetic_score: float = 2 * rel if p1 is not p2 else 1
            if p2 not in dists:
                path_and_genetic_scores[p1, p2] = (0, genetic_score)
            else:
                dist: int = dists[p2]
                path_and_genetic_scores[p1, p2] = (1 / dist if dist > 0 else 1, genetic_score)
    return path_and_genetic_scores

def get_married_surname_if_married(person: Person) -> str:
    try:
        return get_married_surname(person.name)
    except IndexError:
        return get_birth_surname(person.name)

def calculate_surname_score(p1: Person, p2: Person) -> float:
    scores: list[float] = [
        get_score(get_birth_surname(p1.name), get_birth_surname(p2.name)),
        get_score(get_birth_surname(p1.name), get_married_surname_if_married(p2)),
        get_score(get_married_surname_if_married(p1), get_birth_surname(p2.name)),
        get_score(get_married_surname_if_married(p1), get_married_surname_if_married(p2))
    ]
    return 0.75 * max(scores) + 0.25 * mean(scores)

def calculate_loss(surname_score: float, path_score: float, genetic_score: float) -> float:
    weight: float = (path_score + genetic_score) / 2 + 0.1
    return (
        abs(surname_score - path_score) ** 1.5 +
        abs(surname_score - genetic_score) ** 1.5
    ) * weight

def evaluate_scheme_on_family(
    scheme: type[Scheme],
    family_metadata: FamilyMetadata,
    path_and_genetic_similarity_scores: dict[tuple[Person, Person], tuple[float, float]]
) -> EvaluationRecord:
    add_surnames(scheme, family_metadata.events, family_metadata.used_components)
    losses: list[float] = []
    for (p1, p2), (path_score, genetic_score) in path_and_genetic_similarity_scores.items():
        surname_score: float = calculate_surname_score(p1, p2)
        loss: float = calculate_loss(surname_score, path_score, genetic_score)
        losses.append(loss)
    return EvaluationRecord(
        mean(losses), pstdev(losses), min(losses),
        *quantiles(losses, method = "inclusive"), max(losses) # type: ignore
    )

def get_schemes(threshold: float) -> list[type[Scheme]]:
    epsilon: float = 1e-6
    df: pd.DataFrame = pd.read_csv("data/schemes.csv")
    df["score"] = df[list(Scores._fields)].sum(axis = 1)
    schemes: list[type[Scheme]] = import_schemes_from_dataframe(df)
    return [
        schemes[i] for i in range(len(schemes))
        if df.loc[i, "score"] >= threshold - epsilon # type: ignore
    ]

def run_evaluation(
    num_founders: int, num_additional: int, threshold: float, csv_file_name: str
) -> None:
    schemes: list[type[Scheme]] = get_schemes(threshold)
    family_metadata: FamilyMetadata = generate_family(num_founders, num_additional)
    results: dict[type[Scheme], EvaluationRecord] = {}
    path_and_genetic_similarity_scores: dict[tuple[Person, Person], tuple[float, float]] = \
        get_path_and_genetic_similarity_scores()
    for scheme in tqdm(schemes, "evaluating schemes"):
        results[scheme] = evaluate_scheme_on_family(
            scheme, family_metadata, path_and_genetic_similarity_scores
        )
    data: list[list[float | str]] = []
    for scheme, record in results.items():
        data.append([*record, *export_scheme_to_family(scheme)])
    df = pd.DataFrame(data, columns = [*EvaluationRecord._fields, *Family._fields])
    df.to_csv(f"data/{csv_file_name}", index = False)

if __name__ == "__main__":
    run_evaluation(50, 950, 5, "big_family_results_5.csv")