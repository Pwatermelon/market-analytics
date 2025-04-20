from abc import ABC, abstractmethod

class ParserBase(ABC):
    @abstractmethod
    def search(self, query: str):
        pass
