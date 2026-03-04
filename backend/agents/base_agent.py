from abc import ABC, abstractmethod
from models.agent_result import AgentResult


class Agent(ABC):

    name: str

    @abstractmethod
    async def run(self, input_data):
        pass