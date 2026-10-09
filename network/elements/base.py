from abc import ABC, abstractmethod

class ElectricalElement(ABC):

    @abstractmethod
    def update(self, backend):

        raise NotImplementedError