from core.debug import DebugConsole
from models.base import BaseSimulationModel
from models.operating_mode import OperatingMode
from state.tags import Tags


class GridFollowingController(BaseSimulationModel):

    PLL_TIME = 3.0

    def __init__(self, context):

        super().__init__(context)

        self.timer = 0.0
        self.debug_timer = 0.0

        self.debug = DebugConsole(context.database)
        

    def update(self, dt):

        mode = self.db.value(
            Tags.PCS.OPERATING_MODE
        )

        available = self.db.value(
            Tags.Grid.AVAILABLE
        )

        self.debug_timer += dt

        if self.debug_timer >= 1.0:

            # self.debug.dump()

            self.debug_timer = 0.0

        if mode != OperatingMode.GRID_FOLLOWING:

            self.timer = 0.0

            self.db.set(
                Tags.Grid.PLL_LOCKED,
                False,
            )

            self.db.set(
                Tags.Grid.SYNCHRONIZED,
                False,
            )

            self.db.set(
                Tags.Grid.SYNC_PROGRESS,
                0.0,
            )

            return
        

        if not available:

            self.timer = 0.0

            self.db.set(
                Tags.Grid.PLL_LOCKED,
                False,
            )

            self.db.set(
                Tags.Grid.SYNCHRONIZED,
                False,
            )

            self.db.set(
                Tags.Grid.SYNC_PROGRESS,
                0.0,
            )

            return

        self.timer += dt

        progress = min(
            self.timer / self.PLL_TIME,
            1.0,
        )

        self.db.set(
            Tags.Grid.SYNC_PROGRESS,
            progress * 100,
        )

        if self.timer >= self.PLL_TIME:

            self.db.set(
                Tags.Grid.PLL_LOCKED,
                True,
            )

            self.db.set(
                Tags.Grid.SYNCHRONIZED,
                True,
            )