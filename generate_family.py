from genealogy import *
from enumerate import *
import helpers.random_util as ru
from collections import defaultdict

type EventType = Literal["marriage", "childbirth"]
type CandidatePairList = list[tuple[Person, Person]]

class NoCandidatesError(Exception): pass

class Event(NamedTuple):
    p1: Person
    p2: Person
    event: EventType
    p3: Person | None = None

class FamilyMetadata(NamedTuple):
    events: list[Event]
    used_components: set[str]
    person_to_gen: dict[Person, int]
    gen_to_people: dict[int, list[Person]]

def generate_founders(
    num_founders: int, already_used: set[str],
    person_to_gen: dict[Person, int], gen_to_people: dict[int, list[Person]]
) -> None:
    PEOPLE.clear()
    for i in tqdm(range(num_founders), "generating founders"):
        founder = Person(random_name(already_used, 1), "M" if randint(0, 1) == 1 else "F", True)
        person_to_gen[founder] = 0
        PEOPLE[founder.name] = founder
    gen_to_people[0] = list(PEOPLE.values())

def update_marriage_candidate_pairs(
    candidate_pairs: dict[int, CandidatePairList], event: Event,
    person_to_gen: dict[Person, int], gen_to_people: dict[int, list[Person]]
) -> None:
    if event.event == "marriage":
        candidate_pairs[person_to_gen[event.p1]][:] = [
            (p1, p2) for p1, p2 in candidate_pairs[person_to_gen[event.p1]]
            if p1 is not event.p1 and p2 is not event.p2
        ]
    elif event.event == "childbirth":
        assert event.p3 is not None
        for person in gen_to_people[person_to_gen[event.p3]]:
            if (
                person.gender != event.p3.gender and
                person.spouse is None and
                relatedness(person, event.p3) == 0
            ):
                candidate_pairs[person_to_gen[event.p3]].append(
                    (event.p3, person) if event.p3.gender == "M" else (person, event.p3)
                )

def update_childbirth_candidate_fathers(candidate_fathers: list[Person], event: Event) -> None:
    if event.event == "marriage":
        candidate_fathers.append(event.p1)

def num_candidate_pairs(candidate_pairs: dict[int, CandidatePairList]) -> int:
    return sum(len(pair_list) for pair_list in candidate_pairs.values())

def sample_from_candidate_pairs(
    candidate_pairs: dict[int, CandidatePairList]
) -> tuple[Person, Person]:
    total_len: int = num_candidate_pairs(candidate_pairs)
    random_index: int = randint(0, total_len - 1)
    for pair_list in candidate_pairs.values():
        if random_index >= len(pair_list):
            random_index -= len(pair_list)
        else:
            return pair_list[random_index]
    raise RuntimeError("code should never reach here")

def generate_marriage(candidate_pairs: dict[int, CandidatePairList]) -> Event:
    if num_candidate_pairs(candidate_pairs) == 0:
        raise NoCandidatesError
    husband, wife = sample_from_candidate_pairs(candidate_pairs)
    husband.spouse = wife
    wife.spouse = husband
    return Event(husband, wife, "marriage")

def connect_child_with_siblings(child: Person) -> None:
    for sibling in child.parents[0].children:
        if sibling is not child:
            child.add_relative("sibling", sibling.name)

def generate_childbirth(
    candidate_fathers: list[Person], person_to_gen: dict[Person, int],
    gen_to_people: dict[int, list[Person]], already_used: set[str]
) -> Event:
    if len(candidate_fathers) == 0:
        raise NoCandidatesError
    father: Person = ru.random_element(candidate_fathers)
    assert father.spouse is not None
    mother: Person = father.spouse
    child = Person(random_name(already_used, 1), "M" if randint(0, 1) == 1 else "F")
    PEOPLE[child.name] = child
    person_to_gen[child] = person_to_gen[father] + 1
    gen_to_people[person_to_gen[child]].append(child)
    child.add_relative("parent", father.name)
    child.add_relative("parent", mother.name)
    connect_child_with_siblings(child)
    return Event(father, mother, "childbirth", child)

def get_founder_candidate_pairs() -> dict[int, CandidatePairList]:
    candidate_pairs: dict[int, CandidatePairList] = defaultdict(list)
    for husband_candidate in [person for person in PEOPLE.values() if person.gender == "M"]:
        for wife_candidate in [person for person in PEOPLE.values() if person.gender == "F"]:
            candidate_pairs[0].append((husband_candidate, wife_candidate))
    return candidate_pairs

def generate_family(num_founders: int, num_additional: int) -> FamilyMetadata:
    relatedness.cache_clear()
    Person.is_descendant_of.cache_clear()
    already_used: set[str] = set()
    events: list[Event] = []
    person_to_gen: dict[Person, int] = {}
    Person.get_gen = lambda self: person_to_gen[self]
    gen_to_people: dict[int, list[Person]] = defaultdict(list)
    generate_founders(num_founders, already_used, person_to_gen, gen_to_people)
    candidate_pairs: dict[int, CandidatePairList] = get_founder_candidate_pairs()
    candidate_fathers: list[Person] = []
    num_added: int = 0
    with tqdm(total = num_additional, desc = "generating additional people") as progress_bar:
        while num_added < num_additional:
            try:
                if randint(0, 2) == 2:
                    events.append(generate_marriage(candidate_pairs))
                else:
                    events.append(generate_childbirth(
                        candidate_fathers, person_to_gen, gen_to_people, already_used
                    ))
                    num_added += 1
                    progress_bar.update()
                update_marriage_candidate_pairs(
                    candidate_pairs, events[-1], person_to_gen, gen_to_people
                )
                update_childbirth_candidate_fathers(candidate_fathers, events[-1])
            except NoCandidatesError:
                if num_candidate_pairs(candidate_pairs) == 0 and len(candidate_fathers) == 0:
                    raise NoCandidatesError
    return FamilyMetadata(events, already_used, person_to_gen, gen_to_people)

def get_first_name(full_name: str) -> str:
    return full_name.split(" ")[0]

def get_birth_surname(full_name: str) -> str:
    return full_name.split(" ")[1].split("/")[0]

def get_married_surname(full_name: str) -> str:
    return full_name.split(" ")[1].split("/")[1]

def clear_surnames() -> None:
    full_to_first_name: dict[str, str] = {}
    for person in PEOPLE.values():
        first_name: str = get_first_name(person.name)
        full_to_first_name[person.name] = first_name
        person.name = first_name
    for full_name, first_name in full_to_first_name.items():
        PEOPLE[first_name] = PEOPLE.pop(full_name)

def add_founder_surnames(scheme: type[Scheme], already_used: set[str]) -> None:
    first_to_full_name: dict[str, str] = {}
    for founder in [person for person in PEOPLE.values() if person.is_founder]:
        num_components: int = scheme.stable_num_components_at_birth(cast(Gender, founder.gender))
        surname: str = random_name(already_used, num_components)
        full_name: str = f"{founder.name} {surname}"
        first_to_full_name[founder.name] = full_name
        founder.name = full_name
    for first_name, full_name in first_to_full_name.items():
        PEOPLE[full_name] = PEOPLE.pop(first_name)

def handle_marriage_surnames(
    husband: Person, wife: Person, scheme: type[Scheme]
) -> None:
    husband_orig_name: str = husband.name
    wife_orig_name: str = wife.name
    husband_married_surname, wife_married_surname = \
        marry(get_birth_surname(husband.name), get_birth_surname(wife.name), scheme)
    husband.name += f"/{husband_married_surname}"
    wife.name += f"/{wife_married_surname}"
    PEOPLE[husband.name] = PEOPLE.pop(husband_orig_name)
    PEOPLE[wife.name] = PEOPLE.pop(wife_orig_name)

def handle_childbirth_surnames(
    father: Person, mother: Person, child: Person, scheme: type[Scheme]
) -> None:
    child_first_name: str = child.name
    child_birth_surname: str = scheme.get_child_name(
        get_married_surname(father.name),
        get_married_surname(mother.name),
        cast(Gender, child.gender)
    )
    child.name = f"{child_first_name} {child_birth_surname}"
    PEOPLE[child.name] = PEOPLE.pop(child_first_name)

def add_surnames(
    scheme: type[Scheme], events: list[Event], used_first_name_components: set[str]
) -> None:
    already_used: set[str] = used_first_name_components.copy()
    clear_surnames()
    add_founder_surnames(scheme, already_used)
    for event in events:
        if event.event == "marriage":
            husband: Person = event.p1
            wife: Person = event.p2
            handle_marriage_surnames(husband, wife, scheme)
        elif event.event == "childbirth":
            father: Person = event.p1
            mother: Person = event.p2
            assert event.p3 is not None
            child: Person = event.p3
            handle_childbirth_surnames(father, mother, child, scheme)

def find_all_family_members(person: Person) -> set[Person]:
    frontier: list[Person] = [person]
    visited: set[Person] = {person}
    while len(frontier) > 0:
        curr: Person = frontier.pop()
        for p in (
            [*curr.parents, *curr.siblings, *curr.children] +
            ([curr.spouse] if curr.spouse is not None else [])
        ):
            if p not in visited:
                visited.add(p)
                frontier.append(p)
    return visited

def find_all_distinct_families() -> list[set[Person]]:
    result: list[set[Person]] = []
    people: set[Person] = set(PEOPLE.values())
    while len(people) > 0:
        arbitrary_person: Person = people.pop()
        family: set[Person] = find_all_family_members(arbitrary_person)
        result.append(family)
        people.difference_update(family)
    return result

def clean_up_family_metadata(family_metadata: FamilyMetadata) -> FamilyMetadata:
    events: list[Event] = [
        event for event in family_metadata.events
        if event.p1.name in PEOPLE and event.p2.name in PEOPLE and
        (event.p3 is None or event.p3.name in PEOPLE)
    ]
    used_components: set[str] = {
        get_first_name(name) for name in PEOPLE
    }
    person_to_gen: dict[Person, int] = {
        person: gen for person, gen in family_metadata.person_to_gen.items()
        if person.name in PEOPLE
    }
    Person.get_gen = lambda self: person_to_gen[self]
    gen_to_people: dict[int, list[Person]] = {
        gen: [
            person for person in people
            if person.name in PEOPLE
        ] for gen, people in family_metadata.gen_to_people.items()
    }
    return FamilyMetadata(events, used_components, person_to_gen, gen_to_people)

def use_only_largest_family(family_metadata: FamilyMetadata) -> FamilyMetadata:
    distinct_families: list[set[Person]] = find_all_distinct_families()
    largest_family: set[Person] = max(distinct_families, key = lambda family: len(family))
    for name, person in PEOPLE.copy().items():
        if person not in largest_family:
            del PEOPLE[name]
    return clean_up_family_metadata(family_metadata)