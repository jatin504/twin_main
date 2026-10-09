from abc import ABC, abstractmethod


class NetworkInterface(ABC):

    @abstractmethod
    def initialize(self, topology):
        ...

    @abstractmethod
    def solve(self):
        ...

    @abstractmethod
    def set_load(self, name, p_kw, q_kvar):
        ...

    @abstractmethod
    def set_generator(self, name, p_kw, q_kvar):
        ...

    @abstractmethod
    def set_voltage_source(
        self,
        name,
        voltage,
        frequency,
        angle,
    ):
        ...

    @abstractmethod
    def voltage(self, bus):
        ...

    @abstractmethod
    def current(self, branch):
        ...