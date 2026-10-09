from __future__ import annotations


class RampLimiter:
    """
    Generic symmetric ramp limiter.

    Ramp rate is expressed in units per second.
    """

    def __init__(self, rate: float):

        if rate <= 0:
            raise ValueError("Ramp rate must be > 0")

        self.rate = rate

    def update(
        self,
        current: float,
        target: float,
        dt: float,
    ) -> float:

        if dt <= 0:
            return current

        maximum_change = self.rate * dt

        difference = target - current

        if difference > maximum_change:

            difference = maximum_change

        elif difference < -maximum_change:

            difference = -maximum_change

        return current + difference