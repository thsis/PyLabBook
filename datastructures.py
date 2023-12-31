from dataclasses import dataclass
from datetime import datetime
from copy import copy

@dataclass
class Experiment:
    created_at: (str, datetime)
    id: (int, None)

    def __post_init__(self):
        try:
            self.created_at = datetime.strptime(self.created_at, "%Y-%m-%d") if self.created_at else None
        except ValueError:
            self.created_at = datetime.strptime(self.created_at, "%Y-%m-%d %H:%M:%S")
        self.name = str(self)


@dataclass
class Culture(Experiment):
    mushroom: str
    variant: str
    medium: (str, None)

    def __post_init__(self):
        super().__post_init__()
        for att in "mushroom", "variant", "medium":
            if not getattr(self, att):
                setattr(self, att, None)

    def __str__(self):
        return f"{self.created_at.strftime('%Y%m%d')}C{str(self.id).rjust(3, '0')}"


@dataclass
class Bag(Experiment):
    grain_spawn_id: int
    recipe_id: int
    mushroom: str = None
    variant: str = None

    def __post_init__(self):
        super().__post_init__()

    def __str__(self):
        return f"{self.created_at.strftime('%Y%m%d')}B{str(self.id).rjust(3, '0')}"


@dataclass
class GrainSpawn(Experiment):
    culture_id: int
    recipe_id: int
    mushroom: str = None
    variant: str = None

    def __post_init__(self):
        super().__post_init__()

    def __str__(self):
        return f"{self.created_at.strftime('%Y%m%d')}GS{str(self.id).rjust(3, '0')}"


@dataclass
class Recipe:
    id: (int, None)
    name: str
    recipe_type: str
    ingredients: str
    instructions: str

    def __post_init__(self):
        for k, v in self.__dict__.items():
            if k == "id":
                continue
            self.__dict__[k] = v.strip()
            assert v not in [""], f"{v} cannot be empty"


@dataclass
class Observation:
    experiment: (Experiment, Culture, GrainSpawn, Bag)
    observed_at: (str, datetime)
    passed: bool
    action: (str, None)

    def __post_init__(self):
        self.action = None if self.action == "" else self.action
        self.observed_at = datetime.strptime(self.observed_at, "%Y-%m-%d") if self.observed_at else None


@dataclass
class CultureObservation(Observation):

    def __post_init__(self):
        super().__post_init__()
        assert self.action in [None, "Created", "Destroyed"]


@dataclass
class GrainSpawnObservation(Observation):

    def __post_init__(self):
        super().__post_init__()
        assert self.action in [None, "Created", "Destroyed", "Used"]


@dataclass
class BagObservation(Observation):
    harvested: float = None

    def __post_init__(self):
        super().__post_init__()
        assert self.action in [None, "Created", "Destroyed", "Harvested", "Induced Pinning"]