"""Bitwise-reproducible and stochastic pseudo-random number generators."""
import random
import os
import time
from enum import Enum
from typing import Any, Dict, List, Optional, Sequence, TypeVar

T = TypeVar("T")

class RandomnessMode(Enum):
    DETERMINISTIC = "DETERMINISTIC"
    STOCHASTIC = "STOCHASTIC"

class SeededRandom:
    """Seeded, isolated pseudo-random number generator."""

    def __init__(self, seed: Optional[int] = 42, mode: RandomnessMode = RandomnessMode.DETERMINISTIC, stream_name: str = "default"):
        self.stream_name = stream_name
        self.mode = mode
        if mode == RandomnessMode.STOCHASTIC or seed is None:
            entropy_int = int.from_bytes(os.urandom(4), "big") ^ int(time.time_ns() & 0xFFFFFFFF)
            self.seed = entropy_int
            self.mode = RandomnessMode.STOCHASTIC
        else:
            self.seed = int(seed)
            self.mode = RandomnessMode.DETERMINISTIC
        self._rng = random.Random(self.seed)

    @classmethod
    def create_stochastic(cls, stream_name: str = "default") -> "SeededRandom":
        return cls(seed=None, mode=RandomnessMode.STOCHASTIC, stream_name=stream_name)

    def random(self) -> float:
        return self._rng.random()

    def uniform(self, a: float, b: float) -> float:
        return self._rng.uniform(a, b)

    def randint(self, a: int, b: int) -> int:
        return self._rng.randint(a, b)

    def choice(self, seq: Sequence[T]) -> T:
        if not seq:
            raise IndexError("Cannot choose from an empty sequence.")
        return self._rng.choice(seq)

    def sample(self, population: Sequence[T], k: int) -> List[T]:
        return self._rng.sample(population, k)

    def shuffle(self, x: list) -> None:
        self._rng.shuffle(x)

    def gauss(self, mu: float, sigma: float) -> float:
        return self._rng.gauss(mu, sigma)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "stream_name": self.stream_name,
            "seed": self.seed,
            "mode": self.mode.value,
            "state": self._rng.getstate()
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SeededRandom":
        mode_str = data.get("mode", "DETERMINISTIC")
        mode = RandomnessMode(mode_str)
        obj = cls(seed=data.get("seed", 42), mode=mode, stream_name=data.get("stream_name", "default"))
        if "state" in data:
            raw_state = data["state"]
            if isinstance(raw_state, list):
                raw_state = (raw_state[0], tuple(raw_state[1]), raw_state[2])
            obj._rng.setstate(raw_state)
        return obj
