from typing import Literal, Final
from abc import ABC, abstractmethod
from random import randint
from typing import NamedTuple

type Gender = Literal["M", "F"]
NAME_LENGTH: Final[int] = 10

class Scores(NamedTuple):
    husband_wife: float
    brother_sister: float
    brother_brother: float
    sister_sister: float
    son_father: float
    daughter_father: float
    son_mother: float
    daughter_mother: float

# -------------------------------------------------------------------------------

class Scheme(ABC):

    @staticmethod
    @abstractmethod
    def get_child_name(
        father_name: str, mother_name: str, child_gender: Gender
    ) -> str:
        ...

    @staticmethod
    @abstractmethod
    def get_marital_name(
        original_name: str, spouse_original_name: str, self_gender: Gender
    ) -> str:
        ...

    @staticmethod
    @abstractmethod
    def stable_num_components_at_birth(gender: Gender) -> int:
        ...

# -------------------------------------------------------------------------------

def get_components(name: str) -> list[str]:
    return name.split("-")

def is_valid_name(name: str) -> bool:
    components: list[str] = get_components(name)
    return 1 <= len(components) <= 2 and all(len(component) >= 1 for component in components)

def get_score(name_1: str, name_2: str, p: float = 0.5) -> float:
    assert is_valid_name(name_1) and is_valid_name(name_2) and 0 <= p <= 1
    name_1_components: list[str] = get_components(name_1)
    name_2_components: list[str] = get_components(name_2)
    if name_1_components == name_2_components:
        return 1
    elif len(set(name_1_components) & set(name_2_components)) >= 1:
        return p
    else:
        return 0

def get_score_birth_and_married(
    name_1_birth: str, name_1_married: str,
    name_2_birth: str, name_2_married: str,
    p: float = 0.5
) -> float:
    return (
        get_score(name_1_birth, name_2_birth, p) +
        get_score(name_1_married, name_2_married, p)
    ) / 2

def marry(husband: str, wife: str, scheme: type[Scheme]) -> tuple[str, str]:
    husband_original_name: str = husband
    wife_original_name: str = wife
    husband_new_name: str = scheme.get_marital_name(husband_original_name, wife_original_name, "M")
    wife_new_name: str = scheme.get_marital_name(wife_original_name, husband_original_name, "F")
    return (husband_new_name, wife_new_name)

def random_component(already_used_components: set[str]) -> str:
    while True:
        name: str = "".join(chr(randint(ord("a"), ord("z"))) for i in range(NAME_LENGTH))
        if name not in already_used_components:
            already_used_components.add(name)
            return name

def random_name(already_used_components: set[str], num_components: int = 1) -> str:
    assert 1 <= num_components <= 2
    return "-".join(random_component(already_used_components) for i in range(num_components))

# -------------------------------------------------------------------------------

def evaluate_scheme(scheme: type[Scheme], p: float = 0.5) -> Scores:

    def r(gender: Gender) -> str:
        return random_name(already_used_components, scheme.stable_num_components_at_birth(gender))

    assert 0 <= p <= 1
    already_used_components: set[str] = set()

    father_birth: str = r("M")
    mother_birth: str = r("F")
    father_married, mother_married = marry(father_birth, mother_birth, scheme)
    husband_wife_score: float = get_score(father_married, mother_married, p)

    son_1_birth: str = scheme.get_child_name(father_married, mother_married, "M")
    son_2_birth: str = scheme.get_child_name(father_married, mother_married, "M")
    daughter_1_birth: str = scheme.get_child_name(father_married, mother_married, "F")
    daughter_2_birth: str = scheme.get_child_name(father_married, mother_married, "F")

    son_1_wife_birth: str = r("F")
    son_2_wife_birth: str = r("F")
    daughter_1_husband_birth: str = r("M")
    daughter_2_husband_birth: str = r("M")

    son_1_married, _ = marry(son_1_birth, son_1_wife_birth, scheme)
    son_2_married, _ = marry(son_2_birth, son_2_wife_birth, scheme)
    _, daughter_1_married = marry(daughter_1_husband_birth, daughter_1_birth, scheme)
    _, daughter_2_married = marry(daughter_2_husband_birth, daughter_2_birth, scheme)

    brother_sister_score: float = get_score_birth_and_married(
        son_1_birth, son_1_married, daughter_1_birth, daughter_1_married, p
    )
    brother_brother_score: float = get_score_birth_and_married(
        son_1_birth, son_1_married, son_2_birth, son_2_married, p
    )
    sister_sister_score: float = get_score_birth_and_married(
        daughter_1_birth, daughter_1_married, daughter_2_birth, daughter_2_married, p
    )

    son_father_score: float = get_score_birth_and_married(
        son_1_birth, son_1_married, father_married, father_married, p
    )
    daughter_father_score: float = get_score_birth_and_married(
        daughter_1_birth, daughter_1_married, father_married, father_married, p
    )
    son_mother_score: float = get_score_birth_and_married(
        son_1_birth, son_1_married, mother_married, mother_married, p
    )
    daughter_mother_score: float = get_score_birth_and_married(
        daughter_1_birth, daughter_1_married, mother_married, mother_married, p
    )

    return Scores(
        husband_wife_score, brother_sister_score, brother_brother_score, sister_sister_score,
        son_father_score, daughter_father_score, son_mother_score, daughter_mother_score
    )