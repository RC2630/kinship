from surnames import *
from typing import override

class AnglophoneTraditional(Scheme):

    @override
    @staticmethod
    def get_child_name(
        father_name: str, mother_name: str, child_gender: Gender
    ) -> str:
        return father_name

    @override
    @staticmethod
    def get_marital_name(
        original_name: str, spouse_original_name: str, self_gender: Gender
    ) -> str:
        return original_name if self_gender == "M" else spouse_original_name

    @override
    @staticmethod
    def stable_num_components_at_birth(gender: Gender) -> int:
        return 1

# -------------------------------------------------------------------------------

class ChineseTraditional(Scheme):

    @override
    @staticmethod
    def get_child_name(
        father_name: str, mother_name: str, child_gender: Gender
    ) -> str:
        return father_name

    @override
    @staticmethod
    def get_marital_name(
        original_name: str, spouse_original_name: str, self_gender: Gender
    ) -> str:
        return original_name

    @override
    @staticmethod
    def stable_num_components_at_birth(gender: Gender) -> int:
        return 1

# -------------------------------------------------------------------------------

class Symmetric(Scheme):

    @override
    @staticmethod
    def get_child_name(
        father_name: str, mother_name: str, child_gender: Gender
    ) -> str:
        return father_name if child_gender == "M" else mother_name

    @override
    @staticmethod
    def get_marital_name(
        original_name: str, spouse_original_name: str, self_gender: Gender
    ) -> str:
        return original_name

    @override
    @staticmethod
    def stable_num_components_at_birth(gender: Gender) -> int:
        return 1

# -------------------------------------------------------------------------------

class StarWars(Scheme):

    @override
    @staticmethod
    def get_child_name(
        father_name: str, mother_name: str, child_gender: Gender
    ) -> str:
        return father_name

    @override
    @staticmethod
    def get_marital_name(
        original_name: str, spouse_original_name: str, self_gender: Gender
    ) -> str:
        return original_name if self_gender == "M" else f"{original_name}-{spouse_original_name}"

    @override
    @staticmethod
    def stable_num_components_at_birth(gender: Gender) -> int:
        return 1

# -------------------------------------------------------------------------------

class Matrilineal(Scheme):

    @override
    @staticmethod
    def get_child_name(
        father_name: str, mother_name: str, child_gender: Gender
    ) -> str:
        return mother_name

    @override
    @staticmethod
    def get_marital_name(
        original_name: str, spouse_original_name: str, self_gender: Gender
    ) -> str:
        return original_name

    @override
    @staticmethod
    def stable_num_components_at_birth(gender: Gender) -> int:
        return 1

# -------------------------------------------------------------------------------

class SpanishTraditional(Scheme):

    @override
    @staticmethod
    def get_child_name(
        father_name: str, mother_name: str, child_gender: Gender
    ) -> str:
        return f"{get_components(father_name)[0]}-{get_components(mother_name)[0]}"

    @override
    @staticmethod
    def get_marital_name(
        original_name: str, spouse_original_name: str, self_gender: Gender
    ) -> str:
        return original_name

    @override
    @staticmethod
    def stable_num_components_at_birth(gender: Gender) -> int:
        return 2

# -------------------------------------------------------------------------------

class DualLineage(Scheme):

    @override
    @staticmethod
    def get_child_name(
        father_name: str, mother_name: str, child_gender: Gender
    ) -> str:
        return f"{get_components(father_name)[0]}-{get_components(mother_name)[1]}"

    @override
    @staticmethod
    def get_marital_name(
        original_name: str, spouse_original_name: str, self_gender: Gender
    ) -> str:
        return original_name

    @override
    @staticmethod
    def stable_num_components_at_birth(gender: Gender) -> int:
        return 2

# -------------------------------------------------------------------------------

class MatrilinealMarriage(Scheme):

    @override
    @staticmethod
    def get_child_name(
        father_name: str, mother_name: str, child_gender: Gender
    ) -> str:
        return mother_name

    @override
    @staticmethod
    def get_marital_name(
        original_name: str, spouse_original_name: str, self_gender: Gender
    ) -> str:
        return original_name if self_gender == "F" else spouse_original_name

    @override
    @staticmethod
    def stable_num_components_at_birth(gender: Gender) -> int:
        return 1

# -------------------------------------------------------------------------------

class JointFamily(Scheme):

    @override
    @staticmethod
    def get_child_name(
        father_name: str, mother_name: str, child_gender: Gender
    ) -> str:
        return father_name

    @override
    @staticmethod
    def get_marital_name(
        original_name: str, spouse_original_name: str, self_gender: Gender
    ) -> str:
        return (
            f"{get_components(original_name)[0]}-{get_components(spouse_original_name)[0]}"
            if self_gender == "M"
            else f"{get_components(spouse_original_name)[0]}-{get_components(original_name)[0]}"
        )

    @override
    @staticmethod
    def stable_num_components_at_birth(gender: Gender) -> int:
        return 2

# -------------------------------------------------------------------------------

class DoubleSurname(Scheme):

    @override
    @staticmethod
    def get_child_name(
        father_name: str, mother_name: str, child_gender: Gender
    ) -> str:
        return father_name

    @override
    @staticmethod
    def get_marital_name(
        original_name: str, spouse_original_name: str, self_gender: Gender
    ) -> str:
        if len(set(get_components(original_name))) == 1:
            return original_name
        elif len(set(get_components(spouse_original_name))) == 1:
            return spouse_original_name
        else:
            husband_name: str = original_name if self_gender == "M" else spouse_original_name
            return "-".join(2 * [get_components(husband_name)[0]])

    @override
    @staticmethod
    def stable_num_components_at_birth(gender: Gender) -> int:
        return 2

# -------------------------------------------------------------------------------

class AlphabeticalPriority(Scheme):

    @override
    @staticmethod
    def get_child_name(
        father_name: str, mother_name: str, child_gender: Gender
    ) -> str:
        return father_name

    @override
    @staticmethod
    def get_marital_name(
        original_name: str, spouse_original_name: str, self_gender: Gender
    ) -> str:
        a: list[str] = get_components(original_name)
        b: list[str] = get_components(spouse_original_name)
        if a[0] < a[1] and b[0] >= b[1]:
            return original_name
        elif b[0] < b[1] and a[0] >= a[1]:
            return spouse_original_name
        return "-".join(sorted([a[0], b[0]] if self_gender == "M" else [b[0], a[0]]))

    @override
    @staticmethod
    def stable_num_components_at_birth(gender: Gender) -> int:
        return 2