import random
from typing import Any, Dict, List, Sequence, TypeVar

T = TypeVar("T")

class SeededRandom:
    """Seeded pseudo-random number generator for deterministic replay."""

    def __init__(self, seed: int = 42):
        self.seed = seed
        self.rng = random.Random(seed)

    def random(self) -> float:
        return self.rng.random()

    def randint(self, a: int, b: int) -> int:
        return self.rng.randint(a, b)

    def uniform(self, a: float, b: float) -> float:
        return self.rng.uniform(a, b)

    def choice(self, seq: Sequence[T]) -> T:
        return self.rng.choice(seq)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "seed": self.seed,
            "state": list(self.rng.getstate()[1])
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SeededRandom":
        sr = cls(seed=data["seed"])
        if "state" in data:
            state_tuple = (3, tuple(data["state"]), None)
            sr.rng.setstate(state_tuple)
        return sr
