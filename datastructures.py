from dataclasses import dataclass
from datetime import datetime


@dataclass
class Record:
    created_at: (str, datetime)
    id: int
    state: str
    action: str

    def __post_init__(self):
        self.created_at = datetime.strptime(self.created_at, "%Y-%m-%d")


@dataclass
class Culture(Record):
    mushroom: str
    medium: str

    def __str__(self):
        return f"{self.created_at.strftime('%Y%m%d')}C{str(self.id).rjust(3, '0')}"


@dataclass
class Bag(Record):
    mushroom: str
    starter: str
    total_yield: float

    def __str__(self):
        return f"{self.created_at.strftime('%Y%m%d')}B{str(self.id).rjust(3, '0')}"


@dataclass
class GrainSpawn(Record):
    container: int

    def __str__(self):
        return f"{self.created_at.strftime('%Y%m%d')}GS{str(self.id).rjust(3, '0')}"


@dataclass
class Recipe:
    name: str
    ingredients: str
    instructions: str
