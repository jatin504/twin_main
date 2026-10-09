from abc import ABC, abstractmethod


class DispatchStrategy(ABC):

    @abstractmethod
    def dispatch(
        self,
        plant_context,
        pcs_contexts,
    ):
        """
        Calculate and distribute commands.
        """
        pass