import random

class PVInverter:

    def __init__(self):

        self.rated_power = 375.0

        self.status = "Running"

        self.active_power = 0.0
        self.reactive_power = 0.0

        self.dc_voltage = 900.0
        self.dc_current = 0.0

        self.ac_voltage = 415.0
        self.ac_current = 0.0

        self.frequency = 50.0

        self.temperature = 35.0

        self.energy_today = 0.0

        self.alarm = 0

    def update(self):#, dt: float

        # irradiance = 0 to 1000 W/m²
        irradiance = 850

        self.active_power = self.rated_power * irradiance / 1000

        self.dc_current = self.active_power / self.dc_voltage

        self.ac_current = self.active_power * 1000 / (1.732 * 415)

        self.energy_today += self.active_power / 3600


        self.ac_voltage = 415 + random.uniform(-2, 2)

        self.frequency = 50 + random.uniform(-0.02, 0.02)

        self.temperature += random.uniform(-0.05, 0.05)

        self.publish()

    def publish(self):
        print("active_power:", self.active_power)
        print("dc_current:", self.dc_current)
        print("ac_current:", self.ac_current)
        print("ac_voltage:", self.ac_voltage)
        print("frequency:", self.frequency)
        print("temperature:", self.temperature)

    def start(self):
        self.status = "Running"

    def stop(self):
        self.status = "Stopped"
        self.active_power = 0

    def set_power_limit(self, percent):
        self.power_limit = percent

    def trip(self):

        self.status = "Fault"

        self.active_power = 0

        self.alarm = 101