#!/usr/bin/env python3

"""Plasma model

Simulates the height of the plasma, no doubt very unrealistically, but it'll provide
something to try to control. The "plasma" starts at height 0, then does a random walk
around that point, while it's pushed away from 0 exponentially by the magnetic field,
and pushed back by the steering coils. Or at least something that looks similar in terms
of the MUSCLE3 connections.

Ports:
    clock_out (O_I): Sends an empty message for synchronisation purposes.
    control_in (S): Receives control input.
    plasma_state_out (O_I): Sends the state of the plasma.

Settings:
    t_begin: Time at which the simulation starts.
    dt_max: Maximum time step size.
    dt_adj: Multiplication factor if the solver does not converge.
    t_end: Time at which the simulation stops.
"""

import logging
from math import exp
import random
from libmuscle import Instance, Message
import matplotlib.pyplot as plt
from ymmsl import Operator


def interpolate(data: list[list[float]], x: float) -> float:
    """Get a value by interpolation from the list of control points."""
    if not data:
        logging.warning(f"No control data for {x}!")
        return 0.0

    i = 0
    while i < len(data) and x < data[i][0]:
        i += 1

    if i < len(data) - 1:
        x1, y1 = data[i]
        x2, y2 = data[i + 1]
        t = (x - x1) / (x2 - x1)
        result = y1 + t * (y2 - y1)
        logging.info(f"Control input {result} at {x} from {data}")
        return result

    logging.warning(f"Control data {data} is too old for {x}!")
    return 0.0


def main() -> tuple[list[float], list[float]]:
    logger = logging.getLogger()
    logging.getLogger("matplotlib").setLevel(logging.WARNING)
    logging.getLogger("PIL").setLevel(logging.WARNING)

    instance = Instance(
        {Operator.O_I: ["plasma_state_out"], Operator.S: ["control_in"]}
    )

    while instance.reuse_instance():
        # F_INIT
        t_begin = instance.get_setting("t_begin", "float", default=0.0)
        dt_max = instance.get_setting("dt_max", "float", default=1e-4)
        dt_adj = instance.get_setting("dt_adj", "float", default=0.5)
        t_end = instance.get_setting("t_end", "float", default=1.0)

        assert t_begin < t_end

        plasma_position = 0.0
        t_cur = t_begin
        t_next = t_cur + dt_max if t_cur + dt_max < t_end else None

        plasma_timepoints = [t_cur]
        plasma_states = [plasma_position]

        while True:
            # O_I
            instance.send("plasma_state_out", Message(t_cur, t_next, plasma_position))

            # S
            control_msg = instance.receive(
                "control_in", default=Message(t_cur, t_next, None)
            )
            logger.debug(
                f"Received control data {control_msg.data} at {t_cur} {t_next}"
            )

            dt = dt_max
            while random.random() < 0.5:
                # did not converge
                dt = dt * dt_adj

            noise = random.normalvariate() * dt
            kick = 10.0 * plasma_position * (exp(dt) - 1)
            control = interpolate(control_msg.data, t_cur + dt) * dt

            plasma_position += noise + kick + control
            logger.info(f"plasma position at {t_cur}: {plasma_position}")

            if t_next is None:
                break

            t_cur += dt
            t_next = t_cur + dt_max if t_cur + dt_max < t_end else None

            plasma_timepoints.append(t_cur)
            plasma_states.append(plasma_position)

    return plasma_timepoints, plasma_states


if __name__ == "__main__":
    logging.basicConfig()
    logging.getLogger().setLevel(logging.INFO)

    timepoints, states = main()

    plt.figure()
    (plot,) = plt.plot(timepoints, states, "b-")
    plt.show()
