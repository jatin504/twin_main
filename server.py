class PositiveValue:
    def __set_name__(self, owner, name):
        self.name = name

    def __get__(self, instance, owner):
        if instance is None:
            return self
        return instance.__dict__.get(self.name)

    def __set__(self, instance, value):
        if value <= 0:
            raise ValueError(f"{self.name} must be positive")
        instance.__dict__[self.name] = value


class Battery:
    voltage = PositiveValue()
    power = PositiveValue()

    def __init__(self, voltage, power):
        self.voltage = voltage
        self.power = power


b = Battery(690, 2500)

print(b.voltage)
print(b.power)

b.voltage = 720
print(b.voltage)

b.power = -100


# import asyncio


# async def worker(name, delay):
#     print(f"{name}: start")
#     await asyncio.sleep(delay)
#     print(f"{name}: end")
#     return name


# async def main():
#     tasks = [
#         worker("A", 3),
#         worker("B", 1),
#         worker("C", 2),
#     ]

#     results = await asyncio.gather(*tasks)

#     print(results)


# asyncio.run(main())