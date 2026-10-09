from network.interface import NetworkInterface


class DummyBackend(NetworkInterface):

    def initialize(self):

        self.p = 0

        self.load = 0

    def set_generator(
        self,
        name,
        p,
        q,
    ):

        self.p = p

    def set_load(
        self,
        name,
        p,
        q,
    ):

        self.load = p

    def solve(self):

        pass

    def bus_voltage(
        self,
        name,
    ):

        return 690

    def bus_frequency(
        self,
        name,
    ):

        return 50