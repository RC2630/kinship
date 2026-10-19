from typing import Final, override
import re
from sys import argv
from collections import deque
from helpers.colours import green, blue, red, yellow
from abc import ABC, abstractmethod
from functools import cache

INPUT_FILE: Final[str] = "files/input.md"
COMMON_NAMES_FILE: Final[str] = "files/common_names.txt"
PEOPLE: dict[str, Person] = {}
COMMON_NAMES: dict[tuple[str, ...], dict[str, str]] = {}

GENDERED_TERMS: dict[tuple[str, str], str] = {
    ("parent", "M"): "father", ("parent", "F"): "mother",
    ("child", "M"): "son", ("child", "F"): "daughter",
    ("sibling", "M"): "brother", ("sibling", "F"): "sister",
    ("spouse", "M"): "husband", ("spouse", "F"): "wife"
}

NUMBERED_REPRESENTATIONS: dict[str, list[int]] = {
    "parent": [1], "child": [-1], "sibling": [1, -1], "spouse": [-1, 1]
}

type Path = list[tuple[str, str]]

# ----------------------------------------------------------

class Person:

    FOUNDER_COUNTER: int = 1

    def __init__(self, name: str, gender: str, is_founder: bool = False) -> None:
        self.name: str = name
        self.gender: str = gender
        self.siblings: list[Person] = []
        self.parents: list[Person] = []
        self.children: list[Person] = []
        self.spouse: Person | None = None
        self.is_founder: bool = is_founder

    def add_relative(self, type: str, name: str) -> None:
        if type == "child":
            self.children.append(PEOPLE[name])
            PEOPLE[name].parents.append(self)
        elif type == "sibling":
            self.siblings.append(PEOPLE[name])
            PEOPLE[name].siblings.append(self)
        elif type == "parent":
            self.parents.append(PEOPLE[name])
            PEOPLE[name].children.append(self)
        elif type == "spouse":
            if self.spouse is not None or PEOPLE[name].spouse is not None:
                raise ValueError("at least 1 member of this couple already has a spouse")
            self.spouse = PEOPLE[name]
            PEOPLE[name].spouse = self
        else:
            raise ValueError("invalid relative type")
        
    def get_gen(self) -> int:
        path: Path | None = self.find(list(PEOPLE.items())[0][1])
        assert path is not None
        return generational_difference(path)
        
    def __repr__(self) -> str:
        return remove_leading_whitespaces(
            f"""{green(self.name)} ({blue(self.gender)}, gen {blue(str(self.get_gen()))})
            - {blue('parents:')} {display_people_list(self.parents)}
            - {blue('siblings:')} {display_people_list(self.siblings)}
            - {blue('spouse:')} {green(self.spouse.name) if self.spouse else red('(N/A)')}
            - {blue('children:')} {display_people_list(self.children)}"""
        )
        
    def display_without_founders(self) -> str:
        named_parents: list[Person] = [parent for parent in self.parents if not parent.is_founder]
        return remove_leading_whitespaces(
            f"""{green(self.name)} ({blue(self.gender)}, gen {blue(str(self.get_gen()))})
            - {blue('parents:')} {display_people_list(named_parents)}
            - {blue('siblings:')} {display_people_list(self.siblings)}
            - {blue('spouse:')} {green(self.spouse.name) if self.spouse else red('(N/A)')}
            - {blue('children:')} {display_people_list(self.children)}"""
        )
    
    def find(self, other: Person) -> Path | None:
        frontier: deque[tuple[Person, Path]] = deque([(self, [])])
        already_appended: set[str] = {self.name}
        while len(frontier) > 0:
            curr_person, curr_path = frontier.popleft()
            if curr_person.name == other.name:
                return curr_path
            if (spouse := curr_person.spouse) is not None:
                if spouse.name not in already_appended:
                    frontier.append((spouse, curr_path + [("spouse", spouse.name)]))
                    already_appended.add(spouse.name)
            for child in curr_person.children:
                if child.name not in already_appended:
                    frontier.append((child, curr_path + [("child", child.name)]))
                    already_appended.add(child.name)
            for parent in curr_person.parents:
                if parent.name not in already_appended:
                    frontier.append((parent, curr_path + [("parent", parent.name)]))
                    already_appended.add(parent.name)
            for sibling in curr_person.siblings:
                if sibling.name not in already_appended:
                    frontier.append((sibling, curr_path + [("sibling", sibling.name)]))
                    already_appended.add(sibling.name)
        return None

    def add_founders(self) -> None:
        has_father: bool = any(parent.gender == "M" for parent in self.parents)
        has_mother: bool = any(parent.gender == "F" for parent in self.parents)
        if not has_father:
            father_name: str = f"Founder #{Person.FOUNDER_COUNTER}"
            Person.FOUNDER_COUNTER += 1
            father = Person(father_name, "M", is_founder = True)
            PEOPLE[father_name] = father
            self.add_relative("parent", father_name)
            for sibling in self.siblings:
                sibling.add_relative("parent", father_name)
        if not has_mother:
            mother_name: str = f"Founder #{Person.FOUNDER_COUNTER}"
            Person.FOUNDER_COUNTER += 1
            mother = Person(mother_name, "F", is_founder = True)
            PEOPLE[mother_name] = mother
            self.add_relative("parent", mother_name)
            for sibling in self.siblings:
                sibling.add_relative("parent", mother_name)
        assert len(self.parents) == 2

    @cache
    def is_descendant_of(self, candidate_ancestor: Person) -> bool:
        if self.is_founder:
            return False
        if candidate_ancestor in self.parents:
            return True
        return self.parents[0].is_descendant_of(candidate_ancestor) or \
               self.parents[1].is_descendant_of(candidate_ancestor)

# ----------------------------------------------------------

def parse_input_file() -> None:
    
    with open(INPUT_FILE, "r", encoding = "utf-8") as f:
        lines: list[str] = f.read().split("\n")

    current_person: Person | None = None
    for line in lines:
        if line == "":
            current_person = None
        elif not line.startswith("- "):
            if m := re.match(r"(.+) \((.)\)", line):
                p = Person(name = m.group(1), gender = m.group(2))
                PEOPLE[m.group(1)] = p
                current_person = p
            else:
                raise ValueError("new person entry: format error")
        else:
            if m := re.match(r"- (.+): (.+)", line):
                assert current_person is not None
                current_person.add_relative(type = m.group(1), name = m.group(2))
            else:
                raise ValueError("relative entry: format error")

    autofill_siblings_and_parents()

    for person in list(PEOPLE.values()):
        assert not person.is_founder
        person.add_founders()

# ----------------------------------------------------------

def autofill_siblings_and_parents() -> None:
    changed: bool = autofill_one_round()
    while changed:
        changed = autofill_one_round()

def autofill_one_round() -> bool:
    ss: bool = autofill_siblings_from_siblings()
    ps: bool = autofill_parents_from_siblings()
    sp: bool = autofill_siblings_from_parents()
    return ss or ps or sp

def autofill_siblings_from_siblings() -> bool:
    changed: bool = False
    for person in PEOPLE.values():
        for sibling in person.siblings:
            for my_sibling in person.siblings:
                if my_sibling is not sibling and my_sibling not in sibling.siblings:
                    sibling.add_relative("sibling", my_sibling.name)
                    changed = True
    return changed

def autofill_parents_from_siblings() -> bool:
    changed: bool = False
    for person in PEOPLE.values():
        for sibling in person.siblings:
            for my_parent in person.parents:
                if my_parent not in sibling.parents:
                    sibling.add_relative("parent", my_parent.name)
                    changed = True
    return changed

def autofill_siblings_from_parents() -> bool:
    changed: bool = False
    for person in PEOPLE.values():
        if len(person.parents) != 2:
            continue
        candidate_siblings: list[Person] = [
            candidate for candidate in PEOPLE.values()
            if candidate is not person and set(person.parents) == set(candidate.parents)
        ]
        for sibling in candidate_siblings:
            if sibling not in person.siblings:
                person.add_relative("sibling", sibling.name)
                changed = True
    return changed

# ----------------------------------------------------------

def parse_common_names() -> None:
    with open(COMMON_NAMES_FILE, "r") as f:
        lines: list[str] = f.read().split("\n")
    for line in lines:
        if m := re.match(r"(.+) : (.+), (.+)", line):
            chain: tuple[str, ...] = tuple(m.group(1).split(" "))
            COMMON_NAMES[chain] = {}
            COMMON_NAMES[chain]["M"] = m.group(2)
            COMMON_NAMES[chain]["F"] = m.group(3)

def remove_leading_whitespaces(s: str) -> str:
    return "\n".join([line.lstrip() for line in s.split("\n")])

def display_people_list(people: list[Person]) -> str:
    if len(people) == 0:
        return red("(N/A)")
    return ", ".join(green(person.name) for person in people)

def reverse_path(path: Path, start: str) -> Path:
    reverse_mapping: dict[str, str] = {"child": "parent", "parent": "child"}
    relationships: list[str] = [reverse_mapping.get(rel, rel) for rel, name in reversed(path)]
    names: list[str] = [name for rel, name in reversed(path)][1:] + [start]
    return list(zip(relationships, names))

def display_all(include_founders: bool) -> None:
    if include_founders:
        for person in PEOPLE.values():
            print(f"\n{person}")
    else:
        for person in PEOPLE.values():
            if not person.is_founder:
                print(f"\n{person.display_without_founders()}")

def find_person_from_dict(key: str) -> Person:
    try:
        return next(
            person for name, person in PEOPLE.items()
            if name.lower() == key.lower()
        )
    except StopIteration:
        return next(
            person for name, person in PEOPLE.items()
            if name.lower().startswith(key.lower())
        )

def find_chain() -> None:
    try:
        name_1: str = input("\nEnter name of person 1: ")
        person_1: Person = find_person_from_dict(name_1)
        name_2: str = input("Enter name of person 2: ")
        person_2: Person = find_person_from_dict(name_2)
    except StopIteration:
        print("\nThere is no known person with the name you entered.")
        return
    chain: Path | None = person_1.find(person_2)
    if chain is None:
        print("\nThere is no chain of relationships connecting these two people.")
        return
    print(f"\nChain of relationships from {green(person_1.name)} to {green(person_2.name)}:")
    display_full_chain_info(chain, person_1, person_2)
    print(f"\nChain of relationships from {green(person_2.name)} to {green(person_1.name)}:")
    display_full_chain_info(reverse_path(chain, person_1.name), person_2, person_1)

def get_gendered(rel: str, name: str) -> str:
    return GENDERED_TERMS[(rel, PEOPLE[name].gender)]

def ordinal_number(n: int) -> str:
    s: str = str(n)
    if s.endswith(("11", "12", "13")):
        return s + "th"
    elif s.endswith("1"):
        return s + "st"
    elif s.endswith("2"):
        return s + "nd"
    elif s.endswith("3"):
        return s + "rd"
    else:
        return s + "th"
    
def multiplicative_number(n: int) -> str:
    if n == 1:
        return "once"
    elif n == 2:
        return "twice"
    elif n == 3:
        return "thrice"
    else:
        return f"{n} times"

# ----------------------------------------------------------

def compress_at(path: Path, start_index: int) -> Path:
    path[start_index] # raises IndexError if out of bounds
    end_index: int = len(path)
    while True:
        subpath: Path = path[start_index:end_index]
        if len(subpath) <= 1:
            return path
        subpath_rels: tuple[str, ...] = tuple(rel for rel, name in subpath)
        if subpath_rels not in COMMON_NAMES:
            end_index -= 1
            continue
        path_before: Path = path[:start_index]
        path_after: Path = path[end_index:]
        new_name: str = subpath[-1][1]
        new_rel: str = COMMON_NAMES[subpath_rels][PEOPLE[new_name].gender]
        return path_before + [(new_rel, new_name)] + path_after

def compress_one_round(path: Path) -> Path:
    index: int = 0
    while True:
        try:
            path = compress_at(path, index)
            index += 1
        except IndexError:
            return path

def compress_all_rounds(path: Path) -> Path:
    compressed: Path = compress_one_round(path)
    if compressed == path:
        return compressed
    else:
        return compress_all_rounds(compressed)
    
def compress(path: Path) -> Path:
    compressed: Path = compress_all_rounds(path)
    final_path: Path = []
    for rel, name in compressed:
        new_rel: str = GENDERED_TERMS.get((rel, PEOPLE[name].gender), rel)
        final_path.append((new_rel, name))
    return final_path

# ----------------------------------------------------------

def ungendered_with_names(chain: Path) -> str:
    return " -> ".join(f"{red(rel)} ({green(name)})" for rel, name in chain)

def ungendered_without_names(chain: Path) -> str:
    return " -> ".join(red(rel) for rel, name in chain)

def gendered_with_names(chain: Path) -> str:
    return " -> ".join(f"{red(get_gendered(rel, name))} ({green(name)})" for rel, name in chain)

def gendered_without_names(chain: Path) -> str:
    return " -> ".join(red(get_gendered(rel, name)) for rel, name in chain)

def numbered_representation(chain: Path) -> list[int]:
    numbered_repr: list[int] = []
    for rel, name in chain:
        curr_repr: list[int] = NUMBERED_REPRESENTATIONS[rel]
        if len(numbered_repr) == 0 or numbered_repr[-1] * curr_repr[0] < 0:
            numbered_repr += curr_repr
        else:
            numbered_repr[-1] += curr_repr[0]
            numbered_repr += curr_repr[1:]
    return numbered_repr

def common_name(chain: Path, do_compress: bool) -> str:
    if len(chain) == 0:
        return "self"
    else:
        return "'s ".join(rel for rel, name in (compress(chain) if do_compress else chain))

def generational_difference(chain: Path) -> int:
    return sum(numbered_representation(chain))

def distance(chain: Path) -> int:
    return len(chain)

# ----------------------------------------------------------

class Part(ABC):

    @abstractmethod
    def __init__(self, primitive_chain: list[str], final_name: str) -> None:
        ...
    
    @abstractmethod
    def fill_in_up_down_coordinates(self) -> None:
        ...

    @abstractmethod
    def fill_in_canonical_term(self) -> None:
        ...
    
    @abstractmethod
    def __repr__(self) -> str:
        ...

    @abstractmethod
    def convert_to_tuple(self) -> tuple[str, str]:
        ...

# ----------------------------------------------------------

class ConsanguineousPart(Part):

    @override
    def __init__(self, primitive_chain: list[str], final_name: str) -> None:
        self.primitive_chain: list[str] = primitive_chain.copy()
        self.final_name: str = final_name
        self.up_down_coordinates: tuple[int, int] | None = None
        self.canonical_term: str = ""
        self.is_half: bool = False

    @override
    def fill_in_up_down_coordinates(self) -> None:
        if "spouse" in self.primitive_chain:
            return
        up: int = 0
        down: int = 0
        for primitive in self.primitive_chain:
            if primitive == "parent":
                up += 1
            elif primitive == "child":
                down += 1
            elif primitive == "sibling":
                up += 1
                down += 1
        self.up_down_coordinates = (up, down)
        if up >= 1 and down >= 1 and "sibling" not in self.primitive_chain:
            self.is_half = True

    @override
    def fill_in_canonical_term(self) -> None:
        is_male: bool = PEOPLE[self.final_name].gender == "M"
        if self.up_down_coordinates is None:
            self.canonical_term = "husband" if is_male else "wife"
            return
        up: int = self.up_down_coordinates[0]
        down: int = self.up_down_coordinates[1]
        if up == 0:
            if down == 0:
                self.canonical_term = "self"
            elif down == 1:
                self.canonical_term = "son" if is_male else "daughter"
            elif down == 2:
                self.canonical_term = "grandson" if is_male else "granddaughter"
            elif down >= 3:
                self.canonical_term = \
                    (down - 2) * "great-" + ("grandson" if is_male else "granddaughter")
        elif down == 0:
            if up == 1:
                self.canonical_term = "father" if is_male else "mother"
            elif up == 2:
                self.canonical_term = "grandfather" if is_male else "grandmother"
            elif up >= 3:
                self.canonical_term = \
                    (up - 2) * "great-" + ("grandfather" if is_male else "grandmother")
        elif up == 1:
            if down == 1:
                self.canonical_term = "brother" if is_male else "sister"
            elif down == 2:
                self.canonical_term = "nephew" if is_male else "niece"
            elif down == 3:
                self.canonical_term = "grandnephew" if is_male else "grandniece"
            elif down >= 4:
                self.canonical_term = \
                    (down - 3) * "great-" + ("grandnephew" if is_male else "grandniece")
        elif down == 1:
            if up == 2:
                self.canonical_term = "uncle" if is_male else "aunt"
            elif up == 3:
                self.canonical_term = "great-uncle" if is_male else "great-aunt"
            elif up >= 4:
                self.canonical_term = \
                    (up - 3) * "great-" + ("granduncle" if is_male else "grandaunt")
        elif up == down:
            self.canonical_term = ordinal_number(up - 1) + " cousin"
        else:
            self.canonical_term = \
                f"{ordinal_number(min(up, down) - 1)} cousin " \
                f"{multiplicative_number(abs(up - down))} removed"
        if self.is_half:
            self.canonical_term = "half-" + self.canonical_term

    @override
    def __repr__(self) -> str:
        up_down: str = \
            f" {yellow(str(self.up_down_coordinates))}" if self.up_down_coordinates else ""
        return f"{red(self.canonical_term)}{up_down} ({green(self.final_name)})"
    
    @override
    def convert_to_tuple(self) -> tuple[str, str]:
        return (self.canonical_term, self.final_name)

# ----------------------------------------------------------

class AnyPart(Part):
    
    @override
    def __init__(self, primitive_chain: list[str], final_name: str) -> None:
        self.is_step: bool = False
        self.is_in_law: bool = False
        self.canonical_term: str = ""
        self.final_name: str = final_name
        if all(rel == "spouse" for rel in primitive_chain):
            self.consanguineous_part = ConsanguineousPart(primitive_chain, final_name)
            return
        for i, rel in enumerate(temp := [""] + primitive_chain + [""]):
            if rel == "spouse":
                if temp[i-1] == "parent" or temp[i+1] == "child":
                    self.is_step = True
                else:
                    self.is_in_law = True
        primitive_chain = \
            "|".join(primitive_chain).replace("parent|spouse|child", "sibling").split("|")
        no_spouses: list[str] = [rel for rel in primitive_chain if rel != "spouse"]
        self.consanguineous_part = ConsanguineousPart(no_spouses, final_name)

    @override
    def fill_in_up_down_coordinates(self) -> None:
        self.consanguineous_part.fill_in_up_down_coordinates()

    @override
    def fill_in_canonical_term(self) -> None:
        self.consanguineous_part.fill_in_canonical_term()
        self.canonical_term = \
            ("step-" if self.is_step else "") + \
            self.consanguineous_part.canonical_term + \
            ("-in-law" if self.is_in_law else "")

    @override
    def __repr__(self) -> str:
        return f"{red(self.canonical_term)} ({green(self.final_name)})"
    
    @override
    def convert_to_tuple(self) -> tuple[str, str]:
        return (self.canonical_term, self.final_name)

# ----------------------------------------------------------

def should_start_new(prev_rel: str, next_rel: str, part_type: type[Part]) -> bool:
    if prev_rel == "spouse" or next_rel == "spouse":
        return part_type is ConsanguineousPart
    if prev_rel == "parent" or next_rel == "child":
        return False
    else:
        return True
    
def get_prev_rel(curr_part: Path, part_type: type[Part]) -> str:
    if part_type is ConsanguineousPart:
        return curr_part[-1][0]
    else:
        for rel, name in reversed(curr_part):
            if rel != "spouse":
                return rel
        return "spouse"

def decompose(chain: Path, part_type: type[Part]) -> list[Path]:
    parts: list[Path] = []
    for rel, name in chain:
        if len(parts) == 0 or should_start_new(get_prev_rel(parts[-1], part_type), rel, part_type):
            parts.append([(rel, name)])
        else:
            parts[-1].append((rel, name))
    return parts

def transform(raw_parts: list[Path], part_type: type[Part]) -> list[Part]:
    parts: list[Part] = [part_type(
        [rel for rel, name in subchain], subchain[-1][1]
    ) for subchain in raw_parts]
    for part in parts:
        part.fill_in_up_down_coordinates()
        part.fill_in_canonical_term()
    return parts

def decompose_and_format(chain: Path, part_type: type[Part]) -> str:
    parts: list[Part] = transform(decompose(chain, part_type), part_type)
    return " -> ".join(str(part) for part in parts)

def decompose_and_naturalize(chain: Path, part_type: type[Part]) -> str:
    parts: list[Part] = transform(decompose(chain, part_type), part_type)
    parts_as_path: Path = [part.convert_to_tuple() for part in parts]
    return common_name(parts_as_path, do_compress = False)

# ----------------------------------------------------------

@cache
def relatedness(p1: Person, p2: Person) -> float:
    if p1 is p2: # base case 1
        return 1 if p1.is_founder else 1 + 0.5 * relatedness(p1.parents[0], p1.parents[1])
    elif p2.is_descendant_of(p1): # swap the arguments
        return relatedness(p2, p1)
    elif p1.is_founder: # base case 2
        return 0
    else: # recurse until same person or founder is reached
        return 1/2 * relatedness(p1.parents[0], p2) + 1/2 * relatedness(p1.parents[1], p2)

# ----------------------------------------------------------

def display_full_chain_info(chain: Path, p1: Person, p2: Person) -> None:
    print(remove_leading_whitespaces(
        f"""{blue('Ungendered chain with names:')} {ungendered_with_names(chain)}
        {blue('Ungendered chain without names:')} {ungendered_without_names(chain)}
        {blue('Gendered chain with names:')} {gendered_with_names(chain)}
        {blue('Gendered chain without names:')} {gendered_without_names(chain)}
        {blue('Numbered representation:')} {numbered_representation(chain)}
        {blue('Generational difference:')} {generational_difference(chain)}
        {blue('Distance:')} {distance(chain)}
        {blue('Relatedness:')} {(100 * relatedness(p1, p2)):.2f}
        {blue('Consanguineous decomposition:')} {decompose_and_format(chain, ConsanguineousPart)}
        {blue('Canonical decomposition:')} {decompose_and_format(chain, AnyPart)}
        {blue('Common name 1:')} {common_name(chain, do_compress = True)}
        {blue('Common name 2:')} {decompose_and_naturalize(chain, ConsanguineousPart)}
        {blue('Common name 3:')} {decompose_and_naturalize(chain, AnyPart)}"""
    ))

# ----------------------------------------------------------

def run_program() -> None:

    if len(argv) == 1:
        print("\nUSAGE: `python main.py <OPTION>`\n"
              "\nOPTIONS:"
              "\nd: display all people and their immediate relationships"
              "\ndf: display all people and their immediate relationships, including founders"
              "\nf: find the chain of relationships between two people")
        return

    parse_input_file()
    parse_common_names()
    option: str = argv[1]

    if option == "d":
        display_all(include_founders = False)
    elif option == "df":
        display_all(include_founders = True)
    elif option == "f":
        find_chain()
    else:
        raise ValueError("invalid option")

# ----------------------------------------------------------

if __name__ == "__main__":
    run_program()