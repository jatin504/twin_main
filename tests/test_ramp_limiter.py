from models.controllers.ramp_limiter import RampLimiter


def test_ramp():

    limiter = RampLimiter(rate=500)

    output = 0

    for i in range(10):

        output = limiter.update(
            current=output,
            target=1000,
            dt=0.1,
        )

        print(output)