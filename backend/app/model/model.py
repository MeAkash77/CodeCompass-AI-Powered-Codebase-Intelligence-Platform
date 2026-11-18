from typing import Any
from abc import ABC, abstractmethod


class Model(ABC):
    @abstractmethod
    def __init__(self) -> None:
        pass

    @abstractmethod
    def __call__(self, *args: Any, **kwds: Any) -> Any:
        pass