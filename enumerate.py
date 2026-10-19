from import_export import *
from typing import NamedTuple, Callable
from tqdm import tqdm
import pandas as pd

type GetNameNoGender = Callable[[str, str], str]
type GetName = Callable[[str, str, Gender], str]
type ComponentSelector = Callable[[list[str]], list[str]]
type SpecToSelectors = Callable[
    [Spec], tuple[list[ComponentSelector], list[ComponentSelector]]
]

class Spec(NamedTuple):

    male_birth: int
    female_birth: int
    male_married: int
    female_married: int

    @staticmethod
    def make(n: int) -> Spec:
        assert 0 <= n <= 15
        return Spec(*[int(bit) + 1 for bit in f"{n:04b}"])

# -------------------------------------------------------------------------------

def make_one_name_func_no_gender(
    component_selector: ComponentSelector
) -> GetNameNoGender:
    def name_func(name_1: str, name_2: str) -> str:
        components: list[str] = \
            list(dict.fromkeys(get_components(name_1) + get_components(name_2)))
        return "-".join(component_selector(components))
    return name_func

def make_component_selector(indices: list[int]) -> ComponentSelector:
    assert 1 <= len(indices) <= 2
    def component_selector(all_components: list[str]) -> list[str]:
        return [all_components[i] for i in indices]
    return component_selector

def make_component_selectors(
    total_input_components: int, result_components: int
) -> list[ComponentSelector]:
    assert 1 <= result_components <= 2 and 1 <= total_input_components <= 4
    indices_candidates: list[list[int]] = []
    if result_components == 1:
        indices_candidates.extend([i] for i in range(total_input_components))
    elif result_components == 2:
        indices_candidates.extend(
            [i, j]
            for i in range(total_input_components)
            for j in range(total_input_components)
            if i != j
        )
    return [make_component_selector(indices) for indices in indices_candidates]

def all_component_selectors(
    total_input_components: int, male_result_components: int, female_result_components: int
) -> tuple[list[ComponentSelector], list[ComponentSelector]]:
    male_selectors: list[ComponentSelector] = \
        make_component_selectors(total_input_components, male_result_components)
    female_selectors: list[ComponentSelector] = \
        make_component_selectors(total_input_components, female_result_components)
    return (male_selectors, female_selectors)

def all_marital_component_selectors(
    spec: Spec
) -> tuple[list[ComponentSelector], list[ComponentSelector]]:
    return all_component_selectors(
        total_input_components = spec.male_birth + spec.female_birth,
        male_result_components = spec.male_married,
        female_result_components = spec.female_married
    )

def get_total_marital_components(spec: Spec, marital_name_func: GetName) -> int:
    already_used_components: set[str] = set()
    husband_birth_name: str = random_name(already_used_components, spec.male_birth)
    wife_birth_name: str = random_name(already_used_components, spec.female_birth)
    husband_marital_name: str = marital_name_func(husband_birth_name, wife_birth_name, "M")
    wife_marital_name: str = marital_name_func(wife_birth_name, husband_birth_name, "F")
    husband_components: list[str] = get_components(husband_marital_name)
    wife_components: list[str] = get_components(wife_marital_name)
    assert (
        len(husband_components) == spec.male_married and
        len(wife_components) == spec.female_married
    )
    return len(set(husband_components) | set(wife_components))

def all_children_component_selectors(marital_name_func: GetName) -> SpecToSelectors:
    def selectors_func(
        spec: Spec
    ) -> tuple[list[ComponentSelector], list[ComponentSelector]]:
        return all_component_selectors(
            total_input_components = get_total_marital_components(spec, marital_name_func),
            male_result_components = spec.male_birth,
            female_result_components = spec.female_birth
        )
    return selectors_func

def enumerate_male_female_possibilities(
    spec: Spec, component_selectors_func: SpecToSelectors
) -> tuple[list[GetNameNoGender], list[GetNameNoGender]]:
    male_selectors, female_selectors = component_selectors_func(spec)
    male_possibilities: list[GetNameNoGender] = \
        [make_one_name_func_no_gender(selector) for selector in male_selectors]
    female_possibilities: list[GetNameNoGender] = \
        [make_one_name_func_no_gender(selector) for selector in female_selectors]
    return (male_possibilities, female_possibilities)

def combine_male_female_possibility(
    male_func: GetNameNoGender, female_func: GetNameNoGender
) -> GetName:
    def name_func(name_1: str, name_2: str, gender: Gender) -> str:
        return male_func(name_1, name_2) if gender == "M" else female_func(name_1, name_2)
    return name_func

def enumerate_possibilities(
    spec: Spec, component_selectors_func: SpecToSelectors
) -> list[GetName]:
    male_possibilities, female_possibilities = \
        enumerate_male_female_possibilities(spec, component_selectors_func)
    return [
        combine_male_female_possibility(male_func, female_func)
        for male_func in male_possibilities
        for female_func in female_possibilities
    ]

def stable_num_components_at_birth(spec: Spec) -> Callable[[Gender], int]:
    return lambda gender: spec.male_birth if gender == "M" else spec.female_birth

def enumerate_all_schemes() -> list[type[Scheme]]:
    specs: list[Spec] = [Spec.make(i) for i in range(16)]
    schemes: list[type[Scheme]] = []
    scheme_id: int = 1
    for spec in tqdm(specs):
        marital_name_funcs: list[GetName] = \
            enumerate_possibilities(spec, all_marital_component_selectors)
        for marital_name_func in marital_name_funcs:
            child_name_funcs: list[GetName] = \
                enumerate_possibilities(spec, all_children_component_selectors(marital_name_func))
            for child_name_func in child_name_funcs:
                num_components_at_birth: Callable[[Gender], int] = \
                    stable_num_components_at_birth(spec)
                scheme: type[Scheme] = type(f"Scheme{scheme_id}", (Scheme,), {
                    "get_child_name": staticmethod(child_name_func),
                    "get_marital_name": staticmethod(marital_name_func),
                    "stable_num_components_at_birth": staticmethod(num_components_at_birth)
                })
                scheme_id += 1
                schemes.append(scheme)
    return schemes

def run() -> None:
    schemes: list[type[Scheme]] = enumerate_all_schemes()
    print(f"{len(schemes) = }")
    data: list[tuple[str, *tuple[float | str, ...]]] = [
        (scheme.__name__, *evaluate_scheme(scheme), *export_scheme_to_family(scheme))
        for scheme in tqdm(schemes)
    ]
    df = pd.DataFrame(data, columns = ("scheme",) + Scores._fields + Family._fields)
    df.to_csv("data/schemes.csv", index = False)

# -------------------------------------------------------------------------------

if __name__ == "__main__":
    run()