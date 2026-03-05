from abc import ABC, abstractmethod


class Agent(ABC):

    @property
    @abstractmethod
    def name(self) -> str: ...

    @abstractmethod
    async def run(self, input_data): ...